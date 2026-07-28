output "vpc_id" {
  description = "ID da VPC criada para este ambiente."
  value       = aws_vpc.this.id
}

output "public_subnet_id" {
  description = "ID da subnet pública, usada pela EC2 (modules/compute)."
  value       = aws_subnet.public.id
}

output "private_subnet_ids" {
  description = "IDs das subnets privadas (>= 2 AZs), usadas pelo db_subnet_group do RDS."
  value       = [aws_subnet.private_a.id, aws_subnet.private_b.id]
}
