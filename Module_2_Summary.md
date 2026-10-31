# Module 2 Summary: Centralized Observability (Prometheus & Grafana)

In **Module 2**, we built the real-time observability and telemetry stack for the Sentro platform, connecting the Python application, host telemetry, Prometheus metrics scraper, and Grafana interactive dashboards.

---

## 1. Application-Level Metric Instrumentation
* **Prometheus Integration**: Integrated `prometheus-flask-exporter` into `src/app.py` and `src/requirements.txt`.
* **Exposed Endpoints**:
  * `GET /metrics` on port `5000`: Automatically exposes live application metrics in Prometheus exposition format.
  * Tracks request throughput (`flask_http_request_total`), HTTP status codes (`2xx`, `4xx`, `5xx`), and request latency histograms (`flask_http_request_duration_seconds_bucket`).
  * Emits application metadata (`sentro_app_info{version="1.0.0"}`).
* **Automated Unit Testing**: Extended `tests/test_app.py` with `test_metrics(client)` verifying that `/metrics` responds with `200 OK` and valid telemetry.

---

## 2. Centralized Metrics Engine (Prometheus)
* **Configuration File (`prometheus/prometheus.yml`)**:
  * Scrapes `app:5000/metrics` every 5 seconds for application-level data.
  * Scrapes `node-exporter:9100/metrics` every 5 seconds for host hardware data (CPU, RAM, Disk, Network).
  * Self-scrapes `localhost:9090` for internal Prometheus storage engine health.

---

## 3. Automated Visual Analytics (Grafana)
* **Zero-Manual-Setup Provisioning**:
  * `grafana/provisioning/datasources/prometheus_datasource.yml`: Automatically registers the Prometheus server (`http://prometheus:9090`) as the default datasource on container boot.
  * `grafana/provisioning/dashboards/dashboard_provider.yml`: Automatically scans and registers custom dashboard JSONs.
* **Pre-Built Dashboard (`grafana/dashboards/sentro-overview.json`)**:
  * **Current CPU Utilization Gauge**: Color-coded thresholds (Green < 65%, Yellow < 85%, Red >= 85%).
  * **Current Memory Utilization Gauge**: Real-time percentage of RAM consumed.
  * **CPU History Timeline**: Multi-instance CPU % trends.
  * **Memory Breakdown Timeline**: Used RAM vs. Available RAM in bytes.
  * **Network Traffic Timeline**: Real-time throughput (MB/s in/out).
  * **App Throughput**: Request rate (req/sec) categorized by HTTP status code.
  * **Response Latency**: P95 and P99 latency percentiles.

---

## 4. Multi-Container Orchestration (`docker-compose.yml`)
* Seamlessly links 4 containers on a dedicated bridge network (`sentro-network`):
  1. `app`: Containerized Flask workload (Port `5000:5000`).
  2. `node-exporter`: Hardware telemetry collector (Port `9100:9100`).
  3. `prometheus`: Time-series database & scraper (Port `9090:9090`) with persistent volume `prometheus-data`.
  4. `grafana`: Web visualization portal (Port `3000:3000`) with persistent volume `grafana-data` and default admin credentials (`admin`/`admin`).

---

## 5. Infrastructure as Code (Terraform) Updates
* **Firewall Security Groups (`terraform/main.tf`)**:
  * Opened port `9090` for Prometheus.
  * Opened port `3000` for Grafana.
* **Outputs (`terraform/outputs.tf`)**:
  * `app_url`: `http://<EC2_IP>:5000`
  * `prometheus_url`: `http://<EC2_IP>:9090`
  * `grafana_url`: `http://<EC2_IP>:3000`
* **Automated EC2 Bootstrap (`terraform/user_data.sh`)**:
  * Added `docker-compose-plugin` so `docker compose` is pre-installed on the server.

---

## 6. Continuous Deployment (CI/CD Pipeline)
* Updated `.github/workflows/deploy.yml`:
  * Transfers `docker-compose.yml`, `prometheus/`, and `grafana/` configs to the EC2 host via SCP (`appleboy/scp-action`).
  * Executes `sudo -E docker compose pull && sudo -E docker compose up -d --remove-orphans` over SSH.
