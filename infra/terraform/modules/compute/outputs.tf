output "instance_id" {
  description = "EC2 Instance ID"
  value       = aws_instance.clawback_vm.id
}

output "public_ip" {
  description = "Public IP address of the Clawback VM"
  value       = aws_instance.clawback_vm.public_ip
}
