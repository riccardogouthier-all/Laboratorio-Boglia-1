variable "nome" {
  description = "Nome logico del bucket (verra' completato con env e suffisso)"
  type        = string
}

variable "env" {
  description = "Ambiente: dev o prod"
  type        = string

  validation {
    condition     = contains(["dev", "prod"], var.env)
    error_message = "L'ambiente puo' essere solo dev o prod."
  }
}

variable "cost_center" {
  description = "Centro di costo, formato CC-<numero>"
  type        = string

  validation {
    condition     = can(regex("^CC-[0-9]+$", var.cost_center))
    error_message = "Il cost_center deve avere il formato CC-<numero>, es. CC-77."
  }
}

variable "suffisso" {
  description = "Suffisso univoco (la tua matricola)"
  type        = string
}
