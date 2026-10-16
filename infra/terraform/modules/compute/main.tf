# Compute module for Clawback
# Deploys a single hardened VM running Docker Compose via cloud-init.

data "template_file" "cloud_init" {
  template = file("${path.module}/cloud-init.yaml")
  vars = {
    llm_base_url = var.llm_base_url
    llm_api_key  = var.llm_api_key
  }
}

resource "aws_instance" "clawback_vm" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [var.security_group_id]
  associate_public_ip_address = true
  key_name                    = var.ssh_key_name
  user_data                   = data.template_file.cloud_init.rendered

  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  tags = {
    Name        = "clawback-${var.environment}-vm"
    Environment = var.environment
    Project     = "clawback"
  }
}
