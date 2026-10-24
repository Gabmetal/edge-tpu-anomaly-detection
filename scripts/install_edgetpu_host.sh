#!/usr/bin/env bash
# ==============================================================================
# install_edgetpu_host.sh
# Production Host-Level Provisioning Script for Google Coral Edge TPU on K3s
#
# Supported Hardware:
#   - Google Coral USB Accelerator (USB IDs: 1a6e:089a / 18d1:9302)
#   - Google Coral PCIe / M.2 / Dual Edge TPU (/dev/apex_0, /dev/apex_1)
#
# Functionality:
#   1. Sets up the 'plugdev' group and permissions for non-root container runtimes.
#   2. Installs udev rules (99-edgetpu-accelerator.rules) for USB & PCIe Edge TPUs.
#   3. Installs libedgetpu runtime (libedgetpu1-std or libedgetpu1-max).
#   4. Verifies hardware presence, kernel drivers, and device file permissions.
# ==============================================================================

set -euo pipefail

# ANSI Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

LOG_INFO()  { echo -e "${CYAN}[INFO]${NC} $*"; }
LOG_SUCCESS() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
LOG_WARN()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
LOG_ERROR() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

RUNTIME_FLAVOR="std" # Default: std (250 MHz). Can be set to "max" (500 MHz)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UDEV_RULE_FILE="${SCRIPT_DIR}/99-edgetpu-accelerator.rules"

usage() {
    cat <<EOF
Usage: sudo ./install_edgetpu_host.sh [OPTIONS]

Options:
  -f, --flavor FLAVOR   Runtime package: 'std' (default: 250MHz) or 'max' (500MHz overclocked)
  -v, --verify-only     Only verify hardware presence and permission status without installing
  -h, --help            Show this help message

Examples:
  sudo ./install_edgetpu_host.sh --flavor std
  sudo ./install_edgetpu_host.sh --flavor max
  sudo ./install_edgetpu_host.sh --verify-only
EOF
    exit 0
}

# Parse flags
VERIFY_ONLY=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        -f|--flavor)
            RUNTIME_FLAVOR="$2"
            shift 2
            ;;
        -v|--verify-only)
            VERIFY_ONLY=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            LOG_ERROR "Unknown option: $1"
            usage
            ;;
    esac
done

if [[ "${RUNTIME_FLAVOR}" != "std" && "${RUNTIME_FLAVOR}" != "max" ]]; then
    LOG_ERROR "Invalid runtime flavor: ${RUNTIME_FLAVOR}. Must be 'std' or 'max'."
    exit 1
fi

# Verification Function
verify_hardware() {
    echo ""
    LOG_INFO "=== Verifying Google Coral Edge TPU Status ==="
    
    local FOUND=false

    # 1. Check USB Coral
    LOG_INFO "Checking USB Bus for Coral devices..."
    if command -v lsusb >/dev/null 2>&1; then
        local USB_DFU
        local USB_RUNTIME
        USB_DFU=$(lsusb -d 1a6e:089a 2>/dev/null || true)
        USB_RUNTIME=$(lsusb -d 18d1:9302 2>/dev/null || true)

        if [[ -n "${USB_DFU}" ]]; then
            LOG_SUCCESS "Found Google Coral USB in DFU/uninitialized mode (Vendor: 1a6e, Product: 089a):"
            echo "       ${USB_DFU}"
            FOUND=true
        fi
        if [[ -n "${USB_RUNTIME}" ]]; then
            LOG_SUCCESS "Found Google Coral USB in Runtime/active mode (Vendor: 18d1, Product: 9302):"
            echo "       ${USB_RUNTIME}"
            FOUND=true
        fi
    else
        LOG_WARN "lsusb command not found. Skipping USB scan."
    fi

    # 2. Check PCIe / M.2 Coral (Apex driver)
    LOG_INFO "Checking PCIe / Gasket / Apex devices (/dev/apex_*)..."
    if ls /dev/apex* >/dev/null 2>&1; then
        LOG_SUCCESS "Found PCIe / M.2 Edge TPU devices:"
        ls -la /dev/apex*
        FOUND=true
    else
        LOG_INFO "No /dev/apex_* PCIe devices detected (normal if using USB Accelerator)."
    fi

    # 3. Check /dev/bus/usb permissions
    LOG_INFO "Inspecting /dev/bus/usb/ permissions..."
    find /dev/bus/usb/ -type c -exec ls -l {} + 2>/dev/null | grep -E "1a6e|18d1|plugdev" || true

    # 4. Check libedgetpu library installation
    LOG_INFO "Checking for installed libedgetpu shared libraries..."
    if ldconfig -p | grep -i libedgetpu >/dev/null 2>&1; then
        LOG_SUCCESS "libedgetpu dynamic library registered in ldconfig:"
        ldconfig -p | grep -i libedgetpu
    elif ls -la /usr/lib/*-linux-gnu*/libedgetpu.so* /usr/lib/libedgetpu.so* >/dev/null 2>&1; then
        LOG_SUCCESS "libedgetpu library file located:"
        ls -la /usr/lib/*-linux-gnu*/libedgetpu.so* /usr/lib/libedgetpu.so* 2>/dev/null
    else
        LOG_WARN "libedgetpu dynamic library not found in standard system paths."
    fi

    if [[ "${FOUND}" = true ]]; then
        LOG_SUCCESS "Google Coral Edge TPU hardware detected and verified."
    else
        LOG_WARN "No Google Coral Edge TPU devices detected on USB or PCIe buses."
        LOG_WARN "Please ensure the Coral USB is plugged into a USB 3.0 port or PCIe slot."
    fi
}

