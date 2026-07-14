# =============================================================
#  L08 · LAB D — il modulo ROOT (chi chiama)
#
#  Il modulo "bucket" è scritto una volta e usato DUE volte.
#  = i nested stack di CloudFormation (L04), ma senza S3 di mezzo.
#
#  DOPO aver aggiunto un blocco module{}:  terraform init  (di nuovo!)
#  Altrimenti: "Error: Module not installed".
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

variable "owner" {
  type    = string
  default = "cambiami"
}

locals {
  common_tags = {
    Corso     = "ACA"
    UF        = "IaC"
    Owner     = var.owner
    ManagedBy = "Terraform"
  }
}

# --- Prima chiamata: il bucket che avete già ------------------
module "bucket_dati" {
  source = "./modules/bucket"

  bucket_name = "its-iac-CAMBIAMI-01" # <<<<<< lo STESSO di prima
  tags        = local.common_tags
}

# --- Seconda chiamata: stesso mattoncino, altro bucket --------
module "bucket_log" {
  source = "./modules/bucket"

  bucket_name = "its-iac-CAMBIAMI-log-01" # <<<<<< nuovo
  tags        = merge(local.common_tags, { Scopo = "log" })
}

# --- LA TRAPPOLA (step 4 del LAB) -----------------------------
#  Il bucket è lo stesso, ma il suo INDIRIZZO nel codice è cambiato:
#
#     PRIMA:  aws_s3_bucket.dati
#     DOPO:   module.bucket_dati.aws_s3_bucket.this
#
#  Per lo state sono DUE risorse diverse -> il plan propone
#  "1 to destroy, 1 to add".  Voi NON volete distruggere niente.
#
#  LA CURA: il blocco moved{} qui sotto. Dichiarativo, e si VEDE nel plan.
#  (Equivalente imperativo, vecchia scuola:
#     terraform state mv aws_s3_bucket.dati module.bucket_dati.aws_s3_bucket.this)
moved {
  from = aws_s3_bucket.dati
  to   = module.bucket_dati.aws_s3_bucket.this
}

output "arn_dati" {
  value = module.bucket_dati.arn # <- così si legge un output di un modulo
}

output "arn_log" {
  value = module.bucket_log.arn
}

# --- COSA DEVE DIRE IL PLAN ----------------------------------
#  terraform init          (obbligatorio dopo aver aggiunto i module)
#  terraform plan
#     -> "1 to move, 1 to add, 0 to change, 0 to destroy"
#     -> ZERO distruzioni. La risorsa non viene toccata:
#        cambia solo la sua etichetta nell'inventario.
#
#  In azienda, il giorno che rifattorizzate in moduli un'infrastruttura
#  di produzione, è questo blocco che evita di distruggere il database.
