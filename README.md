# Sentro: Real-Time Cloud Resource Monitoring 🚀

Welcome to the Sentro project repository! This project implements Real-Time Cloud Resource Monitoring using Prometheus, Grafana, and the Isolation Forest ML Algorithm.

Currently, we are in **Module 1: Infrastructure & App Deployment (Foundation)**. 

The foundational code (App, Dockerfile, Terraform, and CI/CD workflow) has been written. To complete Module 1, follow the step-by-step instructions below.

---

## 📋 Outstanding Tasks for Module 1

### Step 1: Create an SSH Key Pair in AWS
Before deploying the infrastructure, you need an SSH key pair to access the server later.
1. Log into the [AWS Management Console](https://aws.amazon.com/console/).
2. Navigate to the **EC2 Dashboard**.
3. Under **Network & Security** (left sidebar), click **Key Pairs**.
4. Click **Create key pair**.
5. Name the key pair exactly: `sentro-key`.
6. Select **RSA** and **.pem** format, then click **Create key pair**.
7. Securely save the downloaded `.pem` file on your computer.

### Step 2: Generate AWS Credentials
To allow Terraform to build your infrastructure, it needs programmatic access to your AWS account.
1. In the AWS Console, navigate to the **IAM Dashboard**.
2. Click **Users** -> **Create user**.
3. Name your user (e.g., `sentro-admin`) and click **Next**.
4. Choose **Attach policies directly**, search for `AdministratorAccess`, select it, and create the user.
5. Click on your newly created user, navigate to the **Security credentials** tab.
6. Under **Access keys**, click **Create access key**.
7. Choose **Command Line Interface (CLI)** and proceed to create the key.
8. Keep the screen open or temporarily copy your **Access Key ID** and **Secret Access Key**.

### Step 3: Deploy Infrastructure via Terraform
Now that you have your credentials, you will provision your AWS EC2 instance.
1. Open PowerShell on your computer.
2. Run the following command (replace the placeholder text with your actual keys from Step 2):
   ```powershell
   wsl -d Ubuntu -e bash -c "export AWS_ACCESS_KEY_ID='YOUR_ACCESS_KEY' && export AWS_SECRET_ACCESS_KEY='YOUR_SECRET_KEY' && cd '/mnt/d/projects all/Sentro/terraform' && terraform apply"
   ```
3. Terraform will display a plan. Type `yes` and hit Enter to confirm.
4. When finished, Terraform will output your new server's **Public IP Address**. Copy this down.

### Step 4: Configure GitHub Secrets for CI/CD
To automate your deployments, GitHub Actions needs access to Docker and your AWS server.
1. Create a free account on [Docker Hub](https://hub.docker.com/) if you don't have one.
2. Go to your GitHub repository on the web.
3. Click **Settings** -> **Secrets and variables** -> **Actions**.
4. Add the following **New repository secrets**:
   *   `DOCKER_USERNAME`: Your Docker Hub username.
   *   `DOCKER_PASSWORD`: Your Docker Hub password or access token.
   *   `EC2_HOST`: The Public IP address of your EC2 instance (from Step 3).
   *   `EC2_SSH_KEY`: The entire contents of the `sentro-key.pem` file you downloaded in Step 1.

### Step 5: Activate the CI/CD Pipeline
Right now, the deployment steps are disabled in our code to prevent errors. Let's activate them!
1. Open `.github/workflows/deploy.yml` in your editor.
2. Uncomment the `publish:` and `deploy:` jobs at the bottom of the file.
3. Commit and push the changes to GitHub:
   ```powershell
   git add .
   git commit -m "Activate CI/CD deployment jobs"
   git push origin main
   ```
4. Go to the **Actions** tab on your GitHub repo and watch your code automatically build and deploy to your server!

### Step 6: Verify Deployment (Review 1 Ready!)
Once the GitHub Action completes successfully, verify your deployment in a web browser:
*   **App Workload:** Visit `http://<YOUR_EC2_PUBLIC_IP>:5000`. You should see a success message.
*   **Node Exporter:** Visit `http://<YOUR_EC2_PUBLIC_IP>:9100/metrics`. You should see a wall of text (hardware metrics).

If both work, Module 1 is completely finished! 🎉
