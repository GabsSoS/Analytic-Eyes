output "instance_id" {
  description = "ID da instância EC2 (use com `aws ssm start-session --target` para acesso administrativo)."
  value       = aws_instance.this.id
}

output "private_ip" {
  description = "IP privado da instância, usado pelo target group do ALB (modules/alb)."
  value       = aws_instance.this.private_ip
}
