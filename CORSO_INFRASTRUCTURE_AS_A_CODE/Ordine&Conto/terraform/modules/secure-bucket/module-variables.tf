variable "name" {
  description = "Nome logico del bucket (verrà suffissato con env e account-id)"
  type        = string
}

variable "env" {
  description = "Ambiente: dev o prod"
  type        = string
  validation {
    condition     = contains(["dev", "prod"], var.env)
    error_message = "env deve essere 'dev' o 'prod'."
  }
}

variable "owner" {
  description = "Team proprietario (diventa il tag Owner, obbligatorio)"
  type        = string
  validation {
    condition     = length(var.owner) > 0
    error_message = "owner non può essere vuoto: è il tag di governance Owner."
  }
}

variable "cost_center" {
  description = "Centro di costo (diventa il tag CostCenter, obbligatorio per il FinOps)"
  type        = string
  validation {
    condition     = can(regex("^CC-[0-9]+$", var.cost_center))
    error_message = "cost_center deve avere il formato CC-<numero> (es. CC-1001)."
  }
}