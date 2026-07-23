terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Bootstrap roda com state local de propósito: ele cria o próprio backend
  # (bucket S3 + tabela DynamoDB) que os demais módulos (envs/prod) vão usar
  # como remote state. Aplicar isso uma única vez, por um dev.
}

provider "aws" {
  region = var.aws_region
}
