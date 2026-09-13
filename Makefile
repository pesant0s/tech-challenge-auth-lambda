.DEFAULT_GOAL := help
.PHONY: help conta gateway venv test cov build clean init plan apply destroy implantar logs invoke

AWS_REGION ?= us-east-1
FUNCAO     := tech-challenge-auth
VENV       := .venv
PYTHON     ?= python3
export AWS_REGION

CONTA  = $(shell aws sts get-caller-identity --query Account --output text)
BUCKET = tech-challenge-tfstate-$(CONTA)
# Delimitador `|` no sed: num Makefile, `#` abriria um comentário.
GITHUB_OWNER ?= $(shell git config --get remote.origin.url 2>/dev/null | sed -E 's|^.*github\.com[:/]([^/]+)/.*$$|\1|')

help: ## Lista os alvos
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

conta: ## Mostra em qual conta AWS os comandos vão atuar
	@test -n "$$AWS_PROFILE$$AWS_ACCESS_KEY_ID" || { echo "Defina AWS_PROFILE com a conta que vai receber a função."; exit 1; }
	@echo "Conta AWS: $(CONTA) · perfil: $${AWS_PROFILE:-credenciais do ambiente} · região: $(AWS_REGION)"

gateway: conta
	@aws ssm get-parameter --name /tech-challenge/apigateway/id >/dev/null 2>&1 || { echo "O API Gateway não existe nesta conta: rode 'make up' no tech-challenge-infra-k8s."; exit 1; }

venv: ## Cria o ambiente virtual com as dependências
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install -q -r requirements-dev.txt

test: ## Roda os testes, sem AWS nem banco
	@test -x $(VENV)/bin/python || $(MAKE) --no-print-directory venv
	$(VENV)/bin/python -m pytest -q

cov: ## Testes com cobertura
	@test -x $(VENV)/bin/python || $(MAKE) --no-print-directory venv
	$(VENV)/bin/python -m pytest --cov=src --cov-report=term-missing --cov-report=xml

# Os .dist-info ficam no zip: o scramp, usado pelo pg8000, lê a própria versão por eles.
build: clean ## Monta dist/lambda.zip
	@mkdir -p build dist
	@cp src/*.py build/
	@$(PYTHON) -m pip install -q -r requirements.txt -t build/ --upgrade
	@find build -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@cd build && zip -qr ../dist/lambda.zip .
	@echo "✓ dist/lambda.zip — $$(du -h dist/lambda.zip | cut -f1)"

clean: ## Remove artefatos de build
	@rm -rf build dist

init: conta ## Inicializa o Terraform com o estado desta conta
	cd infra && terraform init -backend-config="bucket=$(BUCKET)" -backend-config="region=$(AWS_REGION)"

plan: conta build ## Mostra o que será alterado
	@test -d infra/.terraform || $(MAKE) --no-print-directory init
	cd infra && terraform plan

apply: conta gateway build ## Publica a função e a rota no API Gateway
	@test -d infra/.terraform || $(MAKE) --no-print-directory init
	cd infra && terraform apply

# O destroy também empacota: o Terraform lê o hash do zip mesmo para destruir.
destroy: conta build ## Remove a função e a rota
	@test -d infra/.terraform || $(MAKE) --no-print-directory init
	cd infra && terraform destroy

implantar: ## Aciona o pipeline de publicação na main
	@test -n "$(GITHUB_OWNER)" || { echo "Dono do repositório desconhecido: rode com GITHUB_OWNER=seu-usuario."; exit 1; }
	gh workflow run ci-cd.yml --ref main --repo $(GITHUB_OWNER)/tech-challenge-auth-lambda

logs: conta ## Acompanha os logs da função
	aws logs tail /aws/lambda/$(FUNCAO) --follow

invoke: conta ## Testa a autenticação de ponta a ponta (CPF=...)
	@curl -s -X POST "$$(aws ssm get-parameter --name /tech-challenge/apigateway/endpoint --query Parameter.Value --output text)/auth/cpf" -H 'content-type: application/json' -d '{"cpf":"$(or $(CPF),529.982.247-25)"}' | python3 -m json.tool
