###############################################################################
# Modulo "secure-bucket" — il MATTONCINO STANDARD dell'azienda.
# Chi vuole un bucket non lo scrive da zero: usa questo modulo, che ci mette
# dentro d'ufficio cifratura, blocco accessi pubblici, versioning e i tag di
# governance obbligatori. Standardizzazione = un blocco approvato, riusabile.
###############################################################################

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

data "aws_caller_identity" "current" {}

locals {
  bucket_name = "${var.name}-${var.env}-${data.aws_caller_identity.current.account_id}"

  # I tag di governance: Owner e CostCenter sono OBBLIGATORI (li impone il modulo).
  tags = {
    Name       = local.bucket_name
    Env        = var.env
    Owner      = var.owner
    CostCenter = var.cost_center
    ManagedBy  = "Terraform"
    Module     = "secure-bucket"
  }
}

resource "aws_s3_bucket" "this" {
  bucket = local.bucket_name
  tags   = local.tags
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = "Enabled"
  }
}