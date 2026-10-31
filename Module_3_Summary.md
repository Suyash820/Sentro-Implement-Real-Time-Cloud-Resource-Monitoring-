# Module 3 Summary: Intelligent Anomaly Detection with Machine Learning (Isolation Forest)

In **Module 3**, we upgraded the Sentro Observability platform into an intelligent AIOps system by implementing unsupervised Machine Learning (**Isolation Forest**) to automatically detect, score, and visualize cloud resource anomalies in real time.

---

## 1. Metric Telemetry Ingestion Pipeline (`ml/collector.py`)
* **Metric Collector**: Automatically queries the Prometheus HTTP API (`/api/v1/query` and `/api/v1/query_range`).
* **Multi-Dimensional Metrics**:
  * `cpu_usage`: Real-time percentage of CPU utilized across all cores.
  * `memory_usage`: Percentage of system RAM consumed.
  * `network_in_rate`: Received bytes per second across active network interfaces.
  * `network_out_rate`: Transmitted bytes per second across active network interfaces.
  * `app_request_rate`: HTTP request throughput (req/sec) against the Flask API.
  * `app_p95_latency`: 95th percentile application response latency in seconds.
* **Resilience**: Features automatic fallback handling and imputation when Prometheus is booting up or endpoints have no traffic yet.

---

## 2. Isolation Forest Machine Learning Engine (`ml/model.py`)
* **Algorithm**: Unsupervised `sklearn.ensemble.IsolationForest` with `StandardScaler` preprocessing.
* **Hyperparameters**:
  * `n_estimators = 100`: High-density forest for robust decision boundaries.
  * `contamination = 0.03`: Calibrated for 3% expected anomaly probability in healthy operations.
  * `random_state = 42`: Deterministic and reproducible inference.
* **Dual-Output Scoring**:
  * **Classification**: `+1` (Normal, `is_anomaly: False`) or `-1` (Anomaly, `is_anomaly: True`).
  * **Normalized Anomaly Score**: Sigmoid transformation mapping raw decision functions smoothly to continuous severity values from `0.00` (healthy baseline) to `1.00` (critical anomaly).
* **Model Serialization**: Automatically saves and loads trained weights (`isolation_forest.joblib`) and feature scalers (`scaler.joblib`) via `joblib`.

---

## 3. Real-Time ML Anomaly Detection Service (`ml/detector_service.py`)
* **Continuous Daemon**: Polls Prometheus every 10 seconds, runs inference over current cloud telemetry, and publishes real-time Prometheus metrics on port `8000/metrics`:
  * `sentro_anomaly_detected`: Gauge (`0` = Healthy, `1` = Anomaly).
  * `sentro_anomaly_score`: Gauge (`0.00` to `1.00`).
  * `sentro_predictions_total`: Counter tracking total cycles evaluated.
  * `sentro_anomalies_detected_total`: Counter tracking total confirmed anomaly events.
* **REST Endpoints**:
  * `GET /health`: Health status and model readiness.
  * `GET /status`: Detailed JSON breakdown of the latest inference decision, timestamp, and raw metric snapshot.
  * `POST /evaluate`: Immediate on-demand evaluation trigger.

---

## 4. Automated Email Alerting & Notification Dispatcher (`ml/email_notifier.py`)
* **Real-Time SMTP Dispatcher**: Directly integrated into the detection loop. Automatically fires when the anomaly score breaches the configured threshold (`ALERT_SCORE_THRESHOLD=0.70`).
* **Cooldown & Anti-Spam Throttling**: Enforces a configurable cooldown window (`ALERT_COOLDOWN_SECONDS=300`) to prevent flooding an engineer's inbox during prolonged load spikes.
* **Auto-Recovery Notifications**: Detects when system metrics stabilize back below `0.50` and automatically delivers an "Issue Resolved — Workload Normalized" notification.
* **Environment-Driven Configuration**: Fully configurable via `.env` or container environment variables (`ALERT_EMAIL_ENABLED`, `SMTP_SERVER`, `SMTP_PORT`, `ALERT_EMAIL_SENDER`, `ALERT_EMAIL_PASSWORD`, `ALERT_EMAIL_RECIPIENT`). Documented in `.env.example`.

---

## 5. Interactive Chaos & Stress Simulator (`scripts/simulate_chaos.py`)
* Command-line tool to trigger artificial cloud disruptions and test ML detection accuracy:
  * `python scripts/simulate_chaos.py --cpu-spike --duration 30`: Spikes multi-threaded CPU load to 100%.
  * `python scripts/simulate_chaos.py --memory-leak --duration 30`: Progressively leaks ~300MB of RAM.
  * `python scripts/simulate_chaos.py --traffic-burst --duration 30`: Floods the Flask workload with concurrent HTTP requests.
  * `python scripts/simulate_chaos.py --normal --duration 30`: Generates calm baseline browsing traffic.
  * `python scripts/simulate_chaos.py --all --duration 45`: Triggers multi-vector combined anomaly.

---

## 5. Grafana Real-Time Anomaly Dashboard (`grafana/dashboards/sentro-overview.json`)
* **Live ML Anomaly Status**: Instant visual banner (`🟢 NORMAL WORKLOAD` in green, shifting to `🚨 ANOMALY DETECTED` in bright red).
* **Anomaly Severity Gauge**: Real-time gauge (0.00 – 1.00) with color-coded warning and critical thresholds.
* **Anomaly Score Timeline**: Multi-minute graph of the anomaly score plotted with a `0.70` critical alert threshold line, correlated directly above the CPU, RAM, and App Latency timelines.

---

## 6. Multi-Container Orchestration (`docker-compose.yml`)
* Orchestrates 5 microservices on the `sentro-network` bridge:
  1. `app`: Python Flask workload API (Port `5000:5000`)
  2. `node-exporter`: System hardware telemetry (Port `9100:9100`)
  3. `prometheus`: Centralized time-series database & scraper (Port `9090:9090`)
  4. `grafana`: Real-time visualization portal (Port `3000:3000`)
  5. `ml-detector`: Isolation Forest anomaly detection engine (Port `8000:8000`)

---

## 7. Cloud Infrastructure & CI/CD Pipeline
* **Terraform (`terraform/main.tf` & `terraform/outputs.tf`)**:
  * Opened port `8000` in the AWS Security Group for the ML Detector API.
  * Added `ml_detector_url` (`http://<EC2_PUBLIC_IP>:8000`) to Terraform outputs.
* **GitHub Actions (`.github/workflows/deploy.yml`)**:
  * Synchronizes `ml/` and `scripts/` directories to the EC2 host via SCP.
  * Executes automated zero-downtime deployment via `docker compose`.
