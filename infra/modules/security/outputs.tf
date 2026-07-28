output "ec2_security_group_id" {
  description = "ID do security group da EC2 (SSH restrito, HTTP/HTTPS)."
  value       = aws_security_group.ec2.id
}

output "rds_security_group_id" {
  description = "ID do security group do RDS (só aceita tráfego do SG da EC2)."
  value       = aws_security_group.rds.id
}
