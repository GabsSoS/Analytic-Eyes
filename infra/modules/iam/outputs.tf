output "instance_profile_name" {
  description = "Nome do instance profile IAM anexado à EC2 (modules/compute)."
  value       = aws_iam_instance_profile.ec2.name
}

output "role_arn" {
  description = "ARN da role IAM usada pela EC2."
  value       = aws_iam_role.ec2.arn
}
