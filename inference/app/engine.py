"""
engine.py
Resilient Edge TPU Inference Engine for Real-Time Anomaly Detection.

Features:
  - Dynamically loads libedgetpu delegate on Google Coral USB/PCIe hardware
  - Automated fallback to CPU INT8 interpreter if Edge TPU is absent or offline
  - Concurrency safety mutex protecting non-reentrant libedgetpu runtime
  - Resilient USB disconnect & re-enumeration recovery with exponential backoff
  - Sub-millisecond INT8 quantization, forward pass, and dequantization
  - Per-feature residual calculation for anomaly root-cause attribution
  - Direct integration with Prometheus metrics
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, List, Optional, Tuple
import numpy as np

from app.config import settings
from app.metrics import (
    DEVICE_STATUS_GAUGE,
    FEATURE_RESIDUAL_GAUGE,
    INFERENCE_LATENCY_HISTOGRAM,
    INFERENCE_REQUESTS_COUNTER,
    RECONNECT_ATTEMPTS_COUNTER,
    RECONSTRUCTION_ERROR_GAUGE,
)
from app.schemas import FEATURE_NAMES, FeatureResidual, PredictionResponse

logger = logging.getLogger("inference.engine")


class EdgeTPUInferenceEngine:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.interpreter = None
        self.delegate = None
        self.is_edgetpu = False
        self.active_model_path = ""
        self.input_details = None
        self.output_details = None
        self.input_scale = 1.0
        self.input_zero_point = 0
        self.output_scale = 1.0
        self.output_zero_point = 0
        self.threshold = settings.anomaly_threshold
        self.total_inferences = 0
        self.last_reconnect_time = 0.0

        # Load threshold override from metadata if available
        self._load_metadata()

    def _load_metadata(self):
        """Loads anomaly threshold and baseline calibration from metadata file."""
        if os.path.exists(settings.metadata_path):
            try:
                with open(settings.metadata_path, "r") as f:
                    meta = json.load(f)
                    if "threshold" in meta:
                        self.threshold = float(meta["threshold"])
                        logger.info(f"Loaded decision threshold from metadata: {self.threshold:.6f}")
            except Exception as e:
                logger.warning(f"Could not parse metadata file {settings.metadata_path}: {e}")

    def _load_tflite_modules(self):
        """Attempts importing tflite_runtime first, then falls back to tensorflow.lite."""
        try:
            import tflite_runtime.interpreter as tflite
            return tflite.Interpreter, tflite.load_delegate
        except ImportError:
            try:
                import tensorflow.lite as tflite
                return tflite.Interpreter, tflite.experimental.load_delegate
            except ImportError:
                raise RuntimeError(
                    "Neither 'tflite_runtime' nor 'tensorflow.lite' is available in Python environment."
                )

    def initialize(self):
        """Initializes the TFLite Interpreter, attempting Edge TPU first with graceful CPU fallback."""
        InterpreterCls, load_delegate_fn = self._load_tflite_modules()

        # Step 1: Attempt loading on Google Coral Edge TPU
        if os.path.exists(settings.model_path):
            try:
                logger.info(f"Attempting to initialize Edge TPU delegate with model: {settings.model_path}")
                delegate_options = {}
                if settings.edgetpu_device:
                    delegate_options["device"] = settings.edgetpu_device

                self.delegate = load_delegate_fn(
                    settings.edgetpu_delegate_path,
                    delegate_options if delegate_options else None,
                )
                self.interpreter = InterpreterCls(
                    model_path=settings.model_path,
                    experimental_delegates=[self.delegate],
                )
                self.interpreter.allocate_tensors()
                self.is_edgetpu = True
                self.active_model_path = settings.model_path
                DEVICE_STATUS_GAUGE.set(1)
                logger.info("Successfully initialized Google Coral Edge TPU delegate.")
            except Exception as e:
                logger.warning(
                    f"Failed to initialize Edge TPU delegate: {e}. Switching to CPU fallback mode."
                )
                self.is_edgetpu = False
                self.delegate = None
                DEVICE_STATUS_GAUGE.set(0)
        else:
            logger.warning(
                f"Edge TPU model not found at {settings.model_path}. Trying fallback model."
            )

        # Step 2: Fallback to CPU INT8 interpreter if Edge TPU failed or model missing
        if not self.is_edgetpu:
            fallback_path = (
                settings.cpu_fallback_model_path
                if os.path.exists(settings.cpu_fallback_model_path)
                else settings.model_path
            )
            if not os.path.exists(fallback_path):
                raise FileNotFoundError(
                    f"No model found at {settings.model_path} or {settings.cpu_fallback_model_path}"
                )

            logger.info(f"Loading fallback model on CPU: {fallback_path}")
            self.interpreter = InterpreterCls(model_path=fallback_path)
            self.interpreter.allocate_tensors()
            self.active_model_path = fallback_path
            DEVICE_STATUS_GAUGE.set(0)

        # Step 3: Extract and cache tensor quantization parameters
        self.input_details = self.interpreter.get_input_details()[0]
        self.output_details = self.interpreter.get_output_details()[0]

        in_scale, in_zero = self.input_details["quantization"]
        out_scale, out_zero = self.output_details["quantization"]

        # Default scale to 1.0 if not quantized
        self.input_scale = in_scale if in_scale > 0 else 1.0
        self.input_zero_point = in_zero
        self.output_scale = out_scale if out_scale > 0 else 1.0
        self.output_zero_point = out_zero

        logger.info(
            f"Model Ready: input_shape={self.input_details['shape']}, "
            f"input_quant=(scale={self.input_scale}, zero={self.input_zero_point}), "
            f"output_quant=(scale={self.output_scale}, zero={self.output_zero_point}), "
            f"device={'Edge TPU' if self.is_edgetpu else 'CPU Fallback'}"
        )

        # Step 4: Run warm-up self-test inference
        self.test_inference()

    def test_inference(self) -> float:
        """Executes a warm-up inference to verify hardware pipeline readiness and latency."""
        dummy_vector = [0.1] * settings.input_dimension
        t0 = time.perf_counter()
        # Direct synchronous invoke for warm-up
        reconstructed = self._predict_raw(dummy_vector)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        mse = float(np.mean(np.square(np.array(dummy_vector) - reconstructed)))
        logger.info(f"Self-test inference passed. Latency: {latency_ms:.3f} ms, MSE: {mse:.6f}")
        return latency_ms

    async def reconnect_tpu(self) -> bool:
        """Attempts reconnecting to the Edge TPU after a USB re-enumeration or bus glitch."""
        now = time.time()
        if now - self.last_reconnect_time < settings.reconnect_base_delay_sec:
            return False  # Prevent re-entrant reconnection storms

        self.last_reconnect_time = now
        logger.warning("Initiating Edge TPU reconnection routine...")

        for attempt in range(1, settings.max_reconnect_retries + 1):
            delay = settings.reconnect_base_delay_sec * (1.5 ** (attempt - 1))
            logger.info(f"Reconnect attempt {attempt}/{settings.max_reconnect_retries} (waiting {delay:.2f}s)...")
            await asyncio.sleep(delay)

            try:
                self.initialize()
                if self.is_edgetpu:
                    logger.info("Edge TPU reconnected successfully!")
                    RECONNECT_ATTEMPTS_COUNTER.labels(result="success").inc()
                    return True
            except Exception as e:
                logger.error(f"Reconnect attempt {attempt} failed: {e}")
                RECONNECT_ATTEMPTS_COUNTER.labels(result="failure").inc()

        logger.critical("Failed to reconnect Edge TPU after maximum retries. Remaining on CPU fallback.")
        return False

    def _predict_raw(self, features: List[float]) -> np.ndarray:
        """Low-level execution: INT8 quantization, forward pass, and dequantization."""
        vector = np.array(features, dtype=np.float32)

        # Quantize float32 -> int8: q = round(x / scale) + zero_point
        if self.input_details["dtype"] == np.int8:
            q_in = np.round(vector / self.input_scale + self.input_zero_point)
            q_in = np.clip(q_in, -128, 127).astype(np.int8)
            tensor_in = np.expand_dims(q_in, axis=0)
        elif self.input_details["dtype"] == np.uint8:
            q_in = np.round(vector / self.input_scale + self.input_zero_point)
            q_in = np.clip(q_in, 0, 255).astype(np.uint8)
            tensor_in = np.expand_dims(q_in, axis=0)
        else:
            tensor_in = np.expand_dims(vector, axis=0)

        self.interpreter.set_tensor(self.input_details["index"], tensor_in)
        self.interpreter.invoke()

        # Dequantize output: x_hat = (q - zero_point) * scale
        q_out = self.interpreter.get_tensor(self.output_details["index"])[0]

        if self.output_details["dtype"] in (np.int8, np.uint8):
            reconstructed = (q_out.astype(np.float32) - self.output_zero_point) * self.output_scale
        else:
            reconstructed = q_out.astype(np.float32)

        return reconstructed

    async def evaluate_vector(
        self,
        features: List[float],
        timestamp: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> PredictionResponse:
        """Evaluates a 32-dim normalized telemetry vector on the Edge TPU.
        Returns MSE reconstruction error, anomaly flag, and root-cause residual attribution.
        """
        if len(features) != settings.input_dimension:
            raise ValueError(
                f"Feature vector dimension is {len(features)}, expected {settings.input_dimension}"
            )

        # Edge TPU delegate is NOT thread-safe; serialize invoke calls via asyncio lock
        async with self.lock:
            t_start = time.perf_counter()
            try:
                reconstructed = self._predict_raw(features)
            except (RuntimeError, Exception) as exc:
                logger.error(f"Inference error on device: {exc}")
                INFERENCE_REQUESTS_COUNTER.labels(status="error").inc()

                # Trigger asynchronous TPU reconnection if running on TPU
                if self.is_edgetpu:
                    DEVICE_STATUS_GAUGE.set(0)
                    asyncio.create_task(self.reconnect_tpu())

                # Attempt emergency CPU forward pass
                reconstructed = self._predict_raw(features)

            latency_sec = time.perf_counter() - t_start
            latency_ms = latency_sec * 1000.0

        # Calculate Mean Squared Error (MSE)
        vec_np = np.array(features, dtype=np.float32)
        diff_sq = np.square(vec_np - reconstructed)
        mse = float(np.mean(diff_sq))

        # Check anomaly condition
        is_anomaly = bool(mse > self.threshold)
        self.total_inferences += 1

        # Record Prometheus Observability Metrics
        INFERENCE_LATENCY_HISTOGRAM.observe(latency_sec)
        RECONSTRUCTION_ERROR_GAUGE.set(mse)
        INFERENCE_REQUESTS_COUNTER.labels(status="anomaly" if is_anomaly else "normal").inc()

        # Build feature residuals for attribution
        residuals = []
        for idx in range(len(features)):
            feat_name = FEATURE_NAMES[idx] if idx < len(FEATURE_NAMES) else f"feature_{idx}"
            res_val = float(diff_sq[idx])
            residuals.append(
                FeatureResidual(
                    feature_index=idx,
                    feature_name=feat_name,
                    residual_mse=round(res_val, 6),
                    input_value=round(float(features[idx]), 5),
                    reconstructed_value=round(float(reconstructed[idx]), 5),
                )
            )

        # Sort residuals descending to determine primary root causes
        residuals.sort(key=lambda x: x.residual_mse, reverse=True)
        top_root_cause = residuals[0] if residuals else None

        # Update top residual metric for monitoring
        if top_root_cause:
            FEATURE_RESIDUAL_GAUGE.labels(
                feature_index=str(top_root_cause.feature_index),
                feature_name=top_root_cause.feature_name,
            ).set(top_root_cause.residual_mse)

        return PredictionResponse(
            timestamp=timestamp,
            is_anomaly=is_anomaly,
            mse=round(mse, 6),
            threshold=round(self.threshold, 6),
            inference_latency_ms=round(latency_ms, 3),
            device="edgetpu" if self.is_edgetpu else "cpu_fallback",
            top_root_cause=top_root_cause,
            top_residuals=residuals[:5],  # Return top 5 contributing features
            metadata=metadata,
        )


# Global Engine Instance
engine = EdgeTPUInferenceEngine()
