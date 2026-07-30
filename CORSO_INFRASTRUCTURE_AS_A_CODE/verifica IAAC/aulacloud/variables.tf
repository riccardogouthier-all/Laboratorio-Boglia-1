variable "matricola" {
  description = "La tua sigla univoca (cognome in minuscolo, senza spazi). Serve a non collidere coi compagni."
  type        = string
}

variable "env" {
  description = "Ambiente: dev oppure prod"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "prod"], var.env)
    error_message = "L'ambiente puo' essere solo dev o prod."
  }
}

variable "cost_center" {
  description = "Centro di costo, formato CC-<numero>"
  type        = string
  default     = "CC-77"

  validation {
    condition     = can(regex("^CC-[0-9]+$", var.cost_center))
    error_message = "Il cost_center deve avere il formato CC-<numero>, es. CC-77."
  }
}