if [[ "${VERIFY_ONLY}" = true ]]; then
    verify_hardware
    exit 0
fi

# Check root privileges
if [[ $EUID -ne 0 ]]; then
    LOG_ERROR "This script must be run as root or with sudo."
    exit 1
fi

LOG_INFO "Starting Host-Level Edge TPU Provisioning (Flavor: libedgetpu1-${RUNTIME_FLAVOR})..."

# Detect Architecture
ARCH="$(uname -m)"
case "${ARCH}" in
    x86_64)
        DEB_ARCH="amd64"
        ;;
    aarch64)
        DEB_ARCH="arm64"
        ;;
    armv7l)
        DEB_ARCH="armhf"
        ;;
    *)
        LOG_ERROR "Unsupported CPU architecture: ${ARCH}"
        exit 1
        ;;
esac
LOG_INFO "Detected host architecture: ${ARCH} (Debian package arch: ${DEB_ARCH})"

# Step 1: Ensure plugdev group exists
LOG_INFO "Step 1: Configuring user groups for non-root container device access..."
if ! getent group plugdev >/dev/null 2>&1; then
    groupadd -r plugdev
    LOG_SUCCESS "Created system group 'plugdev'."
else
    LOG_INFO "Group 'plugdev' already exists (GID: $(getent group plugdev | cut -d: -f3))."
fi

# Add current invoking user (SUDO_USER) to plugdev
if [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]]; then
    usermod -aG plugdev "${SUDO_USER}"
    LOG_SUCCESS "Added user '${SUDO_USER}' to group 'plugdev'."
fi

# Step 2: Install Udev Rules
LOG_INFO "Step 2: Installing Edge TPU udev rules..."
if [[ ! -f "${UDEV_RULE_FILE}" ]]; then
    LOG_ERROR "Udev rules file not found at ${UDEV_RULE_FILE}"
    exit 1
fi

cp -f "${UDEV_RULE_FILE}" /etc/udev/rules.d/99-edgetpu-accelerator.rules
chmod 644 /etc/udev/rules.d/99-edgetpu-accelerator.rules
LOG_SUCCESS "Installed /etc/udev/rules.d/99-edgetpu-accelerator.rules"

LOG_INFO "Reloading udev rules and triggering device subsystem..."
udevadm control --reload-rules && udevadm trigger
LOG_SUCCESS "Udev rules reloaded."

# Step 3: Install libedgetpu package
LOG_INFO "Step 3: Installing libedgetpu1-${RUNTIME_FLAVOR} runtime..."

INSTALL_SUCCESS=false

# Method A: Official Google Coral APT Repository
LOG_INFO "Attempting installation via Google Coral APT repository..."
mkdir -p /etc/apt/keyrings
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor --yes -o /etc/apt/keyrings/coral-edgetpu.gpg 2>/dev/null || true

