# =============================================================
#  L08 · LAB C — parametrizzare il lab
#
#  Obiettivo: stesso risultato su AWS, ma senza "CAMBIAMI" nel codice.
#  Il plan DEVE uscire pulito (o al massimo cambiare i tag):
#  se propone di RICREARE il bucket, avete cambiato il nome.
# =============================================================

terraform {
  required_version = ">= 1.11"

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

# --- locals: calcolati DENTRO, non passati da fuori ----------
locals {
  # interpolazione "${...}" = il !Sub di CloudFormation
  prefix = "its-${var.environment}"

  # IL pattern più usato al mondo: tag uguali su tutte le risorse,
  # scritti una volta sola. Vi salva a un audit sui costi.
  common_tags = {
    Corso       = "ACA"
    UF          = "IaC"
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "Terraform"
  }
}

resource "aws_s3_bucket" "dati" {
  bucket = var.bucket_name # <- niente più nome hardcoded
  tags   = local.common_tags
}

output "nome_bucket" {
  value = aws_s3_bucket.dati.id
}

# --- BONUS per chi finisce prima: for_each -------------------
#  UNA risorsa scritta una volta, creata N volte.
#  In CloudFormation questo NON si poteva fare (servivano N risorse
#  scritte a mano, o uno script che generava il template).
#
#  Per provarlo: togliete i commenti (in VS Code: selezionate e Ctrl+ù / Cmd+/)
#  poi terraform plan -> vedrete DUE bucket in più, con indirizzi:
#     aws_s3_bucket.zone["log"]
#     aws_s3_bucket.zone["backup"]
#  Ricordatevi di distruggerli a fine giornata.
#
# resource "aws_s3_bucket" "zone" {
#   for_each = toset(["log", "backup"])
#
#   bucket = "${local.prefix}-${each.key}-${var.owner}"
#   tags   = local.common_tags
# }
#
# output "zone_create" {
#   description = "Gli indirizzi generati dal for_each"
#   value       = [for b in aws_s3_bucket.zone : b.id]
# }

# --- PROVA CATTIVA (step 5) ----------------------------------
#  terraform plan -var="environment=collaudo"
#  -> deve fallire con IL VOSTRO messaggio: "environment può valere solo 'dev' o 'prod'."
