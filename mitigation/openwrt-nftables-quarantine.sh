#!/usr/bin/env bash
# ==============================================================================
# openwrt-nftables-quarantine.sh
# Production Automated Mitigation Script for OpenWrt (fw4 / nftables)
#
# Invoked by: Automated Mitigation Worker / Alertmanager Webhook
# Actions:
#   1. Ensures the 'quarantined_hosts' dynamic set exists in 'inet fw4'
#   2. Injects the offending IP into the set with an auto-expiring timeout
#   3. Drops and logs all forward traffic from the quarantined host
# ==============================================================================

set -euo pipefail

OFFENDING_IP="${1:-}"
TIMEOUT="${2:-3600s}" # Default 1 hour quarantine

if [[ -z "${OFFENDING_IP}" ]]; then
    echo "Usage: $0 <offending_ip> [timeout_duration]"
    echo "Example: $0 192.168.1.155 1h"
    exit 1
fi

echo "[INFO] Initiating OpenWrt Gateway Quarantine for IP: ${OFFENDING_IP} (Timeout: ${TIMEOUT})..."

# Check if running locally on OpenWrt or executing over SSH
OPENWRT_HOST="${OPENWRT_HOST:-}"

exec_cmd() {
    if [[ -n "${OPENWRT_HOST}" ]]; then
        ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "root@${OPENWRT_HOST}" "$@"
    else
        # Local execution (if running directly on router or test environment)
        "$@"
    fi
}

# 1. Initialize nftables dynamic set and drop rule if not already present
SETUP_NFT=$(cat << 'EOF'
nft list set inet fw4 quarantined_hosts >/dev/null 2>&1 || {
    echo "[INFO] Creating dynamic quarantine set in inet fw4..."
    nft add set inet fw4 quarantined_hosts '{ type ipv4_addr; flags timeout; }'
    nft insert rule inet fw4 forward ip saddr @quarantined_hosts counter log prefix "[QUARANTINED-DROP] " drop
    nft insert rule inet fw4 input ip saddr @quarantined_hosts counter drop
}
EOF
)

exec_cmd bash -c "${SETUP_NFT}" || true

# 2. Add offending host to quarantined set
ADD_IP="nft add element inet fw4 quarantined_hosts { ${OFFENDING_IP} timeout ${TIMEOUT} }"

if exec_cmd bash -c "${ADD_IP}"; then
    echo "[SUCCESS] Successfully isolated ${OFFENDING_IP} on OpenWrt gateway for ${TIMEOUT}."
    echo "          Packets from ${OFFENDING_IP} will be dropped and logged with prefix '[QUARANTINED-DROP]'."
else
    echo "[ERROR] Failed to insert ${OFFENDING_IP} into nftables quarantine set."
    exit 1
fi
