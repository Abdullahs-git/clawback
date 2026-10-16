output "public_ip" {
  description = "Public IP address of the deployed Clawback server"
  value       = module.compute.public_ip
}

output "web_url" {
  description = "URL of the Clawback Web Application"
  value       = "http://${module.compute.public_ip}"
}

output "api_health_url" {
  description = "URL of the Clawback API health endpoint"
  value       = "http://${module.compute.public_ip}:8000/health"
}
