resource "aws_cloudwatch_log_group" "funcao" {
  name              = "/aws/lambda/${local.nome_funcao}"
  retention_in_days = 7
}

resource "aws_lambda_function" "auth" {
  function_name    = local.nome_funcao
  description      = "Autentica o cliente por CPF/CNPJ e emite o JWT"
  role             = aws_iam_role.funcao.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = var.caminho_pacote
  source_code_hash = filebase64sha256(var.caminho_pacote)
  memory_size      = var.memoria_mb
  timeout          = var.timeout_segundos

  # Subnet privada para alcançar o RDS; cliente-db é o grupo que o banco aceita.
  vpc_config {
    subnet_ids         = local.subnets_privadas
    security_group_ids = [data.aws_ssm_parameter.sg_cliente_db.value]
  }

  environment {
    variables = {
      DB_HOST                     = local.segredo["DB_HOST"]
      DB_PORT                     = local.segredo["DB_PORT"]
      DB_NAME                     = local.segredo["DB_NAME"]
      DB_USER                     = local.segredo["DB_USER"]
      DB_PASSWORD                 = local.segredo["DB_PASSWORD"]
      SECRET_KEY                  = local.segredo["SECRET_KEY"]
      ALGORITHM                   = "HS256"
      ACCESS_TOKEN_EXPIRE_MINUTES = "60"
      LOG_LEVEL                   = "INFO"
    }
  }

  depends_on = [aws_iam_role_policy_attachment.vpc, aws_cloudwatch_log_group.funcao]

  tags = { Name = local.nome_funcao }
}
