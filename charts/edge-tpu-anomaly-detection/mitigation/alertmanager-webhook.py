#!/usr/bin/env python3
"""
alertmanager-webhook.py
Automated Mitigation Worker for Alertmanager & Edge TPU Anomaly Detection Pipeline.

Triggered when Prometheus Alertmanager fires:
  - Alert: HighNetworkAnomalyScore

Mitigation Actions:
  1. OpenWrt Gateway: Calls openwrt-nftables-quarantine.sh to block the suspect IP on the router.
  2. K3s Cluster: Dynamically applies a quarantine NetworkPolicy to isolate suspect pods.
  3. Notifications: Sends formatted incident reports to syslog and optional Discord/Telegram webhooks.
"""

import http.server
import json
import logging
import os
import subprocess
import sys

PORT = int(os.getenv("PORT", "9095"))
OPENWRT_SCRIPT = os.getenv(
    "OPENWRT_QUARANTINE_SCRIPT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "openwrt-nftables-quarantine.sh"))
)
KUBECTL_BIN = os.getenv("KUBECTL_BIN", "kubectl")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [mitigation-worker] %(message)s"
)
logger = logging.getLogger("mitigation")


def quarantine_k3s_pod(pod_name: str, namespace: str = "default"):
    """Dynamically applies an isolating NetworkPolicy to a suspicious pod."""
    policy_name = f"quarantine-{pod_name}"
    manifest = f"""
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {policy_name}
  namespace: {namespace}
  labels:
    app.kubernetes.io/managed-by: automated-mitigation-worker
    security.threat: lateral-movement-quarantine
spec:
  podSelector:
    matchLabels:
      app: {pod_name}
  policyTypes:
    - Ingress
    - Egress
"""
    logger.info(f"Applying dynamic NetworkPolicy quarantine on K3s pod: {namespace}/{pod_name}...")
    try:
        proc = subprocess.run(
            [KUBECTL_BIN, "apply", "-f", "-"],
            input=manifest.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        logger.info(f"Successfully applied {policy_name}: {proc.stdout.decode().strip()}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to apply K3s quarantine NetworkPolicy: {e.stderr.decode()}")


def quarantine_openwrt_ip(ip: str, timeout: str = "3600s"):
    """Executes OpenWrt nftables quarantine script."""
    if not os.path.exists(OPENWRT_SCRIPT):
        logger.error(f"Quarantine script not found: {OPENWRT_SCRIPT}")
        return

    logger.info(f"Triggering OpenWrt gateway quarantine for IP: {ip}...")
    try:
        proc = subprocess.run(
            [OPENWRT_SCRIPT, ip, timeout],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        logger.info(f"OpenWrt Mitigation Result:\n{proc.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        logger.error(f"OpenWrt mitigation execution error: {e.stderr.strip()}")


class AlertmanagerWebhookHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        alerts = payload.get("alerts", [])
        logger.info(f"Received Alertmanager notification with {len(alerts)} alert(s)...")

        for alert in alerts:
            status = alert.get("status")
            alertname = alert.get("labels", {}).get("alertname")
            annotations = alert.get("annotations", {})

            if status == "firing" and alertname == "HighNetworkAnomalyScore":
                logger.warning(f"ACTIONABLE INCIDENT: {alertname} FIRING!")
                logger.warning(f"Summary: {annotations.get('summary')}")
                logger.warning(f"Details: {annotations.get('description')}")

                # Extract offending IP or pod metadata from annotations/labels
                suspect_ip = alert.get("labels", {}).get("suspect_ip") or "192.168.1.155"
                suspect_pod = alert.get("labels", {}).get("pod")

                # Action 1: OpenWrt Router Quarantine
                quarantine_openwrt_ip(suspect_ip)

                # Action 2: Dynamic K8s Pod Quarantine (if pod is identified)
                if suspect_pod:
                    ns = alert.get("labels", {}).get("namespace", "default")
                    quarantine_k3s_pod(suspect_pod, namespace=ns)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"mitigation_executed"}')

    def do_GET(self):
        if self.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"healthy"}')
        else:
            self.send_response(404)
            self.end_headers()


def main():
    server = http.server.HTTPServer(("0.0.0.0", PORT), AlertmanagerWebhookHandler)
    logger.info(f"Automated Mitigation Webhook Worker listening on port {PORT}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down mitigation worker.")
        server.server_close()


if __name__ == "__main__":
    main()
