##############################################################
# VERIFICA FINALE IaC - PROVA PRATICA
# Commessa "AulaCloud": il portale iscrizioni ai corsi
# passa sotto Terraform. Completa i TODO e segui le fasi
# indicate sul documento di laboratorio.
##############################################################

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# --- gia' pronto: non serve modificarlo -----------------------
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

data "aws_vpc" "default" {
  default = true
}
# --------------------------------------------------------------

# ==============================================================
# TODO 1 (FASE 1) - la mappa delle taglie.
#   Completa la mappa "taglie": dev -> t3.micro, prod -> t3.small
#   e poi usala per valorizzare instance_type piu' sotto.
# ==============================================================
locals {
  taglie = {
    dev  = "t3.micro"
    prod = "t3.small"
  }

  common_tags = {
    Project    = "AulaCloud"
    Env        = var.env
    Owner      = var.matricola
    CostCenter = var.cost_center
    ManagedBy  = "Terraform"
  }
}

resource "aws_security_group" "portale" {
  name        = "aulacloud-portale-${var.matricola}"
  description = "Security group del portale AulaCloud"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH da EC2 Instance Connect"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP pubblico"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Tutto in uscita"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "aulacloud-sg-${var.matricola}"
  })
}

resource "aws_instance" "portale" {
  ami           = data.aws_ami.al2023.id
  instance_type = local.taglie[var.env]

  vpc_security_group_ids = [aws_security_group.portale.id]

  user_data_replace_on_change = true
  user_data                   = <<-EOT
    #!/bin/bash
    dnf install -y httpd
    systemctl enable --now httpd
    echo "<h1>AulaCloud ${var.env} - ${var.matricola}</h1>" > /var/www/html/index.html
  EOT

  tags = merge(local.common_tags, {
    Name = "aulacloud-portale-${var.matricola}"
  })
}

module "bucket" {
  for_each = toset(["documenti", "backup"])

  source      = "./modules/secure-bucket"
  nome        = "aulacloud-${each.key}"
  env         = var.env
  cost_center = var.cost_center
  suffisso    = var.matricola
}

output "bucket_per_ruolo" {
  description = "Mappa ruolo => nome bucket"
  value       = { for k, v in module.bucket : k => v.bucket_name }
}

# ==============================================================
# TODO 4 (FASE 1) - l'output con l'indirizzo del portale.
#   Deve restituire una stringa tipo http://54.1.2.3
# ==============================================================
output "url_portale" {
  description = "Indirizzo del portale AulaCloud"
  value       = "http://${aws_instance.portale.public_ip}"
}

output "sg_id" {
  description = "ID del security group del portale"
  value       = aws_security_group.portale.id
}
