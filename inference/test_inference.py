#!/usr/bin/env python3
"""
test_inference.py
Unit and Integration Tests for Edge TPU Inference Service.
"""

import os
import sys

# Set test environment overrides BEFORE importing app modules
os.environ["MODEL_PATH"] = os.path.abspath("artifacts/anomaly_autoencoder_edgetpu.tflite")
os.environ["CPU_FALLBACK_MODEL_PATH"] = os.path.abspath("artifacts/anomaly_autoencoder_int8.tflite")
os.environ["METADATA_PATH"] = os.path.abspath("artifacts/model_metadata.json")

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

import unittest
import numpy as np

from inference.app.config import settings
from inference.app.engine import EdgeTPUInferenceEngine
from inference.app.schemas import FEATURE_NAMES, TelemetryVectorRequest


class TestEdgeTPUInference(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.engine = EdgeTPUInferenceEngine()
        self.engine.initialize()

    def test_initialization(self):
        """Verify interpreter is loaded and quantization scale is valid."""
        self.assertIsNotNone(self.engine.interpreter)
        self.assertIsNotNone(self.engine.input_details)
        self.assertIsNotNone(self.engine.output_details)
        self.assertEqual(self.engine.input_details["shape"][1], 32)
        self.assertGreater(self.engine.input_scale, 0.0)
        self.assertGreater(self.engine.threshold, 0.0)

    def test_warmup_inference(self):
        """Verify warm-up latency is recorded and returns valid float."""
        latency_ms = self.engine.test_inference()
        self.assertGreater(latency_ms, 0.0)

    async def test_normal_vector_prediction(self):
        """Normal telemetry should result in MSE below threshold (is_anomaly=False)."""
        normal_vec = [0.1] * 32
        res = await self.engine.evaluate_vector(normal_vec)
        self.assertFalse(res.is_anomaly)
        self.assertLess(res.mse, self.engine.threshold)
        self.assertIsNotNone(res.top_root_cause)

    async def test_anomaly_vector_prediction(self):
        """Attack vector should result in MSE > threshold (is_anomaly=True)."""
        # Simulate SYN flood attack vector
        attack_vec = [0.1] * 32
        attack_vec[1] = 0.95  # flow_packets_rate
        attack_vec[4] = 0.98  # flow_syn_rate
        attack_vec[7] = 0.90  # flow_syn_fin_ratio
        attack_vec[22] = 0.85 # firewall_syn_drop_rate

        res = await self.engine.evaluate_vector(attack_vec)
        self.assertTrue(res.is_anomaly)
        self.assertGreater(res.mse, self.engine.threshold)
        # Check that one of the attacked features is identified in top residuals
        top_indices = [r.feature_index for r in res.top_residuals]
        self.assertTrue(any(idx in [1, 4, 7, 22] for idx in top_indices))

    async def test_dimension_validation(self):
        """Vector with wrong dimension should raise ValueError."""
        with self.assertRaises(ValueError):
            await self.engine.evaluate_vector([0.1] * 16)


if __name__ == "__main__":
    unittest.main()
