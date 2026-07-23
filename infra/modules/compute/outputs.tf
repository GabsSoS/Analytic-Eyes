output "instance_id" {
  value = aws_instance.this.id
}

output "public_ip" {
  description = "Aponte o DNS (A record) do seu domínio para este IP."
  value       = aws_eip.this.public_ip
}
