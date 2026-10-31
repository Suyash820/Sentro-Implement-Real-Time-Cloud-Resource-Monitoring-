# Sentro: Real-Time Cloud Resource Monitoring - Project Documentation

## 1. Project Overview
**Sentro** is a Real-Time Cloud Resource Monitoring solution designed to aggregate, analyze, and visualize hardware and application metrics. The system leverages **Prometheus** for metrics collection, **Grafana** for visualization, and the **Isolation Forest Machine Learning Algorithm** for anomaly detection in cloud workloads.

## 2. Architecture & Tech Stack
The project is built on a modern DevOps and Cloud-Native foundation:
- **Cloud Provider:** AWS (Amazon Web Services)
- **Infrastructure as Code (IaC):** Terraform
- **Containerization:** Docker
- **CI/CD:** GitHub Actions
- **Monitoring & Visualization:** Prometheus, Grafana, Node Exporter
- **Application Workload:** Python (Flask)

## 3. Module 1: Infrastructure & App Deployment (Foundation)
The foundational module establishes the infrastructure required to host the monitoring stack.

### 3.1 Components
- **App:** A Python-based workload simulator that exposes metrics.
- **Dockerfile:** Containerizes the application for consistent deployment.
- **Terraform:** Automates the provisioning of an AWS EC2 instance, security groups, and networking configurations.
- **CI/CD Pipeline (`deploy.yml`):** Automates the testing, building, and deployment process upon every push to the main branch.

### 3.2 Infrastructure Configuration (Terraform)
The Terraform configuration (`main.tf`, `variables.tf`) handles:
- **Provider setup:** AWS region `us-east-1`
- **Instance setup:** Provisioning an Ubuntu 22.04 AMI on a `t3.micro` EC2 instance.
- **Security Groups:** 
  - Port `22` (SSH Access)
  - Port `5000` (Flask Application)
  - Port `9100` (Node Exporter for hardware metrics)

### 3.3 CI/CD Workflow (GitHub Actions)
The deployment pipeline consists of the following automated jobs:
1. **Build-and-Test:** Sets up Python, installs dependencies from `src/requirements.txt`, and runs tests using `pytest`.
2. **Publish:** Logs into Docker Hub, builds the Docker image from the source code, and pushes the tagged image (`sentro-app:latest`) to the Docker registry.
3. **Deploy:** Uses SSH to connect to the AWS EC2 instance, pulls the latest Docker image, stops any running containers, and starts the updated container on port 5000.

## 4. Setup Instructions & Prerequisites
To deploy this project, the following prerequisites are required:
- AWS Account with an IAM User configured with `AdministratorAccess`.
- An AWS RSA `.pem` SSH key pair named `sentro-key`.
- A Docker Hub account.
- GitHub Repository Secrets configured:
  - `DOCKER_USERNAME`
  - `DOCKER_PASSWORD`
  - `EC2_HOST` (Public IP of the EC2 instance)
  - `EC2_SSH_KEY` (Contents of the `.pem` file)

## 5. Verification
Once the pipeline deploys successfully, the health and status of the application can be verified by accessing the EC2 instance's Public IP over the exposed ports:
- **App Interface:** `http://<EC2_PUBLIC_IP>:5000`
- **Metrics Endpoint:** `http://<EC2_PUBLIC_IP>:9100/metrics`

## 6. Future Modules
Subsequent modules will expand on this foundation by integrating the Prometheus time-series database to scrape the exposed metrics, configuring Grafana dashboards for real-time visualization, and deploying the Isolation Forest ML model to intelligently flag anomalous resource consumption.
