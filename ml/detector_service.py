import os
import sys
import time
import logging
import threading
from typing import Dict, Any
from flask import Flask, jsonify, Response
from prometheus_client import Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from ml.model import AnomalyDetector
from ml.collector import MetricCollector
from ml.train import train_and_save_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ml-detector")

# Prometheus Metrics for the ML Engine
GAUGE_ANOMALY = Gauge(
    "sentro_anomaly_detected",
    "Current anomaly state flagged by Isolation Forest (0 = Normal, 1 = Anomaly)"
)
GAUGE_SCORE = Gauge(
    "sentro_anomaly_score",
    "Continuous anomaly severity score normalized between 0.0 (safe) and 1.0 (critical anomaly)"
)
COUNTER_PREDICTIONS = Counter(
    "sentro_predictions_total",
    "Total number of telemetry evaluations performed by the ML model"
)
COUNTER_ANOMALIES = Counter(
    "sentro_anomalies_detected_total",
    "Total count of confirmed anomalies detected over time"
)

app = Flask(__name__)

class DetectionService:
    def __init__(
        self,
        prometheus_url: str = None,
        model_dir: str = None,
        poll_interval: int = 10
    ):
        self.prometheus_url = prometheus_url or os.environ.get("PROMETHEUS_URL", "http://prometheus:9090")
        self.model_dir = model_dir or os.environ.get("MODEL_DIR", "ml/models")
        self.poll_interval = poll_interval or int(os.environ.get("POLL_INTERVAL", "10"))

        self.collector = MetricCollector(prometheus_url=self.prometheus_url)
        self.detector = AnomalyDetector()
        self._ensure_model_loaded()

        self.latest_result: Dict[str, Any] = {
            "status": "INITIALIZING",
            "timestamp": time.time(),
            "metrics": {},
            "prediction": {}
        }
        self.running = False
        self._thread = None

    def _ensure_model_loaded(self):
        try:
            logger.info(f"Loading Isolation Forest model from {self.model_dir}...")
            self.detector.load(self.model_dir)
            logger.info("Isolation Forest model successfully loaded.")
        except Exception as e:
            logger.warning(f"Could not load model from {self.model_dir} ({e}). Training new baseline model...")
            self.detector = train_and_save_model(self.model_dir)

    def evaluate_once(self) -> Dict[str, Any]:
        """
        Executes one evaluation cycle: fetches telemetry, runs inference, updates gauges.
        """
        metrics = self.collector.get_latest_metrics_snapshot()
        prediction = self.detector.predict(metrics)

        # Update Prometheus Gauges & Counters
        is_anomaly = prediction["is_anomaly"]
        score = prediction["anomaly_score"]

        GAUGE_ANOMALY.set(1.0 if is_anomaly else 0.0)
        GAUGE_SCORE.set(score)
        COUNTER_PREDICTIONS.inc()
        if is_anomaly:
            COUNTER_ANOMALIES.inc()
            logger.warning(
                f"[ALERT] Anomaly Detected! Score: {score:.4f} | "
                f"CPU: {metrics.get('cpu_usage')}% | "
                f"RAM: {metrics.get('memory_usage')}% | "
                f"Req/s: {metrics.get('app_request_rate')}"
            )
        else:
            logger.info(f"[HEALTHY] Normal workload. Score: {score:.4f} (CPU: {metrics.get('cpu_usage')}%)")

        self.latest_result = {
            "status": prediction["status"],
            "timestamp": time.time(),
            "metrics": metrics,
            "prediction": prediction
        }
        return self.latest_result

    def _loop(self):
        logger.info(f"Anomaly Detection worker loop started. Polling every {self.poll_interval}s.")
        while self.running:
            try:
                self.evaluate_once()
            except Exception as e:
                logger.error(f"Error during detection cycle: {e}")
            time.sleep(self.poll_interval)

    def start_background_loop(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop(self):
        self.running = False

# Global Service Instance
service = DetectionService()

@app.route("/")
@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "sentro-ml-detector", "model_trained": service.detector.is_trained}), 200

@app.route("/status")
def status():
    return jsonify(service.latest_result), 200

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route("/evaluate", methods=["POST"])
def trigger_evaluation():
    result = service.evaluate_once()
    return jsonify(result), 200

def run_service(port: int = 8000):
    service.start_background_loop()
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    run_service(port=port)
