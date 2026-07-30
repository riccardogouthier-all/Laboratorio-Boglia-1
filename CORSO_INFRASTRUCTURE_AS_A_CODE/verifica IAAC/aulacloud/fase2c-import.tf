# FASE 2c - da usare cosi': rinomina questo file in "fase2c-import.tf",
# sostituisci COGNOME col tuo, e lancia terraform plan.
# Il piano deve riportare:  Plan: 1 to import, ...

import {
  to = aws_s3_bucket.legacy
  id = "aulacloud-legacy-gouthier" # <- l'id del bucket che hai creato a mano
}

resource "aws_s3_bucket" "legacy" {
  bucket = "aulacloud-legacy-gouthier"

  tags = {
    Name      = "aulacloud-legacy-gouthier"
    Env       = "dev"
    ManagedBy = "Terraform"
  }
}
