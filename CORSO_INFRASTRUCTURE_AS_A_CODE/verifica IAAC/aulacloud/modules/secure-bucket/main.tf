# Modulo gia' pronto: NON va modificato.
# Impone lo standard aziendale su ogni bucket: cifratura, niente
# accessi pubblici, versioning acceso in produzione, tag di costo.

locals {
  bucket_name = "${var.nome}-${var.env}-${var.suffisso}"

  tags = {
    Name       = local.bucket_name
    Env        = var.env
    CostCenter = var.cost_center
    ManagedBy  = "Terraform"
  }
}

resource "aws_s3_bucket" "this" {
  bucket = local.bucket_name
  tags   = local.tags
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = var.env == "prod" ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
