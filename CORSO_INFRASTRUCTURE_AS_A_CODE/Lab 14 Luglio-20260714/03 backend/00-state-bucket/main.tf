# =============================================================
#  L08 · LAB B step 1 — il progetto "BOOTSTRAP"
#
#  Crea il bucket che ospiterà lo state degli ALTRI progetti.
#  L'uovo e la gallina: questo progetto NON può usare come backend
#  il bucket che sta creando -> il SUO state resta in locale. Ed è giusto così.
#
#  Si lancia UNA volta e non si tocca più.
# =============================================================

terraform {
  required_version = ">= 1.11"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  # NIENTE backend qui: state locale. È il bootstrap.
}

provider "aws" {
  region = "us-east-1"
}

# --- Il bucket dello state -----------------------------------
resource "aws_s3_bucket" "tfstate" {
  bucket = "its-tfstate-riccardo-01" # <<<<<< il VOSTRO nome (globale!)

  tags = {
    Corso      = "ACA"
    Scopo      = "terraform-state"
    NonToccare = "sul-serio"
  }
}

# --- Versioning: IL PARACADUTE -------------------------------
#  Se lo state si corrompe o qualcuno fa danni, si torna alla versione di ieri.
#  Costa zero. Mettetelo SEMPRE sui bucket di state.
resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  versioning_configuration {
    status = "Enabled"
  }
}

# --- Cifratura a riposo --------------------------------------
#  Lo state contiene attributi sensibili (password, chiavi): va cifrato.
resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# --- Blocco degli accessi pubblici ---------------------------
#  Uno state pubblico su internet = regalare la mappa della vostra infrastruttura.
resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "state_bucket" {
  description = "Copiatelo: vi serve nel blocco backend del progetto vero"
  value       = aws_s3_bucket.tfstate.id
}

# --- ATTENZIONE AL DESTROY -----------------------------------
#  A fine giornata: PRIMA destroy nel progetto del lab,
#  POI destroy qui. Se cancellate prima il bucket dello state,
#  perdete lo state e restate con risorse orfane su AWS.
#  (E il bucket va svuotato: col versioning attivo servirà
#   "Empty" da console, oppure force_destroy = true.)
