output "instance_id" {
  description = "ID da instância EC2."
  value       = aws_instance.this.id
}

output "public_ip" {
  description = "Aponte o DNS (A record) do seu domínio para este IP."
  value       = aws_eip.this.public_ip
}
