variable "regiao" {
  description = "Região AWS"
  type        = string
  default     = "us-east-1"
}

variable "perfil_aws" {
  description = "Perfil local do AWS CLI; vazio no CI, que usa OIDC"
  type        = string
  default     = null
}

variable "prefixo" {
  description = "Prefixo dos nomes de recurso"
  type        = string
  default     = "tech-challenge"
}

variable "caminho_pacote" {
  description = "Zip gerado por make build"
  type        = string
  default     = "../dist/lambda.zip"
}

variable "memoria_mb" {
  description = "Memória da função; na Lambda, a CPU acompanha a memória"
  type        = number
  default     = 512
}

variable "timeout_segundos" {
  description = "Timeout da função"
  type        = number
  default     = 10
}
