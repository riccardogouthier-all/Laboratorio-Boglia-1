output "bucket_name" {
  description = "Nome del bucket creato dal modulo"
  value       = aws_s3_bucket.this.bucket
}

output "bucket_arn" {
  description = "ARN del bucket creato dal modulo"
  value       = aws_s3_bucket.this.arn
}
