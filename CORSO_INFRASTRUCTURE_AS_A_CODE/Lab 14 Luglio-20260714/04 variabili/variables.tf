# =============================================================
#  L08 · LAB C — variabili (= i Parameters di CloudFormation)
# =============================================================

variable "bucket_name" {
  description = "Nome del bucket dati (globale su tutto AWS)"
  type        = string
  # niente default: se non lo passate, Terraform ve lo chiede
}

variable "environment" {
  description = "Ambiente di deploy"
  type        = string
  default     = "dev"

  # È l'AllowedValues di CFN, ma con il messaggio d'errore scritto da voi.
  # E l'errore arriva AL PLAN, prima di toccare qualsiasi cosa su AWS.
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment può valere solo 'dev' o 'prod'."
  }
}

variable "owner" {
  description = "Chi è il proprietario (finisce nei tag)"
  type        = string
  default     = "studente"
}
