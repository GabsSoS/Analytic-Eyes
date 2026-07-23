output "bucket_name" {
  value = aws_s3_bucket.pipelines.id
}

output "bucket_arn" {
  value = aws_s3_bucket.pipelines.arn
}
