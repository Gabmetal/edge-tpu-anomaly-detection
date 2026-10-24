"""
schemas.py
Pydantic Request and Response Schemas for Edge TPU Inference Service.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

FEATURE_NAMES = [
    "flow_bytes_rate",
    "flow_packets_rate",
    "flow_avg_packet_size",
    "flow_avg_duration_sec",
    "flow_syn_rate",
    "flow_fin_rate",
    "flow_rst_rate",
    "flow_syn_fin_ratio",
    "flow_rst_ratio",
    "flow_tcp_ratio",
    "flow_udp_ratio",
    "flow_icmp_ratio",
    "flow_unique_src_ips",
    "flow_unique_dst_ips",
    "flow_unique_dst_ports",
    "flow_fanout_ratio",
    "dns_query_rate",
    "dns_nxdomain_rate",
    "dns_nxdomain_ratio",
    "adblock_drop_rate",
    "adblock_drop_ratio",
    "firewall_reject_rate",
    "firewall_syn_drop_rate",
    "firewall_outbound_drop_rate",
    "k8s_api_request_rate",
    "k8s_api_401_rate",
    "k8s_api_403_rate",
    "k8s_api_error_ratio",
    "k8s_exec_probe_rate",
    "k8s_privilege_escalate_rate",
    "k8s_anonymous_request_rate",
    "k8s_pod_network_churn_rate",
]


class TelemetryVectorRequest(BaseModel):
    timestamp: Optional[str] = Field(None, description="ISO8601 timestamp of telemetry window")
    window_seconds: int = Field(10, description="Duration of sliding/tumbling aggregation window")
    features: List[float] = Field(
        ...,
        description="Flattened 32-dimensional array of normalized telemetry floats [0.0, 1.0]",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Contextual metadata (e.g. source router, interface, cluster)",
    )


class BatchTelemetryRequest(BaseModel):
    vectors: List[TelemetryVectorRequest] = Field(..., description="Batch of telemetry windows")


class FeatureResidual(BaseModel):
    feature_index: int
    feature_name: str
    residual_mse: float
    input_value: float
    reconstructed_value: float


class PredictionResponse(BaseModel):
    timestamp: Optional[str]
    is_anomaly: bool
    mse: float
    threshold: float
    inference_latency_ms: float
    device: str  # "edgetpu" or "cpu_fallback"
    top_root_cause: Optional[FeatureResidual]
    top_residuals: List[FeatureResidual]
    metadata: Optional[Dict[str, Any]] = None


class BatchPredictionResponse(BaseModel):
    results: List[PredictionResponse]
    total_evaluated: int
    anomalies_detected: int
    average_latency_ms: float


class StatusResponse(BaseModel):
    status: str
    edge_tpu_connected: bool
    device_type: str
    model_loaded: str
    input_tensor: Dict[str, Any]
    output_tensor: Dict[str, Any]
    anomaly_threshold: float
    total_inferences: int
