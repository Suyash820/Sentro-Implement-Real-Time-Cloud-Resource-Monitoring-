import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from ml.model import AnomalyDetector, FEATURE_NAMES

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def generate_baseline_data(n_samples: int = 2500, random_seed: int = 42) -> pd.DataFrame:
    """
    Generates synthetic baseline telemetry representing healthy, normal cloud operations across 12 parameters.
    """
    np.random.seed(random_seed)

    # 1. Compute Tier
    cpu_usage = np.clip(np.random.normal(loc=12.0, scale=5.0, size=n_samples), 1.0, 45.0)
    system_load = np.clip(np.random.normal(loc=0.6, scale=0.25, size=n_samples), 0.1, 2.0)

    # 2. Memory Tier (bounded flexibly between 15% and 82% to support varied instance profiles)
    memory_usage = np.clip(np.random.normal(loc=50.0, scale=14.0, size=n_samples), 15.0, 82.0)

    # 3. Storage & Disk Tier
    disk_usage = np.clip(np.random.normal(loc=35.0, scale=3.0, size=n_samples), 20.0, 55.0)
    disk_read = np.clip(np.random.normal(loc=1200.0, scale=400.0, size=n_samples), 200.0, 5000.0)
    disk_write = np.clip(np.random.normal(loc=2500.0, scale=800.0, size=n_samples), 500.0, 10000.0)

    # 4. Network Tier
    network_in = np.clip(np.random.normal(loc=2500.0, scale=800.0, size=n_samples), 800.0, 6000.0)
    network_out = np.clip(np.random.normal(loc=1500.0, scale=500.0, size=n_samples), 400.0, 3000.0)
    tcp_connections = np.clip(np.random.normal(loc=15.0, scale=3.0, size=n_samples), 5.0, 35.0)

    # 5. Application Workload Tier (Golden Signals)
    app_requests = np.clip(np.random.normal(loc=5.0, scale=2.0, size=n_samples), 0.5, 15.0)
    app_latency = np.clip(np.random.normal(loc=0.015, scale=0.005, size=n_samples), 0.002, 0.040)
    app_errors = np.clip(np.random.normal(loc=0.01, scale=0.01, size=n_samples), 0.0, 0.05)

    df = pd.DataFrame({
        "cpu_usage": cpu_usage,
        "system_load": system_load,
        "memory_usage": memory_usage,
        "disk_usage": disk_usage,
        "disk_read_rate": disk_read,
        "disk_write_rate": disk_write,
        "network_in_rate": network_in,
        "network_out_rate": network_out,
        "tcp_connections": tcp_connections,
        "app_request_rate": app_requests,
        "app_p95_latency": app_latency,
        "app_error_rate": app_errors
    })

    return df

def train_and_save_model(model_dir: str = "ml/models") -> AnomalyDetector:
    """
    Generates baseline training data, fits the Isolation Forest model, and persists weights.
    """
    print("[*] Generating baseline operational telemetry...")
    training_data = generate_baseline_data(n_samples=3000)
    print(f"[*] Generated {len(training_data)} training rows with features: {FEATURE_NAMES}")

    detector = AnomalyDetector(contamination=0.03, n_estimators=100, random_state=42)
    print("[*] Training Isolation Forest model on 12 telemetry features...")
    summary = detector.train(training_data)
    print(f"[+] Model successfully trained: {summary}")

    # Validate against normal sample
    normal_sample = {
        "cpu_usage": 15.0,
        "system_load": 0.55,
        "memory_usage": 60.0,
        "disk_usage": 36.0,
        "disk_read_rate": 1100.0,
        "disk_write_rate": 2200.0,
        "network_in_rate": 2200.0,
        "network_out_rate": 1400.0,
        "tcp_connections": 14.0,
        "app_request_rate": 4.5,
        "app_p95_latency": 0.018,
        "app_error_rate": 0.0
    }
    pred_normal = detector.predict(normal_sample)
    print(f"[+] Normal Sample Prediction: {pred_normal}")

    # Validate against anomalous sample (severe multi-tier saturation and error storm)
    anomaly_sample = {
        "cpu_usage": 98.5,
        "system_load": 8.5,
        "memory_usage": 94.0,
        "disk_usage": 96.0,
        "disk_read_rate": 450000.0,
        "disk_write_rate": 850000.0,
        "network_in_rate": 150000.0,
        "network_out_rate": 90000.0,
        "tcp_connections": 450.0,
        "app_request_rate": 280.0,
        "app_p95_latency": 1.950,
        "app_error_rate": 45.0
    }
    pred_anomaly = detector.predict(anomaly_sample)
    print(f"[!] Anomaly Sample Prediction: {pred_anomaly}")

    # Save artifacts
    print(f"[*] Saving model artifacts to {model_dir}...")
    detector.save(model_dir)
    print("[+] Model weights and scaler successfully saved!")

    return detector

if __name__ == "__main__":
    train_and_save_model()
