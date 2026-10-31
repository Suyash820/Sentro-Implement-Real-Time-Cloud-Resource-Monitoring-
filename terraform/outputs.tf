output "instance_public_ip" {
  description = "The public IP address of the EC2 instance"
  value       = aws_instance.sentro_server.public_ip
}

output "instance_public_dns" {
  description = "The public DNS of the EC2 instance"
  value       = aws_instance.sentro_server.public_dns
}

output "app_url" {
  description = "URL of the deployed application"
  value       = "http://${aws_instance.sentro_server.public_ip}:5000"
}

output "prometheus_url" {
  description = "URL of the Prometheus monitoring server"
  value       = "http://${aws_instance.sentro_server.public_ip}:9090"
}

output "grafana_url" {
  description = "URL of the Grafana dashboard"
  value       = "http://${aws_instance.sentro_server.public_ip}:3000"
}

output "ml_detector_url" {
  description = "URL of the ML Anomaly Detection Service"
  value       = "http://${aws_instance.sentro_server.public_ip}:8000"
}