if [[ -f /etc/apt/keyrings/coral-edgetpu.gpg ]]; then
    echo "deb [signed-by=/etc/apt/keyrings/coral-edgetpu.gpg] https://packages.cloud.google.com/apt coral-edgetpu-stable main" > /etc/apt/sources.list.d/coral-edgetpu.list
    if apt-get update -o Dir::Etc::sourcelist="sources.list.d/coral-edgetpu.list" -o Dir::Etc::sourceparts="-" -o APT::Get::List-Cleanup="0" >/dev/null 2>&1; then
        if apt-get install -y --no-install-recommends "libedgetpu1-${RUNTIME_FLAVOR}" >/dev/null 2>&1; then
            LOG_SUCCESS "Installed libedgetpu1-${RUNTIME_FLAVOR} from Google Coral APT repo."
            INSTALL_SUCCESS=true
        fi
    fi
fi

# Method B: Prebuilt Debian package from feranick/libedgetpu (modern releases)
if [[ "${INSTALL_SUCCESS}" = false ]]; then
    LOG_WARN "Google Coral APT repository install not available or failed. Trying modern prebuilt deb package..."
    TMP_DIR=$(mktemp -d)
    
    # Select release suitable for modern Debian/Ubuntu
    PACKAGE_NAME="libedgetpu1-${RUNTIME_FLAVOR}_16.0tf2.19.1-1.bookworm_${DEB_ARCH}.deb"
    DOWNLOAD_URL="https://github.com/feranick/libedgetpu/releases/download/16.0TF2.19.1-1/${PACKAGE_NAME}"
    
    LOG_INFO "Downloading ${DOWNLOAD_URL}..."
    if curl -fsSL -o "${TMP_DIR}/${PACKAGE_NAME}" "${DOWNLOAD_URL}"; then
        LOG_INFO "Installing ${PACKAGE_NAME} via dpkg..."
        if dpkg -i "${TMP_DIR}/${PACKAGE_NAME}" >/dev/null 2>&1 || apt-get install -y -f >/dev/null 2>&1; then
            LOG_SUCCESS "Installed libedgetpu1-${RUNTIME_FLAVOR} successfully via dpkg."
            INSTALL_SUCCESS=true
        fi
    else
        LOG_WARN "Failed to download from feranick/libedgetpu repository."
    fi
    rm -rf "${TMP_DIR}"
fi

# Method C: Direct binary extraction from edgetpu_runtime archive
if [[ "${INSTALL_SUCCESS}" = false ]]; then
    LOG_WARN "Attempting direct extraction from Google edgetpu_runtime archive..."
    TMP_DIR=$(mktemp -d)
    ARCHIVE_URL="https://github.com/google-coral/libedgetpu/releases/download/release-grouper/edgetpu_runtime_20221024.zip"
    
    if curl -fsSL -o "${TMP_DIR}/edgetpu_runtime.zip" "${ARCHIVE_URL}"; then
        unzip -q "${TMP_DIR}/edgetpu_runtime.zip" -d "${TMP_DIR}/extracted"
        # Find corresponding debian package
        DEB_CANDIDATE=$(find "${TMP_DIR}/extracted" -name "*${RUNTIME_FLAVOR}*${DEB_ARCH}*.deb" | head -n 1)
        if [[ -n "${DEB_CANDIDATE}" && -f "${DEB_CANDIDATE}" ]]; then
            dpkg -i "${DEB_CANDIDATE}" || apt-get install -y -f
            INSTALL_SUCCESS=true
            LOG_SUCCESS "Installed ${DEB_CANDIDATE} from release archive."
        fi
    fi
    rm -rf "${TMP_DIR}"
fi

# Step 4: Verify symlinks and ldconfig
if [[ "${INSTALL_SUCCESS}" = true ]]; then
    ldconfig
    LOG_SUCCESS "Dynamic library cache updated."
else
    LOG_ERROR "Could not automatically install libedgetpu1-${RUNTIME_FLAVOR}. Check network or package repositories."
fi

# Step 5: Final Verification
verify_hardware

echo ""
LOG_SUCCESS "=== Host Provisioning Complete ==="
LOG_INFO "To verify Edge TPU container access on K3s:"
LOG_INFO "  1. If using Coral Device Plugin, ensure DaemonSet 'k8s-device-plugin' is running."
LOG_INFO "  2. If using Direct Host Passthrough, mount '/dev/bus/usb' and set supplementalGroups: [$(getent group plugdev | cut -d: -f3)]."

