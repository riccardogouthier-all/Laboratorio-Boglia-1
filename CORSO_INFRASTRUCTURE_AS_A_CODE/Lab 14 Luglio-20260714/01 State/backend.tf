# =============================================================
#  L08 · LAB B step 2 — spostare lo state su S3
#
#  Questo file va aggiunto nella cartella del LAB (01-state/),
#  quella dove avete già bucket + import.
#
#  Poi:   terraform init -migrate-state
#         -> "Do you want to copy existing state to the new backend?"  -> yes
#
#  Se rispondete NO, il backend parte VUOTO e Terraform si dimentica
#  di tutto (vedi slide "ho perso lo state"). Rispondete yes.
# =============================================================

terraform {
  backend "s3" {
    bucket = "its-tfstate-riccardo-01" # <<<<<< il bucket creato col bootstrap
    key    = "lab/terraform.tfstate"   # il "percorso" dentro il bucket
    region = "us-east-1"

    # IL LOCK, senza DynamoDB (Terraform >= 1.11).
    # S3 crea un file .tflock accanto allo state usando le scritture condizionali.
    use_lockfile = true

    # State cifrato a riposo
    encrypt = true

    # --- LEGACY (lo troverete in tutti i repo aziendali) ---
    # Prima che S3 sapesse fare il lock da solo, serviva una tabella DynamoDB:
    #   dynamodb_table = "terraform-locks"
    # Oggi è DEPRECATO. Sappiatelo leggere, ma non scrivetelo più.
  }
}

# --- ATTENZIONE ----------------------------------------------
#  Dentro il blocco backend NON si possono usare variabili.
#  Il backend viene inizializzato PRIMA che Terraform valuti le variabili.
#  In azienda si aggira con:  terraform init -backend-config=prod.hcl
