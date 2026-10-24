"""
config.py
Configuration parameters for the Edge TPU Anomaly Inference Microservice.
Supports environment variable overrides for 12-factor cloud-native deployment.
"""

import os
from pydantic import BaseModel, Field


class Settings(BaseModel):
    # Service Information
    app_name: str = "Edge TPU Anomaly Detection Microservice"
    environment: str = os.getenv("ENVIRONMENT", "production")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    log_level: str = os.getenv("LOG_LEVEL", "info")

    # Model Configuration
    model_path: str = os.getenv(
        "MODEL_PATH",
        "/models/anomaly_autoencoder_edgetpu.tflite"
    )
    cpu_fallback_model_path: str = os.getenv(
        "CPU_FALLBACK_MODEL_PATH",
        "/models/anomaly_autoencoder_int8.tflite"
    )
    metadata_path: str = os.getenv(
        "METADATA_PATH",
        "/models/model_metadata.json"
    )
    edgetpu_delegate_path: str = os.getenv(
        "EDGETPU_DELEGATE_PATH",
        "libedgetpu.so.1"
    )

    # Edge TPU Device Identifier:
    # None for first available device, "usb" for USB Coral, "pci" for PCIe Coral, or specific device path
    edgetpu_device: str = os.getenv("EDGETPU_DEVICE", "")

    # Anomaly Decision Parameters
    # Default threshold calibrated on 99.5th percentile of normal baseline
    anomaly_threshold: float = float(os.getenv("ANOMALY_THRESHOLD", "0.001806"))
    input_dimension: int = int(os.getenv("INPUT_DIMENSION", "32"))

    # Reconnection & Circuit Breaker Settings
    max_reconnect_retries: int = int(os.getenv("MAX_RECONNECT_RETRIES", "5"))
    reconnect_base_delay_sec: float = float(os.getenv("RECONNECT_BASE_DELAY_SEC", "1.0"))


settings = Settings()
