# 📋 Sentro — Project Roadmap & Task Checklist (TODO.md)

---

## ✅ Module 1: Infrastructure & App Deployment (Completed)
- [x] Python Flask simulated cloud workload (`src/app.py`)
- [x] Automated unit test suite (`tests/test_app.py`)
- [x] Dockerfile containerization
- [x] Terraform AWS EC2 infrastructure & security groups
- [x] Node Exporter hardware metrics exposition (`:9100`)
- [x] GitHub Actions automated CI/CD pipeline

---

## ✅ Module 2: Centralized Observability Stack (Completed)
- [x] Application-level metric instrumentation via `prometheus-flask-exporter`
- [x] Prometheus server configuration & automated scrape targets (`prometheus/prometheus.yml`)
- [x] Automated Grafana provisioning (Datasource & Sentro Overview Dashboard)
- [x] Unified Docker Compose orchestration (`docker-compose.yml`)
- [x] Terraform Security Group updates (Ports `9090` and `3000`)
- [x] Continuous deployment pipeline updates

---

## 🚀 Module 3: Intelligent Anomaly Detection (Isolation Forest)

> **Module 3 Objective:** Implement an unsupervised Machine Learning service using the **Isolation Forest** algorithm that continuously ingests Prometheus metrics, detects anomalous resource consumption (CPU spikes, memory leaks, traffic floods), and visualizes anomaly scores in Grafana.

---

### Phase 1: Metric Ingestion Pipeline & Dependencies
- [x] **1.1 Set up ML Dependencies**
  - File: `ml/requirements.txt`
  - Add: `scikit-learn>=1.3.0`, `pandas>=2.1.0`, `numpy>=1.24.0`, `requests>=2.31.0`, `prometheus-client>=0.19.0`, `joblib>=1.3.0`
- [x] **1.2 Build Prometheus Telemetry Ingestion Client**
  - File: `ml/collector.py`
  - Query Prometheus HTTP API (`/api/v1/query_range` and `/api/v1/query`):
    - CPU utilization %
    - Memory utilization %
    - Network I/O rate (Rx/Tx bytes/sec)
    - App request throughput & P95 latency
  - Format metrics into structured Pandas DataFrames with timestamp indexing

---

### Phase 2: Isolation Forest Model Architecture & Training
- [x] **2.1 Build ML Model Class (`ml/model.py`)**
  - Preprocessing pipeline with `StandardScaler` to normalize multi-dimensional metrics
  - Initialize `sklearn.ensemble.IsolationForest`:
    - `n_estimators=100`, `contamination=0.05` (5% expected anomalies), `random_state=42`
  - Training method: Fit model on normal baseline cloud telemetry
  - Inference method:
    - Output binary label: `+1` (Normal) vs. `-1` (Anomaly)
    - Output continuous anomaly score: Normalized from `0.00` (safe) to `1.00` (critical anomaly)
  - Model persistence: Save/load trained weights via `joblib`
- [x] **2.2 Baseline Dataset Generator & Model Training Script**
  - File: `ml/train.py`
  - Generate baseline normal workload data and train initial model artifact (`ml/models/isolation_forest.joblib`)

---

### Phase 3: Real-Time ML Anomaly Detection Service
- [x] **3.1 Build Continuous Daemon Service (`ml/detector_service.py`)**
  - Runs in a continuous loop (polls Prometheus every 10–15 seconds)
  - Fetches the latest metric window, runs inference via the Isolation Forest model
  - Exposes detected anomaly metrics on port `8000/metrics`:
    - `sentro_anomaly_detected` (Gauge: `0` for Normal, `1` for Anomaly)
    - `sentro_anomaly_score` (Gauge: `0.00` to `1.00`)
    - `sentro_predictions_total` (Counter: total evaluated samples)
- [x] **3.2 Update Prometheus Configuration**
  - File: `prometheus/prometheus.yml`
  - Add `ml-detector` scrape target (`ml-detector:8000/metrics`)

---

### Phase 4: Chaos & Stress Testing Simulator
- [x] **4.1 Build Interactive Workload / Chaos Simulator**
  - File: `scripts/simulate_chaos.py`
  - Command-line tool to trigger artificial anomalies on demand:
    - `--cpu-spike`: Multi-core CPU intensive computation loop
    - `--memory-leak`: Progressive RAM allocation to simulate uncollected memory
    - `--traffic-burst`: Concurrent HTTP flood against the Flask workload (`/`)
    - `--normal`: Emulates baseline healthy user traffic

---

### Phase 5: Grafana Anomaly Visualizations
- [x] **5.1 Update Sentro Overview Dashboard (`grafana/dashboards/sentro-overview.json`)**
  - Add **Anomaly Status Panel**:
    - Displays bold status: `🟢 NORMAL WORKLOAD` or `🔴 ANOMALY DETECTED`
  - Add **Isolation Forest Anomaly Score Timeline**:
    - Plotted anomaly score (0.0 – 1.0) with red threshold line at `0.70`
    - Correlated directly alongside CPU/RAM spikes for visual root-cause analysis

---

### Phase 6: Docker Integration & Automated Testing
- [x] **6.1 Containerize ML Service**
  - File: `ml/Dockerfile`
  - Builds lightweight Python image running `detector_service.py`
- [x] **6.2 Update `docker-compose.yml`**
  - Add `ml-detector` service on port `8000:8000` attached to `sentro-network`
- [x] **6.3 Automated Unit Tests for ML Pipeline**
  - File: `tests/` (`test_collector.py`, `test_model.py`, `test_service.py`, `test_chaos.py`)
  - Unit tests for metric collector, model training, anomaly prediction, and chaos testing (15 passed)
