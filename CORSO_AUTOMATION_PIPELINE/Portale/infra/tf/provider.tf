provider "aws" {
  region = "eu-south-1"

  access_key                  = var.aws_endpoint == "" ? null : "test"
  secret_key                  = var.aws_endpoint == "" ? null : "test"
  skip_credentials_validation = var.aws_endpoint != ""
  skip_metadata_api_check     = var.aws_endpoint != ""
  skip_requesting_account_id  = var.aws_endpoint != ""
  s3_use_path_style           = var.aws_endpoint != ""

  endpoints {
    s3       = var.aws_endpoint
    dynamodb = var.aws_endpoint
    kms      = var.aws_endpoint
    sts      = var.aws_endpoint
  }
}