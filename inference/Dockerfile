# ==============================================================================
# Production Dockerfile for Edge TPU Anomaly Inference Microservice
# Base: Debian Bullseye with Python 3.11, libedgetpu1-std, and tflite-runtime
# Security: Non-root execution in 'plugdev' group for Coral USB/PCIe access
# ==============================================================================

FROM python:3.11-slim-bookworm AS runtime

LABEL maintainer="Platform Engineering & Edge ML Team"
LABEL description="Google Coral Edge TPU INT8 Network Anomaly Detection Microservice"

# Prevent interactive prompts and Python byte-compiling
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Install essential system dependencies and USB / Edge TPU libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    libusb-1.0-0 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install libedgetpu runtime (standard frequency 250MHz)
# Uses feranick's production build compiled for modern glibc and Debian
RUN curl -fsSL -o /tmp/libedgetpu.deb https://github.com/feranick/libedgetpu/releases/download/16.0TF2.19.1-1/libedgetpu1-std_16.0tf2.19.1-1.bookworm_amd64.deb && \
    dpkg -i /tmp/libedgetpu.deb && \
    rm -f /tmp/libedgetpu.deb && \
    ldconfig

# Create dedicated non-root user matching Coral host permissions
# Host Coral group 'plugdev' typically GID 46 (Ubuntu) or 44 (Debian)
RUN groupadd -g 46 plugdev || true && \
    groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -G plugdev -s /bin/bash -m appuser

# Set up isolated virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install python dependencies including tflite-runtime and numpy 1.x
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip install --no-cache-dir \
    "numpy>=1.23.0,<2.0.0" \
    "tflite-runtime==2.14.0" \
    "fastapi>=0.100.0" \
    "uvicorn[standard]>=0.22.0" \
    "prometheus_client>=0.17.0" \
    "pydantic>=2.0.0"

WORKDIR /app

# Copy model artifacts
COPY artifacts/ /models/
RUN chown -R appuser:appuser /models

# Copy inference service code
COPY inference/app/ /app/app/
RUN chown -R appuser:appuser /app

# Switch to non-root execution
USER 10001:46

# Expose HTTP port for API and Prometheus scraping
EXPOSE 8000

# Container Healthcheck
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/healthz || exit 1

# Default runtime configuration
ENV MODEL_PATH="/models/anomaly_autoencoder_edgetpu.tflite" \
    CPU_FALLBACK_MODEL_PATH="/models/anomaly_autoencoder_int8.tflite" \
    METADATA_PATH="/models/model_metadata.json" \
    HOST="0.0.0.0" \
    PORT="8000"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
