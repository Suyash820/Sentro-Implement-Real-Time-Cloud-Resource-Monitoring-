# 📋 Sentro — Module 2 Implementation Plan (TODO.md)

> **Module 2 Objective:** Implement the centralized **Real-Time Observability Stack** by instrumenting the application, collecting metrics via **Prometheus**, and visualizing system & application performance on interactive **Grafana** dashboards.

---

## 🛠️ Step-by-Step Task Checklist

### Phase 1: Application Instrumentation (Flask Metrics)
- [x] **1.1 Add Prometheus Library to Dependencies**
  - File: `src/requirements.txt`
  - Add `prometheus-flask-exporter==0.23.1`
- [x] **1.2 Instrument Flask Application (`src/app.py`)**
  - Integrate `PrometheusMetrics(app)` to expose default HTTP metrics:
    - Request counts by endpoint and HTTP status (`2xx`, `4xx`, `5xx`)
    - Request latency histograms
  - Expose the `/metrics` endpoint on port `5000`
- [x] **1.3 Add Unit Test for Metrics Endpoint**
  - File: `tests/test_app.py`
  - Add `test_metrics_endpoint()` verifying `200 OK` and presence of metric headers

---

### Phase 2: Prometheus Setup & Scraping Configuration
- [x] **2.1 Create Prometheus Configuration (`prometheus/prometheus.yml`)**
  - Configure global scrape interval (e.g., `10s`)
  - Configure scrape jobs:
    - `flask-app`: Scrapes `app:5000/metrics`
    - `node-exporter`: Scrapes `node-exporter:9100/metrics`
    - `prometheus`: Self-monitoring on `localhost:9090`

---

### Phase 3: Grafana Automated Provisioning & Dashboards
- [x] **3.1 Automate Prometheus Data Source Provisioning**
  - File: `grafana/provisioning/datasources/prometheus_datasource.yml`
  - Auto-configure Prometheus (`http://prometheus:9090`) as the default data source upon boot
- [x] **3.2 Automate Dashboard Provider**
  - File: `grafana/provisioning/dashboards/dashboard_provider.yml`
  - Tell Grafana to automatically load dashboard JSON files from `grafana/dashboards/`
- [x] **3.3 Create Sentro Overview Dashboard (`grafana/dashboards/sentro-overview.json`)**
  - **CPU Utilization Panel**: Gauge + Time-series graph showing `% CPU used`
  - **Memory Utilization Panel**: Used RAM vs. Free RAM
  - **Network Throughput Panel**: Transmit & Receive rates (MB/s)
  - **Application Traffic Panel**: Total HTTP Requests/sec grouped by status code
  - **Application Latency Panel**: P95 & P99 response time in milliseconds

---

### Phase 4: Multi-Container Orchestration (`docker-compose.yml`)
- [x] **4.1 Create Unified `docker-compose.yml`**
  - Service 1: `app` (Flask API on port `5000`)
  - Service 2: `node-exporter` (Hardware telemetry on port `9100`)
  - Service 3: `prometheus` (`prom/prometheus:v2.48.0` on port `9090`)
  - Service 4: `grafana` (`grafana/grafana:10.2.0` on port `3000`)
  - Unified Docker bridge network `sentro-network` ensuring instant DNS resolution between containers

---

### Phase 5: Infrastructure as Code (Terraform Updates)
- [x] **5.1 Update Security Group (`terraform/main.tf`)**
  - Ingress port `9090` (Prometheus Web UI)
  - Ingress port `3000` (Grafana Dashboard)
- [x] **5.2 Update Outputs (`terraform/outputs.tf`)**
  - Add output `prometheus_url` (`http://<EC2_PUBLIC_IP>:9090`)
  - Add output `grafana_url` (`http://<EC2_PUBLIC_IP>:3000`)

---

### Phase 6: CI/CD Pipeline Updates
- [x] **6.1 Update GitHub Actions Workflow (`.github/workflows/deploy.yml`)**
  - Update deployment job to copy docker compose configs and execute `docker compose up -d`
- [x] **6.2 Commit Baseline Updates**
  - Commit untracked documentation files and `t3.micro` instance type adjustment

---

## 🎯 Verification & Deliverables Upon Completion
1. **Flask Metrics Test**: `curl http://localhost:5000/metrics` returns live Prometheus metrics.
2. **Prometheus Targets Status**: `http://<IP>:9090/targets` shows all endpoints in state `UP` (Green).
3. **Grafana Real-time View**: `http://<IP>:3000` opens immediately with pre-loaded Sentro dashboards.
