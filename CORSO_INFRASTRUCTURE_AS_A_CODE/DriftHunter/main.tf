###############################################################################
# DriftHunter — lo stack che oggi difenderemo dal DRIFT.
#
# STATE LOCALE (è un lab sul TUO portatile, come L07/L08): nessun backend
# remoto, così il plan gira subito e vedi il drift senza impalcature.
# Due risorse: un Security Group "web" (il bersaglio del drift, facile da
# toccare in console) e un bucket S3 (per l'esercizio "leggi il piano").
###############################################################################

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

data "aws_caller_identity" "current" {}
data "aws_vpc" "default" {
  default = true
}

locals {
  common_tags = {
    Project = "DriftHunter"
    Env     = "dev"
    Owner   = "team-piattaforma"
  }
}

# --- Il BERSAGLIO del drift: un Security Group "web" -------------------------
# In console gli aggiungerai a mano una regola (es. RDP 3389): il `plan` la
# smaschererà perché non è qui nel codice.
resource "aws_security_group" "web" {
  name        = "drifthunter-web"
  description = "DriftHunter web SG - gestito da Terraform"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTP dal mondo"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "tutto in uscita"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, { Name = "drifthunter-web" })
}

# --- Il bucket per l'esercizio "leggi il piano" ------------------------------
# Cambiare il NOME di questo bucket forza un -/+ (destroy + create): perdita dati.
resource "aws_s3_bucket" "data" {
  bucket = "drifthunter-data-${data.aws_caller_identity.current.account_id}"
  tags   = local.common_tags
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket = aws_s3_bucket.data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id

  versioning_configuration {
    status = "Enabled"
  }
}

output "web_sg_id" {
  description = "ID del Security Group da toccare in console"
  value       = aws_security_group.web.id
}

output "bucket_name" {
  value = aws_s3_bucket.data.bucket
}
