variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "demo"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "admin_ssh_cidr_blocks" {
  description = "Allowed CIDRs for SSH"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "llm_api_key" {
  description = "API key for AMD inference endpoint"
  type        = string
  sensitive   = true
  default     = "dummy-token-replay"
}

variable "llm_base_url" {
  description = "AMD Token Factory or vLLM base URL"
  type        = string
  default     = "https://notebooks.amd.com/v1"
}
