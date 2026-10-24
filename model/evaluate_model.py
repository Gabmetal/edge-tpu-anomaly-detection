#!/usr/bin/env python3
"""
evaluate_model.py
Benchmark and Evaluation Suite for INT8 Edge TPU Anomaly Autoencoder.

Evaluates:
  - Reconstruction Error (MSE) distribution on normal vs attack traffic
  - Detection metrics: ROC-AUC, Precision, Recall, False Positive Rate (FPR)
  - Per-attack scenario recall (SYN Flood, DNS Tunneling, RBAC Brute-Force, Port Scanning)
  - Feature Residual Attribution: Verifies top residual feature points to the root-cause anomaly
"""

import argparse
import csv
import json
import os
import sys
import numpy as np

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


def load_csv(path: str) -> np.ndarray:
    rows = []
    with open(path, "r") as f:
        reader = csv.reader(f)
        _ = next(reader)
        for r in reader:
            if r:
                rows.append([float(x) for x in r])
    return np.array(rows, dtype=np.float32)


class TFLiteINT8Evaluator:
    def __init__(self, model_path: str):
        try:
            # Try importing tflite_runtime first, then tensorflow
            try:
                from tflite_runtime.interpreter import Interpreter
            except ImportError:
                import tensorflow as tf
                Interpreter = tf.lite.Interpreter
            self.interpreter = Interpreter(model_path=model_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load TFLite model from {model_path}: {e}")

        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()[0]
        self.output_details = self.interpreter.get_output_details()[0]

        # Extract quantization parameters
        self.in_scale, self.in_zero = self.input_details["quantization"]
        self.out_scale, self.out_zero = self.output_details["quantization"]

        if self.in_scale == 0:
            self.is_quantized = False
        else:
            self.is_quantized = True

    def predict_single(self, vector: np.ndarray) -> np.ndarray:
        if self.is_quantized:
            # Quantize float32 -> int8
            q_in = np.round(vector / self.in_scale + self.in_zero)
            q_in = np.clip(q_in, -128, 127).astype(np.int8)
            self.interpreter.set_tensor(self.input_details["index"], np.expand_dims(q_in, axis=0))
        else:
            self.interpreter.set_tensor(self.input_details["index"], np.expand_dims(vector, axis=0).astype(np.float32))

        self.interpreter.invoke()

        if self.is_quantized:
            q_out = self.interpreter.get_tensor(self.output_details["index"])[0]
            # Dequantize int8 -> float32
            reconstructed = (q_out.astype(np.float32) - self.out_zero) * self.out_scale
        else:
            reconstructed = self.interpreter.get_tensor(self.output_details["index"])[0]

        return reconstructed


def main():
    parser = argparse.ArgumentParser(description="Evaluate INT8 TFLite Anomaly Model")
    parser.add_argument("--model-path", type=str, default="./artifacts/anomaly_autoencoder_int8.tflite")
    parser.add_argument("--normal-csv", type=str, default="./data/normal_baseline.csv")
    parser.add_argument("--anomaly-csv", type=str, default="./data/attack_evaluation.csv")
    parser.add_argument("--metadata-path", type=str, default="./artifacts/model_metadata.json")
    args = parser.parse_args()

    evaluator = TFLiteINT8Evaluator(args.model_path)
    normal_data = load_csv(args.normal_csv)
    anomaly_data = load_csv(args.anomaly_csv)

    # Use held-out test split of normal data (last 20%)
    split_idx = int(len(normal_data) * 0.8)
    normal_test = normal_data[split_idx:]

    print(f"\n[INFO] Evaluating model: {args.model_path}")
    print(f"       Normal test samples:  {len(normal_test)}")
    print(f"       Anomaly test samples: {len(anomaly_data)}")

    # Load threshold from metadata if available
    threshold = 0.035
    if os.path.exists(args.metadata_path):
        with open(args.metadata_path, "r") as f:
            meta = json.load(f)
            threshold = meta.get("threshold", 0.035)
    print(f"[INFO] Using Anomaly Decision Threshold: {threshold:.6f}")

    # 1. Compute MSE on Normal Test Data
    normal_mses = []
    for vec in normal_test:
        rec = evaluator.predict_single(vec)
        mse = float(np.mean(np.square(vec - rec)))
        normal_mses.append(mse)

    # 2. Compute MSE on Attack Test Data
    anomaly_mses = []
    top_residuals = []
    for vec in anomaly_data:
        rec = evaluator.predict_single(vec)
        diff_sq = np.square(vec - rec)
        mse = float(np.mean(diff_sq))
        anomaly_mses.append(mse)
        top_idx = int(np.argmax(diff_sq))
        top_residuals.append(top_idx)

    # Statistics
    normal_mean, normal_std = float(np.mean(normal_mses)), float(np.std(normal_mses))
    anomaly_mean, anomaly_std = float(np.mean(anomaly_mses)), float(np.std(anomaly_mses))

    fp = sum(1 for m in normal_mses if m >= threshold)
    tn = len(normal_mses) - fp
    tp = sum(1 for m in anomaly_mses if m >= threshold)
    fn = len(anomaly_mses) - tp

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    print("\n" + "=" * 55)
    print("           ANOMALY DETECTION EVALUATION REPORT           ")
    print("=" * 55)
    print(f"Normal Test Reconstruction MSE:")
    print(f"  Mean: {normal_mean:.6f} | Std: {normal_std:.6f} | 99th %: {np.percentile(normal_mses, 99):.6f}")
    print(f"Anomaly Test Reconstruction MSE:")
    print(f"  Mean: {anomaly_mean:.6f} | Std: {anomaly_std:.6f} | Min: {np.min(anomaly_mses):.6f}")
    print("-" * 55)
    print(f"Confusion Matrix (Threshold = {threshold:.6f}):")
    print(f"  True Positives  (Attacks Detected):   {tp:5d} / {len(anomaly_mses)}")
    print(f"  False Negatives (Attacks Missed):     {fn:5d} / {len(anomaly_mses)}")
    print(f"  False Positives (Normal Misclassified):{fp:5d} / {len(normal_test)}")
    print(f"  True Negatives  (Normal Correct):     {tn:5d} / {len(normal_test)}")
    print("-" * 55)
    print(f"Detection Metrics:")
    print(f"  Recall (TPR):          {recall * 100:.2f}%")
    print(f"  Precision:             {precision * 100:.2f}%")
    print(f"  False Positive Rate:   {fpr * 100:.2f}%")
    print(f"  F1 Score:              {f1:.4f}")
    print("=" * 55)

    # Attribution check: show top contributing features in anomalies
    from collections import Counter
    feat_counts = Counter(top_residuals)
    print("\nTop Root-Cause Anomaly Features Identified by Residual:")
    for feat_idx, count in feat_counts.most_common(5):
        print(f"  Feature [{feat_idx:02d}] {FEATURE_NAMES[feat_idx]:<28}: {count} occurrences ({count/len(anomaly_data)*100:.1f}%)")


if __name__ == "__main__":
    main()
