# =============================================================
#  MODULO "bucket" — gli OUTPUT (la spina)
#  L'unico modo che ha il chiamante di leggere qualcosa da dentro.
#  Dal root si usano così:  module.bucket_dati.arn
# =============================================================

output "id" {
  description = "Nome/ID del bucket"
  value       = aws_s3_bucket.this.id
}

output "arn" {
  description = "ARN del bucket"
  value       = aws_s3_bucket.this.arn
}
