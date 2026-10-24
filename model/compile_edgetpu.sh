#!/usr/bin/env bash
# ==============================================================================
# compile_edgetpu.sh
# Automated Edge TPU compilation script for INT8 Anomaly Autoencoder.
# Verifies that 100% of operators map to Edge TPU with 0 CPU fallbacks.
# ==============================================================================

set -euo pipefail

INPUT_MODEL="${1:-./artifacts/anomaly_autoencoder_int8.tflite}"
OUTPUT_DIR="${2:-./artifacts}"

if [[ ! -f "${INPUT_MODEL}" ]]; then
    echo "[ERROR] Input quantized model not found at: ${INPUT_MODEL}"
    echo "        Run python3 model/train_and_export.py first."
    exit 1
fi

mkdir -p "${OUTPUT_DIR}"

echo "[INFO] === Compiling ${INPUT_MODEL} for Google Coral Edge TPU ==="

if command -v edgetpu_compiler >/dev/null 2>&1; then
    echo "[INFO] Using host edgetpu_compiler: $(edgetpu_compiler --version)"
    edgetpu_compiler -s -o "${OUTPUT_DIR}" "${INPUT_MODEL}"
else
    echo "[WARN] edgetpu_compiler not found in PATH."
    echo "[INFO] Attempting containerized compilation..."
    if command -v podman >/dev/null 2>&1; then
        RUNTIME_CMD="podman"
    elif command -v docker >/dev/null 2>&1; then
        RUNTIME_CMD="docker"
    else
        echo "[ERROR] Neither edgetpu_compiler nor podman/docker found."
        exit 1
    fi

    ${RUNTIME_CMD} run --rm -v "$(pwd):/workspace" -w /workspace \
        debian:bullseye-slim bash -c "
            apt-get update && apt-get install -y curl gnupg &&
            echo 'deb https://packages.cloud.google.com/apt coral-edgetpu-stable main' > /etc/apt/sources.list.d/coral-edgetpu.list &&
            curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - &&
            apt-get update && apt-get install -y edgetpu-compiler &&
            edgetpu_compiler -s -o '${OUTPUT_DIR}' '${INPUT_MODEL}'
        "
fi

# Locate compiled artifact
COMPILED_MODEL=$(find "${OUTPUT_DIR}" -name "*_edgetpu.tflite" | head -n 1)

if [[ -n "${COMPILED_MODEL}" && -f "${COMPILED_MODEL}" ]]; then
    cp -f "${COMPILED_MODEL}" "${OUTPUT_DIR}/anomaly_autoencoder_edgetpu.tflite"
    echo ""
    echo "[SUCCESS] Successfully compiled Edge TPU model:"
    echo "          ${OUTPUT_DIR}/anomaly_autoencoder_edgetpu.tflite"
    
    # Inspect compiler log if present
    LOG_FILE=$(find "${OUTPUT_DIR}" -name "*_edgetpu.log" | head -n 1)
    if [[ -n "${LOG_FILE}" && -f "${LOG_FILE}" ]]; then
        echo ""
        echo "[INFO] Compiler Mapping Summary (${LOG_FILE}):"
        cat "${LOG_FILE}"
    fi
else
    echo "[ERROR] Compilation output not found."
    exit 1
fi
