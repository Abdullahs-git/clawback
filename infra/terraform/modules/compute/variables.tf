variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "demo"
}

variable "subnet_id" {
  description = "Subnet ID where the compute instance will be launched"
  type        = string
}

variable "security_group_id" {
  description = "Security group ID attached to the compute instance"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "ami_id" {
  description = "Ubuntu 24.04 LTS AMI ID"
  type        = string
  default     = "ami-0c7217cdde317cfec" # Ubuntu 24.04 us-east-1 placeholder
}

variable "ssh_key_name" {
  description = "Optional EC2 SSH Key Pair name"
  type        = string
  default     = null
}

variable "llm_api_key" {
  description = "AMD inference endpoint API key passed securely into runtime .env"
  type        = string
  sensitive   = true
  default     = "dummy-token-replay"
}

variable "llm_base_url" {
  description = "AMD Token Factory or vLLM inference base URL"
  type        = string
  default     = "https://notebooks.amd.com/v1"
}
