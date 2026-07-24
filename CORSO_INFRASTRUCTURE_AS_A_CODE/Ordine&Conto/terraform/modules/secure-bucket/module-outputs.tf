output "bucket_id" {
  description = "ID (nome) del bucket creato"
  value       = aws_s3_bucket.this.id
}

output "bucket_arn" {
  description = "ARN del bucket, da passare ad altri moduli"
  value       = aws_s3_bucket.this.arn
}