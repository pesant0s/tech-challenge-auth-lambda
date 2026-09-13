terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }

  # Bucket e região vêm de -backend-config, pois dependem da conta de quem executa.
  backend "s3" {
    key          = "auth-lambda/terraform.tfstate"
    encrypt      = true
    use_lockfile = true
  }
}

provider "aws" {
  region  = var.regiao
  profile = var.perfil_aws

  default_tags {
    tags = {
      Project     = "tech-challenge"
      Fase        = "03"
      Repositorio = "tech-challenge-auth-lambda"
      ManagedBy   = "terraform"
    }
  }
}
