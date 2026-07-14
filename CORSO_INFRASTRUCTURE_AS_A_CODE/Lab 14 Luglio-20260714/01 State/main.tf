# =============================================================
#  L08 · LAB A — la base di partenza (è il main.tf di lunedì)
#  Serve per: state list/show, drift, import.
#  NON fate destroy: questa cartella ci serve per tutta la giornata.
# =============================================================

#aggiungo una riga per avere delle modifiche da fare

terraform {
  required_version = ">= 1.11" # per il locking nativo S3 del LAB B

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

resource "aws_s3_bucket" "dati" {
  bucket = "its-iac-riccardo-01" # <<<<<< il VOSTRO nome (globale!)

  tags = {
    Corso = "ACA"
    UF    = "IaC"
    Owner = "riccardo"
  }
}

output "nome_bucket" {
  value = aws_s3_bucket.dati.id
}

# --- COSA FARE (LAB A step 1) --------------------------------
#  terraform init
#  terraform apply                              -> yes
#  terraform state list                         -> cosa c'è nell'inventario
#  terraform state show aws_s3_bucket.dati      -> tutti i dettagli
#  poi aprite terraform.tfstate in VS Code:
#     cercate  "serial"   (contatore di modifiche)
#              "lineage"  (carta d'identità dello state)
#              "arn"      (quello che ha risposto AWS)
#
# --- LAB A step 2: il DRIFT ----------------------------------
#  1) in console S3, sul vostro bucket: cambiate il tag Corso in "pippo"
#     e aggiungetene uno nuovo (es. urgente = si)
#  2) terraform plan               -> cosa propone? tiene o cancella?
#  3) terraform plan -refresh-only -> "drift detection" pura:
#                                     dice cosa è cambiato SENZA correggerlo
