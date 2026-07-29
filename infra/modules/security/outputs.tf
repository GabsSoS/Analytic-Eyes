output "ec2_security_group_id" {
  description = "ID do security group da EC2 (só aceita tráfego do ALB)."
  value       = aws_security_group.ec2.id
}

output "rds_security_group_id" {
  description = "ID do security group do RDS (só aceita tráfego do SG da EC2)."
  value       = aws_security_group.rds.id
}

output "alb_security_group_id" {
  description = "ID do security group do ALB (HTTP/HTTPS restritos a app_allowed_cidrs)."
  value       = aws_security_group.alb.id
}
