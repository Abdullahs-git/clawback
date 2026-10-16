terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    template = {
      source  = "hashicorp/template"
      version = "~> 2.2"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "network" {
  source                = "../../modules/network"
  environment           = var.environment
  admin_ssh_cidr_blocks = var.admin_ssh_cidr_blocks
}

module "compute" {
  source            = "../../modules/compute"
  environment       = var.environment
  subnet_id         = module.network.public_subnet_id
  security_group_id = module.network.security_group_id
  instance_type     = var.instance_type
  llm_api_key       = var.llm_api_key
  llm_base_url      = var.llm_base_url
}
