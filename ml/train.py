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

def generate_baseline_data(n_samples: int = 2000, random_seed: int = 42) -> pd.DataFrame:
    """
    Generates synthetic baseline telemetry representing healthy, normal cloud operations.
    """
    np.random.seed(random_seed)

    # Normal CPU usage: centered around 15%, standard deviation 5%, bounded [2%, 45%]
    cpu_usage = np.clip(np.random.normal(loc=15.0, scale=5.0, size=n_samples), 2.0, 45.0)

    # Normal Memory usage: centered around 30%, standard deviation 4%, bounded [15%, 55%]
    memory_usage = np.clip(np.random.normal(loc=30.0, scale=4.0, size=n_samples), 15.0, 55.0)

    # Normal Network In: 1000 - 6000 Bps
    network_in = np.clip(np.random.normal(loc=2500.0, scale=800.0, size=n_samples), 800.0, 6000.0)

    # Normal Network Out: 500 - 3000 Bps
    network_out = np.clip(np.random.normal(loc=1500.0, scale=500.0, size=n_samples), 400.0, 3000.0)

    # Normal App Request Rate: 1 - 12 requests/second
    app_requests = np.clip(np.random.normal(loc=5.0, scale=2.0, size=n_samples), 0.5, 12.0)

    # Normal Latency: 0.005 - 0.035 seconds (5ms - 35ms)
    app_latency = np.clip(np.random.normal(loc=0.015, scale=0.005, size=n_samples), 0.002, 0.040)

    df = pd.DataFrame({
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,
        "network_in_rate": network_in,
        "network_out_rate": network_out,
        "app_request_rate": app_requests,
        "app_p95_latency": app_latency
    })

    return df

def train_and_save_model(model_dir: str = "ml/models") -> AnomalyDetector:
    """
    Generates baseline training data, fits the Isolation Forest model, and persists weights.
    """
    print("[*] Generating baseline operational telemetry...")
    training_data = generate_baseline_data(n_samples=2500)
    print(f"[*] Generated {len(training_data)} training rows with features: {FEATURE_NAMES}")

    detector = AnomalyDetector(contamination=0.03, n_estimators=100, random_state=42)
    print("[*] Training Isolation Forest model...")
    summary = detector.train(training_data)
    print(f"[+] Model successfully trained: {summary}")

    # Validate against normal sample
    normal_sample = {
        "cpu_usage": 18.0,
        "memory_usage": 32.0,
        "network_in_rate": 2200.0,
        "network_out_rate": 1400.0,
        "app_request_rate": 4.5,
        "app_p95_latency": 0.018
    }
    pred_normal = detector.predict(normal_sample)
    print(f"[+] Normal Sample Prediction: {pred_normal}")

    # Validate against anomalous sample (severe CPU spike and latency surge)
    anomaly_sample = {
        "cpu_usage": 96.5,
        "memory_usage": 88.0,
        "network_in_rate": 85000.0,
        "network_out_rate": 45000.0,
        "app_request_rate": 250.0,
        "app_p95_latency": 1.850
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
