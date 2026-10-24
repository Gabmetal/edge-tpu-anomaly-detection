"""
metrics.py
Prometheus metrics registry and collectors for Edge TPU Anomaly Inference.
"""

from prometheus_client import Counter, Gauge, Histogram

# Sub-millisecond latency histogram buckets tailored for Edge TPU performance (<2ms SLA)
LATENCY_BUCKETS = (
    0.0001,  # 0.1 ms
    0.00025, # 0.25 ms
    0.0005,  # 0.5 ms
    0.00075, # 0.75 ms
    0.001,   # 1.0 ms
    0.0015,  # 1.5 ms
    0.002,   # 2.0 ms (SLA threshold)
    0.003,   # 3.0 ms
    0.005,   # 5.0 ms
    0.010,   # 10.0 ms
    0.025,   # 25.0 ms
)

INFERENCE_LATENCY_HISTOGRAM = Histogram(
    "edge_tpu_inference_latency_seconds",
    "Inference latency on the Google Coral Edge TPU or CPU fallback in seconds",
    buckets=LATENCY_BUCKETS,
)

RECONSTRUCTION_ERROR_GAUGE = Gauge(
    "anomaly_reconstruction_error_mse",
    "Latest computed autoencoder Mean Squared Error (MSE) reconstruction loss",
)

FEATURE_RESIDUAL_GAUGE = Gauge(
    "anomaly_feature_residual",
    "Individual feature squared residual (x_i - x_hat_i)^2 indicating root-cause anomaly contribution",
    ["feature_index", "feature_name"],
)

DEVICE_STATUS_GAUGE = Gauge(
    "edge_tpu_device_status",
    "Status of physical Edge TPU accelerator hardware (1 = Connected/Healthy, 0 = Fallback/Disconnected)",
)

INFERENCE_REQUESTS_COUNTER = Counter(
    "anomaly_inferences_total",
    "Total number of telemetry window inferences performed",
    ["status"],  # normal, anomaly, error
)

RECONNECT_ATTEMPTS_COUNTER = Counter(
    "edge_tpu_reconnect_attempts_total",
    "Total number of Edge TPU device reconnect/re-initialization attempts",
    ["result"],  # success, failure
)
