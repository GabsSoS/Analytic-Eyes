output "state_bucket_name" {
  description = "Use isto em envs/prod/backend.tf (bucket)."
  value       = aws_s3_bucket.tfstate.id
}

output "lock_table_name" {
  description = "Use isto em envs/prod/backend.tf (dynamodb_table)."
  value       = aws_dynamodb_table.tfstate_lock.name
}
