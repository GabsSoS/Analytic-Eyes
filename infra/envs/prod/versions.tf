terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Precisa bater com os outputs de infra/bootstrap (state_bucket_name /
  # lock_table_name). O bloco "backend" não aceita variáveis - se você
  # mudou os nomes no bootstrap, atualize aqui também.
  backend "s3" {
    bucket         = "analytic-eyes-tfstate"
    key            = "envs/prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "analytic-eyes-tfstate-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}
