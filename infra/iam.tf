data "aws_iam_policy_document" "confianca" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "funcao" {
  name               = "${local.nome_funcao}-execucao"
  assume_role_policy = data.aws_iam_policy_document.confianca.json
}

resource "aws_iam_role_policy_attachment" "vpc" {
  role       = aws_iam_role.funcao.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}
