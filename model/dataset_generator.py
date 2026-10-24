#!/usr/bin/env python3
"""
dataset_generator.py
Synthetic Telemetry Generator & Baseline CSV Ingestion for Edge TPU Anomaly Autoencoder.

Generates 32-dimensional normalized time-window feature vectors representing:
  - Normal operational cluster & network baseline
  - Injected attack scenarios (SYN Flood, DNS Tunneling, RBAC Brute-Force, Lateral Port Scan)

Feature Index Mapping (32 Dimensions, normalized [0.0, 1.0]):
  0: flow_bytes_rate               16: dns_query_rate
  1: flow_packets_rate             17: dns_nxdomain_rate
  2: flow_avg_packet_size          18: dns_nxdomain_ratio
  3: flow_avg_duration_sec         19: adblock_drop_rate
  4: flow_syn_rate                 20: adblock_drop_ratio
  5: flow_fin_rate                 21: firewall_reject_rate
  6: flow_rst_rate                 22: firewall_syn_drop_rate
  7: flow_syn_fin_ratio            23: firewall_outbound_drop_rate
  8: flow_rst_ratio                24: k8s_api_request_rate
  9: flow_tcp_ratio                25: k8s_api_401_rate
 10: flow_udp_ratio                26: k8s_api_403_rate
 11: flow_icmp_ratio               27: k8s_api_error_ratio
 12: flow_unique_src_ips           28: k8s_exec_probe_rate
 13: flow_unique_dst_ips           29: k8s_privilege_escalate_rate
 14: flow_unique_dst_ports         30: k8s_anonymous_request_rate
 15: flow_fanout_ratio             31: k8s_pod_network_churn_rate
"""

import argparse
import csv
import math
import os
import random
from typing import List, Tuple

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


