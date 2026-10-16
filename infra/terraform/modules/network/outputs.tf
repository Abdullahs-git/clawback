output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.clawback_vpc.id
}

output "public_subnet_id" {
  description = "The ID of the public subnet"
  value       = aws_subnet.public_subnet.id
}

output "security_group_id" {
  description = "The ID of the web security group"
  value       = aws_security_group.clawback_sg.id
}
