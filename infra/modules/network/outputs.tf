output "vpc_id" {
  description = "ID da VPC criada para este ambiente."
  value       = aws_vpc.this.id
}

output "public_subnet_ids" {
  description = "IDs das 2 subnets públicas (>= 2 AZs), usadas pelo ALB (modules/alb)."
  value       = [aws_subnet.public.id, aws_subnet.public_b.id]
}

output "private_subnet_ids" {
  description = "IDs das subnets privadas (>= 2 AZs), usadas pelo db_subnet_group do RDS."
  value       = [aws_subnet.private_a.id, aws_subnet.private_b.id]
}

output "app_subnet_id" {
  description = "ID da subnet privada da EC2 (modules/compute) - sem IP público, sai via NAT Gateway."
  value       = aws_subnet.app.id
}

output "nat_eip_arn" {
  description = "ARN do EIP do NAT Gateway - usado por aws_shield_protection quando enable_shield_advanced = true (ver envs/prod/main.tf)."
  value       = aws_eip.nat.arn
}
