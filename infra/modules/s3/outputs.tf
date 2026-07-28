output "bucket_name" {
  description = "Nome do bucket S3 de pipelines - vira AWS_STORAGE_BUCKET_NAME no .env da aplicação."
  value       = aws_s3_bucket.pipelines.id
}

output "bucket_arn" {
  description = "ARN do bucket S3 de pipelines, usado nas policies IAM (modules/iam)."
  value       = aws_s3_bucket.pipelines.arn
}
