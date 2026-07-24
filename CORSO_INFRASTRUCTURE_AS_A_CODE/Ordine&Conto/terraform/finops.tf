###############################################################################
# FinOps — questa risorsa serve a VEDERE il costo dal piano (infracost).
# NON si applica: si stima PRIMA di spendere. Cambia `instance_type` e ri-stima
# per vedere l'impatto sul conto (right-sizing).
###############################################################################

variable "instance_type" {
  description = "Tipo di istanza — il right-sizing parte da qui"
  type        = string
  default     = "t3.micro"
}

variable "ami" {
  description = "AMI (per la sola STIMA non serve che sia reale/applicabile)"
  type        = string
  default     = "ami-0c7217cdde317cfec"
}

resource "aws_instance" "app" {
  ami           = var.ami
  instance_type = var.instance_type

  tags = {
    Name       = "acme-app"
    Env        = "dev"
    Owner      = "team-piattaforma"
    CostCenter = "CC-1001"
  }
}