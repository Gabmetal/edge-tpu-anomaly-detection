"""
main.py
FastAPI Application Entrypoint for Edge TPU Anomaly Detection Microservice.
"""

from collections import deque
from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, List, Optional, Union
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.responses import HTMLResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.config import settings
from app.dashboard import get_dashboard_html
from app.engine import engine
from app.schemas import (
    BatchPredictionResponse,
    BatchTelemetryRequest,
    PredictionResponse,
    StatusResponse,
    TelemetryVectorRequest,
)

# In-memory circular buffer for recent telemetry events & anomalies
EVENT_LOG: deque = deque(maxlen=100)

def record_event(res: PredictionResponse, metadata: Optional[Dict] = None):
    meta = metadata or res.metadata or {}
    scenario = meta.get("scenario", "telemetry_stream")
    source_ip = meta.get("src_ip", "192.168.0.x / Cluster Ingress")
    
    evt = {
        "id": f"evt-{int(time.time() * 1000)}",
        "timestamp": res.timestamp or time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "is_anomaly": res.is_anomaly,
        "mse": res.mse,
        "threshold": res.threshold,
        "latency_ms": res.inference_latency_ms,
        "root_cause": res.top_root_cause.feature_name if res.top_root_cause else "nominal",
        "root_cause_residual": res.top_root_cause.residual_mse if res.top_root_cause else 0.0,
        "scenario": scenario,
        "source_ip": source_ip,
        "status": "QUARANTINED" if res.is_anomaly else "NOMINAL",
        "mitigation": "OpenWrt fw4 Quarantine" if res.is_anomaly else "Normal Passthrough",
    }
    EVENT_LOG.appendleft(evt)

# Logging configuration
logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("inference.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize TPU / Fallback Interpreter
    logger.info("Initializing Edge TPU Inference Engine...")
    try:
        engine.initialize()
    except Exception as e:
        logger.error(f"Fatal error during engine initialization: {e}")
        # Note: Do not crash if running in container without TPU immediately attached;
        # let readyz fail so Kubernetes handles the state accurately.

    yield

    # Shutdown
    logger.info("Shutting down Edge TPU Inference Microservice.")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Sub-millisecond INT8 Autoencoder Anomaly Detection on Google Coral Edge TPU",
    lifespan=lifespan,
)


@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
@app.get("/ui", response_class=HTMLResponse, tags=["Dashboard"])
async def dashboard():
    """Cyber SOC Interactive Dashboard for Edge TPU Anomaly Detection."""
    return HTMLResponse(content=get_dashboard_html(), status_code=status.HTTP_200_OK)


@app.get("/healthz", status_code=status.HTTP_200_OK, tags=["Probes"])
async def healthz():
    """Kubernetes Liveness Probe: Confirms HTTP server process is running."""
    return {"status": "alive"}


@app.get("/readyz", tags=["Probes"])
async def readyz():
    """Kubernetes Readiness Probe: Verifies interpreter allocation and executes test inference."""
    if engine.interpreter is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Inference engine interpreter not initialized.",
        )
    try:
        test_latency_ms = engine.test_inference()
        return {
            "status": "ready",
            "device": "edgetpu" if engine.is_edgetpu else "cpu_fallback",
            "test_latency_ms": round(test_latency_ms, 3),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Readiness check failed during test inference: {e}",
        )


@app.get("/metrics", tags=["Observability"])
async def metrics():
    """Prometheus Scrape Endpoint: Exposes inference latency histograms, MSE gauges, and residuals."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/v1/status", response_model=StatusResponse, tags=["Diagnostics"])
async def get_status():
    """Returns detailed hardware and runtime status of the Edge TPU accelerator and active model."""
    if engine.interpreter is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Inference engine is not initialized",
        )

    return StatusResponse(
        status="operational",
        edge_tpu_connected=engine.is_edgetpu,
        device_type="Edge TPU (libedgetpu)" if engine.is_edgetpu else "CPU Fallback",
        model_loaded=engine.active_model_path,
        input_tensor={
            "name": str(engine.input_details["name"]),
            "shape": [int(x) for x in engine.input_details["shape"]],
            "dtype": str(engine.input_details["dtype"]),
            "scale": float(engine.input_scale),
            "zero_point": int(engine.input_zero_point),
        },
        output_tensor={
            "name": str(engine.output_details["name"]),
            "shape": [int(x) for x in engine.output_details["shape"]],
            "dtype": str(engine.output_details["dtype"]),
            "scale": float(engine.output_scale),
            "zero_point": int(engine.output_zero_point),
        },
        anomaly_threshold=float(engine.threshold),
        total_inferences=int(engine.total_inferences),
    )


@app.get("/v1/events", tags=["Diagnostics"])
async def get_events(limit: int = 50):
    """Returns the most recent flagged anomaly events and telemetry audit records."""
    return list(EVENT_LOG)[:limit]


@app.post("/v1/predict", response_model=Union[PredictionResponse, List[PredictionResponse]], tags=["Inference"])
async def predict_single(req: Union[TelemetryVectorRequest, List[TelemetryVectorRequest]]):
    """Evaluates a single or batched 10-second window 32-dim normalized telemetry vector on Edge TPU."""
    if isinstance(req, list):
        if not req:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Empty vector batch")
        results = []
        for item in req:
            res = await engine.evaluate_vector(
                features=item.features,
                timestamp=item.timestamp,
                metadata=item.metadata,
            )
            record_event(res, item.metadata)
            results.append(res)
        return results if len(results) > 1 else results[0]
    else:
        try:
            result = await engine.evaluate_vector(
                features=req.features,
                timestamp=req.timestamp,
                metadata=req.metadata,
            )
            record_event(result, req.metadata)
            return result
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
        except Exception as e:
            logger.error(f"Prediction failed: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/v1/predict/batch", response_model=BatchPredictionResponse, tags=["Inference"])
async def predict_batch(batch_req: BatchTelemetryRequest):
    """Evaluates a batch of sliding window telemetry vectors."""
    results = []
    anomalies = 0
    t0 = time.perf_counter()

    for item in batch_req.vectors:
        res = await engine.evaluate_vector(
            features=item.features,
            timestamp=item.timestamp,
            metadata=item.metadata,
        )
        if res.is_anomaly:
            anomalies += 1
        record_event(res, item.metadata)
        results.append(res)

    total_time_ms = (time.perf_counter() - t0) * 1000.0
    avg_latency = total_time_ms / len(results) if results else 0.0

    return BatchPredictionResponse(
        results=results,
        total_evaluated=len(results),
        anomalies_detected=anomalies,
        average_latency_ms=round(avg_latency, 3),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
