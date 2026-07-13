terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}
provider "aws" { region = "us-east-1" }

resource "aws_s3_bucket" "dati" {
  bucket = "its-iac-riccardo-107"
  tags   = { Corso = "ACA", Owner = "riccardo" }
}

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]
  filter { 
    name = "name" 
    values = ["al2023-ami-*-x86_64"] 
    }
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.al2023.id    # ← niente più AMI hardcoded!
  instance_type = "t3.micro"    # t3 = Nitro. AL2023 NON gira su t2 (Xen)
  key_name      = "vockey"
  tags          = { Name = "tf-web" }
}
