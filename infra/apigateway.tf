# Rota explícita vence a coringa do infra-k8s: /auth/cpf chega aqui, o resto vai ao EKS (ADR-012).

resource "aws_apigatewayv2_integration" "auth" {
  api_id                 = data.aws_ssm_parameter.apigateway_id.value
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.auth.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 15000
}

resource "aws_apigatewayv2_route" "auth" {
  for_each = toset(["POST /auth/cpf", "GET /auth/cpf"])

  api_id    = data.aws_ssm_parameter.apigateway_id.value
  route_key = each.value
  target    = "integrations/${aws_apigatewayv2_integration.auth.id}"
}

resource "aws_lambda_permission" "apigateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.auth.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${data.aws_ssm_parameter.apigateway_execucao_arn.value}/*/*"
}
