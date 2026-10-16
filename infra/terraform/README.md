# Clawback Infrastructure: Terraform Deployment

This directory contains Infrastructure-as-Code (Terraform >= 1.6) configurations for provisioning a private deployment of Clawback on cloud infrastructure.

## Architecture & Modules

```
infra/terraform/
|-- modules/
|   |-- network/          VPC, public subnet, internet gateway, and security groups
|   |-- compute/          Hardened VM with encrypted EBS and cloud-init Docker Compose runner
`-- envs/
    `-- demo/             Single-instance demo environment configuration
```

## Security & Well-Architected Standards

- **Zero Em Dashes**: All resource names and descriptions use hyphens only per AWS naming conventions.
- **Least Privilege Ingress**: Ingress is restricted to ports 80, 443, and SSH (restricted via `admin_ssh_cidr_blocks`).
- **Secret Isolation**: AMD API tokens are passed at apply time and injected into `/opt/clawback/.env` with strict `0600` permissions. Secrets are never checked into git.
- **Encrypted Storage**: EBS root volumes are encrypted using AWS-managed KMS keys.

## Deployment Instructions

```bash
cd infra/terraform/envs/demo

# 1. Initialize Terraform
terraform init

# 2. Review Execution Plan
terraform plan -var-file=terraform.tfvars

# 3. Apply Infrastructure (Manual approval required)
terraform apply -var-file=terraform.tfvars
```

If deploying outside Terraform, Clawback can be deployed directly via `docker compose up -d` on any host with Docker installed.
