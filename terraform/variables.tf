variable "aws_region" {
  description = "The AWS region to deploy to"
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  default     = "t2.micro"
}

variable "key_name" {
  description = "Name of the SSH key pair to use for EC2 instances"
  type        = string
  default     = "sentro-key" # Update this to your actual key pair name in AWS
}
