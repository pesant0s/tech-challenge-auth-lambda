output "nome_funcao" {
  value = aws_lambda_function.auth.function_name
}

output "url_autenticacao" {
  value = "${data.aws_ssm_parameter.apigateway_endpoint.insecure_value}/auth/cpf"
}

output "grupo_de_logs" {
  value = aws_cloudwatch_log_group.funcao.name
}