def clamp(val: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    return max(min_val, min(max_val, val))


def generate_normal_sample() -> List[float]:
    """Generates a single 32-dim feature vector of normal operational telemetry."""
    # Baseline network activity
    bytes_rate = clamp(random.betavariate(2, 8) * 0.4)
    pkts_rate = clamp(random.betavariate(2, 7) * 0.35)
    avg_pkt_sz = clamp(random.gauss(0.45, 0.1))
    avg_dur = clamp(random.betavariate(2, 5) * 0.3)

    # TCP Flags & Ratios
    syn = clamp(random.betavariate(1.5, 8) * 0.25)
    fin = clamp(syn * random.uniform(0.85, 1.15))
    rst = clamp(random.betavariate(1, 15) * 0.1)
    syn_fin_ratio = clamp((syn / (fin + 0.05)) * 0.5)
    rst_ratio = clamp((rst / (pkts_rate + 0.1)) * 0.2)

    # Protocols
    tcp = clamp(random.gauss(0.7, 0.08))
    udp = clamp(1.0 - tcp - random.uniform(0.01, 0.05))
    icmp = clamp(random.uniform(0.0, 0.03))

    # IP & Port Cardinality
    u_src = clamp(random.betavariate(2, 10) * 0.25)
    u_dst = clamp(random.betavariate(3, 8) * 0.35)
    u_ports = clamp(random.betavariate(2, 8) * 0.2)
    fanout = clamp((u_dst / (u_src + 0.05)) * 0.3)

    # DNS & Adblock
    dns_q = clamp(random.betavariate(2, 6) * 0.35)
    dns_nx = clamp(random.betavariate(1, 20) * 0.08)
    dns_nx_ratio = clamp((dns_nx / (dns_q + 0.05)) * 0.1)
    adblock_drop = clamp(random.betavariate(1.5, 10) * 0.2)
    adblock_ratio = clamp((adblock_drop / (dns_q + 0.05)) * 0.25)
    adblock_drop_ratio = adblock_ratio

    # Firewall
    fw_reject = clamp(random.betavariate(1, 25) * 0.05)
    fw_syn_drop = clamp(random.betavariate(1, 30) * 0.04)
    fw_out_drop = clamp(random.betavariate(1, 40) * 0.02)

    # K8s Internal Audit
    k8s_req = clamp(random.betavariate(2, 5) * 0.4)
    k8s_401 = clamp(random.betavariate(1, 50) * 0.02)
    k8s_403 = clamp(random.betavariate(1, 40) * 0.03)
    k8s_err_ratio = clamp((k8s_401 + k8s_403) / (k8s_req + 0.1))
    k8s_exec = 0.0 if random.random() > 0.02 else clamp(random.uniform(0.01, 0.05))
    k8s_escalate = 0.0
    k8s_anon = clamp(random.betavariate(1, 50) * 0.02)
    k8s_churn = clamp(random.betavariate(1, 20) * 0.08)

    return [
        round(bytes_rate, 5),
        round(pkts_rate, 5),
        round(avg_pkt_sz, 5),
        round(avg_dur, 5),
        round(syn, 5),
        round(fin, 5),
        round(rst, 5),
        round(syn_fin_ratio, 5),
        round(rst_ratio, 5),
        round(tcp, 5),
        round(udp, 5),
        round(icmp, 5),
        round(u_src, 5),
        round(u_dst, 5),
        round(u_ports, 5),
        round(fanout, 5),
        round(dns_q, 5),
        round(dns_nx, 5),
        round(dns_nx_ratio, 5),
        round(adblock_drop, 5),
        round(adblock_drop_ratio, 5),
        round(fw_reject, 5),
        round(fw_syn_drop, 5),
        round(fw_out_drop, 5),
        round(k8s_req, 5),
        round(k8s_401, 5),
        round(k8s_403, 5),
        round(k8s_err_ratio, 5),
        round(k8s_exec, 5),
        round(k8s_escalate, 5),
        round(k8s_anon, 5),
        round(k8s_churn, 5),
    ]


def generate_anomaly_sample(attack_type: str = "random") -> Tuple[List[float], str]:
    """Generates an attack vector representing network intrusion or cluster abuse."""
    sample = generate_normal_sample()

    types = ["syn_flood", "dns_tunnel_c2", "k8s_rbac_probe", "lateral_port_scan"]
    if attack_type not in types:
        attack_type = random.choice(types)

    if attack_type == "syn_flood":
        # Massive SYN surge, skewed SYN/FIN, high packet count, small packet size
        sample[0] = clamp(sample[0] + random.uniform(0.4, 0.7))  # bytes
        sample[1] = clamp(random.uniform(0.85, 1.0))            # packets
        sample[2] = clamp(random.uniform(0.05, 0.15))           # small avg packet
        sample[4] = clamp(random.uniform(0.85, 1.0))            # high SYN
        sample[5] = clamp(sample[5] * 0.1)                      # very low FIN
        sample[7] = clamp(random.uniform(0.8, 1.0))             # massive syn/fin ratio
        sample[9] = 0.98                                        # 98% TCP
        sample[10] = 0.02
        sample[22] = clamp(random.uniform(0.6, 0.95))           # firewall dropping SYNs

    elif attack_type == "dns_tunnel_c2":
        # DNS flood with high NXDOMAIN and unusual payload size
        sample[16] = clamp(random.uniform(0.75, 1.0))           # high dns query rate
        sample[17] = clamp(random.uniform(0.6, 0.95))           # high nxdomain rate
        sample[18] = clamp(random.uniform(0.7, 0.98))           # high nxdomain ratio
        sample[20] = clamp(random.uniform(0.4, 0.8))            # adblock/sinkhole hit
        sample[10] = clamp(random.uniform(0.7, 0.9))            # heavy UDP traffic

    elif attack_type == "k8s_rbac_probe":
        # Unauthorized API queries, privilege escalation attempts, exec probes
        sample[24] = clamp(random.uniform(0.7, 0.95))           # k8s api requests
        sample[25] = clamp(random.uniform(0.6, 0.9))            # 401 Unauthorized
        sample[26] = clamp(random.uniform(0.65, 0.95))          # 403 Forbidden
        sample[27] = clamp(random.uniform(0.75, 1.0))           # api error ratio
        sample[28] = clamp(random.uniform(0.5, 0.85))           # pod exec probe rate
        sample[29] = clamp(random.uniform(0.4, 0.8))            # rolebinding escalation
        sample[30] = clamp(random.uniform(0.5, 0.85))           # anonymous probe

    elif attack_type == "lateral_port_scan":
        # Sweeping destination IPs and ports, high firewall rejects
        sample[13] = clamp(random.uniform(0.8, 1.0))            # unique dst IPs
        sample[14] = clamp(random.uniform(0.85, 1.0))           # unique dst ports
        sample[15] = clamp(random.uniform(0.75, 1.0))           # fanout ratio
        sample[21] = clamp(random.uniform(0.65, 0.95))          # firewall reject rate
        sample[22] = clamp(random.uniform(0.7, 0.98))           # syn drops on closed ports
        sample[6] = clamp(random.uniform(0.5, 0.8))             # RST replies

    return sample, attack_type


def save_csv(filename: str, rows: List[List[float]], header: List[str] = None):
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        if header:
            writer.writerow(header)
        writer.writerows(rows)
    print(f"[INFO] Wrote {len(rows)} samples to {filename}")


def load_and_validate_csv(filename: str) -> List[List[float]]:
    """Loads and validates a CSV file containing 32-dim feature vectors."""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"CSV file not found: {filename}")

    data = []
    with open(filename, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        # Check column count
        if len(header) != 32:
            print(f"[WARN] Header column count is {len(header)} (expected 32)")

        for line_num, row in enumerate(reader, start=2):
            if not row:
                continue
            if len(row) != 32:
                raise ValueError(f"Line {line_num} in {filename} has {len(row)} columns; expected 32.")
            vector = [float(val) for val in row]
            for idx, val in enumerate(vector):
                if val < 0.0 or val > 1.0:
                    raise ValueError(f"Line {line_num}, col {idx} value {val} out of bounds [0.0, 1.0]")
            data.append(vector)

    print(f"[SUCCESS] Loaded and validated {len(data)} vectors from {filename}")
    return data


def main():
    parser = argparse.ArgumentParser(description="Dataset Generator & Ingestion for Edge TPU Anomaly Autoencoder")
    parser.add_argument("--normal-samples", type=int, default=25000, help="Number of normal baseline samples")
    parser.add_argument("--anomaly-samples", type=int, default=2500, help="Number of attack test samples")
    parser.add_argument("--output-dir", type=str, default="./data", help="Target directory for generated CSVs")
    parser.add_argument("--validate-csv", type=str, default=None, help="Validate an existing CSV file")
    args = parser.parse_args()

    if args.validate_csv:
        load_and_validate_csv(args.validate_csv)
        return

    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    print(f"[INFO] Generating {args.normal_samples} normal baseline samples...")
    normal_data = [generate_normal_sample() for _ in range(args.normal_samples)]
    normal_csv = os.path.join(output_dir, "normal_baseline.csv")
    save_csv(normal_csv, normal_data, header=FEATURE_NAMES)

    print(f"[INFO] Generating {args.anomaly_samples} attack evaluation samples...")
    anomaly_data = []
    labels = []
    for _ in range(args.anomaly_samples):
        vec, label = generate_anomaly_sample()
        anomaly_data.append(vec)
        labels.append(label)
    anomaly_csv = os.path.join(output_dir, "attack_evaluation.csv")
    save_csv(anomaly_csv, anomaly_data, header=FEATURE_NAMES)

    print(f"[SUCCESS] Datasets generated in {output_dir}")


if __name__ == "__main__":
    main()
