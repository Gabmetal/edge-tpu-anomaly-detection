#!/usr/bin/env python3
"""
simulate_telemetry.py
Telemetry Simulation Tool for OpenWrt Router & K3s Cluster Telemetry Ingestion.

Can send:
  1. Syslog messages to Vector (UDP/TCP 514): dnsmasq queries, adblock drops, nftables rejected packets
  2. NetFlow flow records to Vector (UDP 2055)
  3. Direct HTTP POST vectors to the Inference Microservice (/v1/predict)

Supports attack simulation:
  --attack syn_flood | dns_tunnel | rbac_probe | port_scan
"""

import argparse
import json
import random
import socket
import sys
import time
import urllib.request

NORMAL_DOMAINS = ["google.com", "github.com", "cloudflare.com", "ubuntu.com", "debian.org", "wikipedia.org"]
BLOCKED_AD_DOMAINS = ["ads.doubleclick.net", "tracker.telemetry.io", "analytics.adservice.com", "pixel.tracking.net"]
MALICIOUS_DGA_DOMAINS = ["x9fk2l0a8z.cc", "m7q19v0c4.ru", "c2-exfil-beacon-99.biz", "dga-tunnel-chunk42.net"]


def send_syslog_udp(host: str, port: int, message: str):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(message.encode("utf-8"), (host, port))
    finally:
        sock.close()


def send_netflow_udp(host: str, port: int, flow_dict: dict):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        payload = json.dumps(flow_dict).encode("utf-8")
        sock.sendto(payload, (host, port))
    finally:
        sock.close()


def simulate_normal_cycle(vector_host: str, syslog_port: int, netflow_port: int, count: int = 20):
    print(f"[INFO] Emitting {count} normal telemetry events to Vector ({vector_host})...")
    ts = time.strftime("%b %d %H:%M:%S")
    for _ in range(count):
        # 1. Normal DNS query (RFC 3164 OpenWrt format)
        dom = random.choice(NORMAL_DOMAINS)
        dns_log = f"<134>{ts} openwrt dnsmasq[1420]: query[A] {dom} from 192.168.1.{random.randint(10, 50)}"
        send_syslog_udp(vector_host, syslog_port, dns_log)

        # 2. Normal Flow Record
        flow = {
            "bytes": random.randint(500, 15000),
            "pkts": random.randint(5, 30),
            "duration_ms": random.randint(100, 2000),
            "protocol": 6,
            "tcp_flags": "SF",
            "src_ip": f"192.168.1.{random.randint(10, 50)}",
            "dst_ip": f"104.26.{random.randint(1, 15)}.{random.randint(1, 250)}",
            "dst_port": 443,
        }
        send_netflow_udp(vector_host, netflow_port, flow)
        time.sleep(0.05)


def simulate_attack_cycle(vector_host: str, syslog_port: int, netflow_port: int, attack_type: str):
    print(f"\n[ALERT] Injecting Attack Scenario: {attack_type.upper()}...")
    ts = time.strftime("%b %d %H:%M:%S")

    if attack_type == "syn_flood":
        # Surge of SYN-only packets, high pps, small packet sizes
        for _ in range(150):
            flow = {
                "bytes": 60,
                "pkts": 1,
                "duration_ms": 10,
                "protocol": 6,
                "tcp_flags": "SYN",
                "src_ip": f"192.168.1.{random.randint(100, 200)}",
                "dst_ip": "10.0.0.50",
                "dst_port": 80,
            }
            send_netflow_udp(vector_host, netflow_port, flow)
            # Associated firewall drop log
            fw_log = f"<130>{ts} openwrt kernel: [NFT-REJECT] IN=br-lan OUT=wan PROTO=TCP SPT={random.randint(1024, 65535)} DPT=80 FLAGS=SYN"
            send_syslog_udp(vector_host, syslog_port, fw_log)

    elif attack_type == "dns_tunnel":
        # Surging NXDOMAIN queries for random high-entropy subdomains
        for _ in range(80):
            dga = f"{random.randint(10000, 99999)}.{random.choice(MALICIOUS_DGA_DOMAINS)}"
            dns_log = f"<134>{ts} openwrt dnsmasq[1420]: query[TXT] {dga} reply {dga} is NXDOMAIN"
            send_syslog_udp(vector_host, syslog_port, dns_log)

    elif attack_type == "port_scan":
        # Scanning multiple target ports with rejected SYNs
        target_ip = "192.168.1.1"
        for port in range(20, 120):
            flow = {
                "bytes": 60,
                "pkts": 1,
                "duration_ms": 5,
                "protocol": 6,
                "tcp_flags": "SYN",
                "src_ip": "192.168.1.155",
                "dst_ip": target_ip,
                "dst_port": port,
            }
            send_netflow_udp(vector_host, netflow_port, flow)
            fw_log = f"<130>{ts} openwrt kernel: [NFT-REJECT] IN=br-lan OUT= PROTO=TCP SPT=49152 DPT={port} FLAGS=SYN"
            send_syslog_udp(vector_host, syslog_port, fw_log)


def send_direct_prediction(api_url: str, attack: bool = False):
    print(f"\n[INFO] Sending direct test inference vector to {api_url} (attack={attack})...")
    features = [0.1] * 32
    if attack:
        features[1] = 0.95   # packet rate
        features[4] = 0.98   # syn rate
        features[7] = 0.92   # syn/fin ratio
        features[22] = 0.88  # firewall syn drops

    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window_seconds": 10,
        "features": features,
        "metadata": {"simulation": True, "scenario": "attack" if attack else "normal"},
    }

    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req) as resp:
        duration_ms = (time.perf_counter() - t0) * 1000.0
        data = json.loads(resp.read().decode("utf-8"))
        print(f"[RESPONSE in {duration_ms:.2f}ms]: is_anomaly={data['is_anomaly']}, mse={data['mse']:.6f}, device={data['device']}")
        if data.get("top_root_cause"):
            rc = data["top_root_cause"]
            print(f"  Root Cause: [{rc['feature_index']:02d}] {rc['feature_name']} (residual={rc['residual_mse']:.4f})")


def main():
    parser = argparse.ArgumentParser(description="Simulate Telemetry for Vector & Edge TPU Anomaly Detection")
    parser.add_argument("--vector-host", type=str, default="127.0.0.1", help="Vector UDP receiver host")
    parser.add_argument("--syslog-port", type=int, default=514, help="Vector Syslog UDP port")
    parser.add_argument("--netflow-port", type=int, default=2055, help="Vector NetFlow UDP port")
    parser.add_argument("--inference-url", type=str, default="http://127.0.0.1:8000/v1/predict")
    parser.add_argument("--mode", choices=["normal", "attack", "direct_http"], default="normal")
    parser.add_argument("--attack-type", choices=["syn_flood", "dns_tunnel", "port_scan"], default="syn_flood")
    args = parser.parse_args()

    if args.mode == "normal":
        simulate_normal_cycle(args.vector_host, args.syslog_port, args.netflow_port)
    elif args.mode == "attack":
        simulate_attack_cycle(args.vector_host, args.syslog_port, args.netflow_port, args.attack_type)
    elif args.mode == "direct_http":
        send_direct_prediction(args.inference_url, attack=False)
        send_direct_prediction(args.inference_url, attack=True)


if __name__ == "__main__":
    main()
