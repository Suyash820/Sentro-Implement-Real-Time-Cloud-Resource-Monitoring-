import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Union, Optional
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

FEATURE_NAMES = [
    "cpu_usage",
    "system_load",
    "memory_usage",
    "disk_usage",
    "disk_read_rate",
    "disk_write_rate",
    "network_in_rate",
    "network_out_rate",
    "tcp_connections",
    "app_request_rate",
    "app_p95_latency",
    "app_error_rate"
]

class AnomalyDetector:
    """
    Isolation Forest Machine Learning Anomaly Detector for Sentro Cloud Telemetry.
    """
    def __init__(self, contamination: float = 0.05, n_estimators: int = 100, random_state: int = 42):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=self.random_state
        )
        self.is_trained = False

    def _prepare_features(self, X: Union[Dict[str, float], pd.DataFrame, np.ndarray]) -> np.ndarray:
        """
        Converts input metrics (dict, DataFrame, or array) into the standard ordered 2D numpy array.
        """
        if isinstance(X, dict):
            row = [float(X.get(k, 0.0)) for k in FEATURE_NAMES]
            return np.array([row])
        elif isinstance(X, pd.DataFrame):
            # Select or add missing columns in exact order
            df = X.copy()
            for col in FEATURE_NAMES:
                if col not in df.columns:
                    df[col] = 0.0
            return df[FEATURE_NAMES].values
        elif isinstance(X, np.ndarray):
            if X.ndim == 1:
                return X.reshape(1, -1)
            return X
        else:
            raise ValueError(f"Unsupported data type for inference: {type(X)}")

    def train(self, X: Union[pd.DataFrame, np.ndarray]) -> Dict[str, Any]:
        """
        Trains the scaler and Isolation Forest model on baseline normal workload telemetry.
        """
        X_arr = self._prepare_features(X)
        X_scaled = self.scaler.fit_transform(X_arr)
        self.model.fit(X_scaled)
        self.is_trained = True

        return {
            "status": "trained",
            "samples": len(X_arr),
            "features": FEATURE_NAMES,
            "contamination": self.contamination,
            "n_estimators": self.n_estimators
        }

    def predict(self, X: Union[Dict[str, float], pd.DataFrame, np.ndarray]) -> Dict[str, Any]:
        """
        Evaluates input metrics for anomalies.
        Returns:
            - is_anomaly: True if anomalous (-1), False if normal (+1)
            - label: +1 (Normal) or -1 (Anomaly)
            - anomaly_score: Continuous float between 0.00 (healthy) and 1.00 (critical anomaly)
        """
        if not self.is_trained:
            raise RuntimeError("AnomalyDetector is not trained yet. Call train() or load() first.")

        X_arr = self._prepare_features(X)
        X_scaled = self.scaler.transform(X_arr)

        # Raw prediction: +1 for inliers, -1 for outliers
        preds = self.model.predict(X_scaled)
        # Decision function: > 0 for inliers, < 0 for outliers
        decision_scores = self.model.decision_function(X_scaled)

        # Map decision score smoothly to 0.0 - 1.0 anomaly severity score
        # Using sigmoid: when decision_score is strongly negative, anomaly_score approaches 1.0
        # When decision_score is positive (normal), anomaly_score is low (< 0.5)
        sigmoid_scores = 1.0 / (1.0 + np.exp(decision_scores * 4.0))

        if len(preds) == 1:
            is_anomaly = bool(preds[0] == -1)
            return {
                "is_anomaly": is_anomaly,
                "label": int(preds[0]),
                "status": "ANOMALY" if is_anomaly else "NORMAL",
                "anomaly_score": round(float(sigmoid_scores[0]), 4),
                "decision_score": round(float(decision_scores[0]), 4)
            }
        else:
            return {
                "is_anomaly": [bool(p == -1) for p in preds],
                "labels": [int(p) for p in preds],
                "anomaly_scores": [round(float(s), 4) for s in sigmoid_scores],
                "decision_scores": [round(float(ds), 4) for ds in decision_scores]
            }

    def save(self, model_dir: str = "ml/models") -> None:
        """
        Serializes the trained Isolation Forest model and scaler to disk.
        """
        if not self.is_trained:
            raise RuntimeError("Cannot save an untrained model.")
        os.makedirs(model_dir, exist_ok=True)
        joblib.dump(self.model, os.path.join(model_dir, "isolation_forest.joblib"))
        joblib.dump(self.scaler, os.path.join(model_dir, "scaler.joblib"))

    def load(self, model_dir: str = "ml/models") -> None:
        """
        Loads the trained Isolation Forest model and scaler from disk.
        """
        model_path = os.path.join(model_dir, "isolation_forest.joblib")
        scaler_path = os.path.join(model_dir, "scaler.joblib")

        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            raise FileNotFoundError(f"Model artifacts not found in {model_dir}")

        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        self.is_trained = True
