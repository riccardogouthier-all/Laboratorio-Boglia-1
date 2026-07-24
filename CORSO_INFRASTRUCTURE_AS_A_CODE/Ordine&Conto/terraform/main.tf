###############################################################################
# ACME — governance con i moduli.
# Nessuno scrive più un bucket "a mano": si usa il MODULO standard
# "secure-bucket", che impone hardening + tag. Qui lo istanziamo per due
# ambienti (dev e prod): stesso mattoncino, due risultati.
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

module "logs_dev" {
  source      = "./modules/secure-bucket"
  name        = "acme-logs"
  env         = "dev"
  owner       = "team-piattaforma"
  cost_center = "CC-1001"
}

module "logs_prod" {
  source      = "./modules/secure-bucket"
  name        = "acme-logs"
  env         = "prod"
  owner       = "team-piattaforma"
  cost_center = "CC-1001"
}

output "dev_bucket" {
  value = module.logs_dev.bucket_id
}

output "prod_bucket" {
  value = module.logs_prod.bucket_id
}