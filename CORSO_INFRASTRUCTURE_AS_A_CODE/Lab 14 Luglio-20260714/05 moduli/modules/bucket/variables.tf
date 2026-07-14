# =============================================================
#  MODULO "bucket" — gli INPUT (la presa)
#  Sono gli unici valori che il chiamante può passare.
#  = i Parameters di un nested stack CloudFormation.
# =============================================================

variable "bucket_name" {
  description = "Nome del bucket (globale su tutto AWS)"
  type        = string
}

variable "tags" {
  description = "Tag da applicare al bucket"
  type        = map(string)
  default     = {}
}

# COMPITO FACOLTATIVO (dalla slide finale):
# aggiungete una variabile bool "versioning" (default false) e, nel main.tf
# del modulo, la risorsa aws_s3_bucket_versioning creata solo se è true.
# Suggerimento: count = var.versioning ? 1 : 0
