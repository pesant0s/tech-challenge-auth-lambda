# Rede e segredo do tech-challenge-infra-db; API Gateway do tech-challenge-infra-k8s.

data "aws_ssm_parameter" "subnets_privadas" { name = "/tech-challenge/network/subnet_ids_privadas" }
data "aws_ssm_parameter" "sg_cliente_db" { name = "/tech-challenge/network/sg_cliente_db_id" }
data "aws_ssm_parameter" "secret_nome" { name = "/tech-challenge/database/secret_nome" }
data "aws_ssm_parameter" "apigateway_id" { name = "/tech-challenge/apigateway/id" }
data "aws_ssm_parameter" "apigateway_execucao_arn" { name = "/tech-challenge/apigateway/execucao_arn" }
data "aws_ssm_parameter" "apigateway_endpoint" { name = "/tech-challenge/apigateway/endpoint" }

# Lido no apply e passado como variável de ambiente: sem NAT, a Lambda não alcança o Secrets Manager (ADR-010).
data "aws_secretsmanager_secret_version" "app" {
  secret_id = data.aws_ssm_parameter.secret_nome.value
}

locals {
  segredo          = jsondecode(data.aws_secretsmanager_secret_version.app.secret_string)
  subnets_privadas = split(",", data.aws_ssm_parameter.subnets_privadas.value)
  nome_funcao      = "${var.prefixo}-auth"
}
