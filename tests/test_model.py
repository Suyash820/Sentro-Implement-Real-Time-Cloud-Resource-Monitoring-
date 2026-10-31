import pytest
import sys
import os
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from ml.model import AnomalyDetector, FEATURE_NAMES

def test_anomaly_detector_training_and_prediction():
    detector = AnomalyDetector(contamination=0.05, n_estimators=50, random_state=42)
    assert not detector.is_trained

    # Generate synthetic training data
    np.random.seed(42)
    data = {
        "cpu_usage": np.random.normal(20, 5, 200),
        "memory_usage": np.random.normal(30, 5, 200),
        "network_in_rate": np.random.normal(2000, 500, 200),
        "network_out_rate": np.random.normal(1000, 250, 200),
        "app_request_rate": np.random.normal(5, 1, 200),
        "app_p95_latency": np.random.normal(0.02, 0.005, 200),
    }
    df = pd.DataFrame(data)

    res = detector.train(df)
    assert detector.is_trained
    assert res["status"] == "trained"
    assert res["samples"] == 200

    # Normal sample
    normal_metrics = {
        "cpu_usage": 21.0,
        "memory_usage": 31.0,
        "network_in_rate": 2050.0,
        "network_out_rate": 1020.0,
        "app_request_rate": 5.1,
        "app_p95_latency": 0.021
    }
    pred_normal = detector.predict(normal_metrics)
    assert pred_normal["is_anomaly"] is False
    assert pred_normal["label"] == 1
    assert pred_normal["status"] == "NORMAL"
    assert 0.0 <= pred_normal["anomaly_score"] <= 1.0

    # Extreme anomalous sample
    anomalous_metrics = {
        "cpu_usage": 99.0,
        "memory_usage": 98.0,
        "network_in_rate": 500000.0,
        "network_out_rate": 250000.0,
        "app_request_rate": 500.0,
        "app_p95_latency": 5.0
    }
    pred_anom = detector.predict(anomalous_metrics)
    assert pred_anom["is_anomaly"] is True
    assert pred_anom["label"] == -1
    assert pred_anom["status"] == "ANOMALY"
    assert pred_anom["anomaly_score"] > pred_normal["anomaly_score"]

def test_anomaly_detector_save_and_load(tmp_path):
    model_dir = str(tmp_path / "models")
    detector = AnomalyDetector(n_estimators=30, random_state=42)

    X = np.random.normal(10, 2, (100, 6))
    detector.train(X)
    detector.save(model_dir)

    loaded_detector = AnomalyDetector()
    loaded_detector.load(model_dir)
    assert loaded_detector.is_trained

    # Predict with loaded model
    sample = {"cpu_usage": 10.0, "memory_usage": 10.0, "network_in_rate": 10.0, "network_out_rate": 10.0, "app_request_rate": 10.0, "app_p95_latency": 10.0}
    pred = loaded_detector.predict(sample)
    assert "is_anomaly" in pred
