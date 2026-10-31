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
    data = {f: np.random.normal(10, 2, 200) for f in FEATURE_NAMES}
    df = pd.DataFrame(data)

    res = detector.train(df)
    assert detector.is_trained
    assert res["status"] == "trained"
    assert res["samples"] == 200

    # Normal sample
    normal_metrics = {f: 10.0 for f in FEATURE_NAMES}
    pred_normal = detector.predict(normal_metrics)
    assert pred_normal["is_anomaly"] is False
    assert pred_normal["label"] == 1
    assert pred_normal["status"] == "NORMAL"
    assert 0.0 <= pred_normal["anomaly_score"] <= 1.0

    # Extreme anomalous sample
    anomalous_metrics = {f: 50000.0 for f in FEATURE_NAMES}
    pred_anom = detector.predict(anomalous_metrics)
    assert pred_anom["is_anomaly"] is True
    assert pred_anom["label"] == -1
    assert pred_anom["status"] == "ANOMALY"
    assert pred_anom["anomaly_score"] > pred_normal["anomaly_score"]

def test_anomaly_detector_save_and_load(tmp_path):
    model_dir = str(tmp_path / "models")
    detector = AnomalyDetector(n_estimators=30, random_state=42)

    X = np.random.normal(10, 2, (100, len(FEATURE_NAMES)))
    detector.train(X)
    detector.save(model_dir)

    loaded_detector = AnomalyDetector()
    loaded_detector.load(model_dir)
    assert loaded_detector.is_trained

    # Predict with loaded model
    sample = {f: 10.0 for f in FEATURE_NAMES}
    pred = loaded_detector.predict(sample)
    assert "is_anomaly" in pred
