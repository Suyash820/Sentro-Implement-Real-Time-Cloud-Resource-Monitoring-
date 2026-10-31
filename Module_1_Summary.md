# Module 1 Summary: Infrastructure & App Deployment

In **Module 1**, we successfully established the foundational infrastructure for the Sentro Real-Time Cloud Resource Monitoring project. Here is a detailed summary of everything we accomplished:

## 1. AWS Credentials & Security Access
- **SSH Key Pair:** We created a secure RSA key pair (`sentro-key.pem`) in the AWS EC2 dashboard. This key is used by GitHub Actions to securely connect to the server.
- **IAM User Access:** We generated programmatic access keys (Access Key ID and Secret Access Key) for a new IAM user with `AdministratorAccess` to allow Terraform to authenticate and build the infrastructure.

## 2. Infrastructure as Code (Terraform)
We used Terraform to fully automate the cloud provisioning process.
- **EC2 Instance Deployment:** We deployed an Ubuntu 22.04 server on AWS. We specifically updated the instance type from `t2.micro` to `t3.micro` to ensure compatibility with your AWS account's Free Tier limits.
- **Security Groups (Firewall):** We configured network rules to expose the required ports for the monitoring stack:
  - **Port 22:** Allowed SSH access for automated deployments.
  - **Port 5000:** Exposed the simulated Python/Flask application workload.
  - **Port 9100:** Exposed Node Exporter, which tracks the server's raw hardware metrics.

## 3. Automated CI/CD Pipeline (GitHub Actions)
We activated and debugged the continuous integration and continuous deployment (CI/CD) pipeline located in `.github/workflows/deploy.yml`.
- **Secrets Configuration:** We mapped your sensitive credentials (Docker Hub login, EC2 IP, and SSH Key) into GitHub Secrets securely.
- **Pipeline Workflow:** The automated pipeline now handles three major jobs every time code is pushed to the `main` branch:
  1. **Test & Build:** Validates the Python code and tests dependencies.
  2. **Publish (Docker):** Packages the application into a Docker container and pushes it to Docker Hub.
  3. **Deploy (EC2):** Automatically logs into the live AWS server, pulls the latest Docker image, and spins it up.

## 4. Key Metrics Exposed (Node Exporter)
As part of the infrastructure setup, we installed Node Exporter on the EC2 instance, which actively exposes hardware metrics in the Prometheus Exposition Format on port 9100. Here are the key metric categories it represents:
- **Node CPU Metrics (`node_cpu_seconds_total`)**: Tracks the exact number of seconds each CPU core spends doing different types of work (e.g., idle vs. user processes). Critical for detecting high server load.
  - *Example:* `node_cpu_seconds_total{cpu="0",mode="idle"} 3925.86` means CPU core 0 has spent 3925.86 seconds completely idle since the server booted.
- **Node Memory Metrics (`node_memory_*`)**: Reads from the Linux kernel to show total RAM and free RAM. Essential for preventing out-of-memory crashes.
  - *Example:* `node_memory_MemTotal_bytes 9.5840256e+08` means the server has ~958 MB of total RAM, which matches our `t3.micro` instance specification.
- **Network Metrics (`node_network_*`)**: Tracks every single byte of data coming in (`receive`) and going out (`transmit`) across network interfaces, allowing calculation of live bandwidth usage.
  - *Example:* `node_network_receive_bytes_total{device="ens5"} 2.17e+08` means the primary network interface (`ens5`) has received roughly 217 MB of data.
- **Disk I/O Metrics (`node_disk_*`)**: Tracks data read from and written to the server's storage disk, helping monitor storage performance constraints.
  - *Example:* `node_disk_written_bytes_total{device="nvme0n1"} 2.06e+09` means over 2 GB of data has been written to the `nvme0n1` AWS EBS volume.
- **Go Runtime Metrics (`go_*`)**: Because Node Exporter is written in the Go programming language, it exposes its own internal health metrics.
  - *Example:* `go_goroutines 7` means there are currently 7 Go routines (lightweight threads) running inside the Node Exporter process.

## 5. Current State & Next Steps
The foundational workload is completely live. The Python application is running on the EC2 server, and the server's hardware metrics are actively being exposed on port 9100. 

In **Module 2**, we will deploy Prometheus to start scraping and storing these live metrics!

## 6. Project Structure & File Explanations
Here is a breakdown of the repository structure and the exact purpose of every file used in Module 1:

- **`.github/workflows/deploy.yml`**: The CI/CD pipeline configuration file. It tells GitHub Actions exactly how to test the Python app, build the Docker container, and deploy it to the AWS EC2 instance.
- **`Dockerfile`**: Instructions for Docker on how to build the container image for the Python application, including copying the code and installing requirements.
- **`src/app.py`**: The core Python (Flask) application that acts as our simulated cloud workload.
- **`src/requirements.txt`**: A list of Python package dependencies (like Flask) needed to run `app.py`.
- **`tests/test_app.py`**: Automated unit tests written for the application. These are executed by GitHub Actions before every deployment to ensure the code isn't broken.
- **`terraform/main.tf`**: The primary Infrastructure as Code script. It defines the AWS EC2 instance, the AMI (Ubuntu operating system), and the Security Groups (firewall rules for ports 22, 5000, 9100).
- **`terraform/variables.tf`**: Defines configuration variables for Terraform (like the AWS region and the `t3.micro` instance type) making the setup flexible.
- **`terraform/outputs.tf`**: Configures Terraform to print out useful information (like the public IP address of the server) after the infrastructure is successfully built.
- **`terraform/user_data.sh`**: A shell script that automatically runs on the EC2 instance the very first time it boots up. It installs necessary base software (like Docker and Node Exporter) onto the server automatically.
