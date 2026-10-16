# Network module for Clawback demo deployment
# Configures VPC, public subnet, internet gateway, and security group for ports 80, 443, and 22.

resource "aws_vpc" "clawback_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "clawback-${var.environment}-vpc"
    Environment = var.environment
    Project     = "clawback"
  }
}

resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.clawback_vpc.id

  tags = {
    Name        = "clawback-${var.environment}-igw"
    Environment = var.environment
  }
}

resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.clawback_vpc.id
  cidr_block              = var.subnet_cidr
  map_public_ip_on_launch = true

  tags = {
    Name        = "clawback-${var.environment}-public-subnet"
    Environment = var.environment
  }
}

resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.clawback_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }

  tags = {
    Name        = "clawback-${var.environment}-public-rt"
    Environment = var.environment
  }
}

resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_security_group" "clawback_sg" {
  name        = "clawback-${var.environment}-sg"
  description = "Security group for Clawback web application and API"
  vpc_id      = aws_vpc.clawback_vpc.id

  # Inbound HTTP
  ingress {
    description = "HTTP ingress"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Inbound HTTPS
  ingress {
    description = "HTTPS ingress"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Inbound SSH from allowlist
  ingress {
    description = "SSH ingress from configured allowlist"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.admin_ssh_cidr_blocks
  }

  # Outbound egress
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "clawback-${var.environment}-sg"
    Environment = var.environment
  }
}
