# RFC-003 · Estratégia de autenticação do cliente

| | |
|---|---|
| **Status** | Aceita |
| **Data** | 2026-09-09 |
| **Decisões derivadas** | ADR-010 (segredo por variável de ambiente), ADR-011 (validação de CPF duplicada), ADR-012 (rota do dono da função) |

## Contexto

O enunciado pede rotas sensíveis protegidas por autenticação via CPF e uma função serverless
que valide o CPF, confira se o cliente existe e está ativo e devolva um JWT. A API já
autenticava funcionários com JWT próprio (`POST /auth/token`) desde a Fase 01.

O cliente não tem senha: o CPF é a única informação que ele apresenta.

## Critérios

1. Seguir o fluxo do enunciado: função serverless, consulta ao banco, JWT.
2. Um único mecanismo de validação de token dentro da API, para funcionário e cliente.
3. Nenhum serviço extra pago ou difícil de reproduzir em outra conta.
4. Cliente autenticado enxerga apenas as próprias ordens de serviço.
5. Cadastro desativado perde o acesso sem esperar o token expirar.

## Opções

**A · Lambda emite JWT HS256 e a API valida.** A Lambda consulta o RDS e assina com a
`SECRET_KEY` do Secrets Manager. A API valida com a mesma chave e separa os públicos pelo
claim `tipo`.

**B · Amazon Cognito com autenticação customizada.** CPF como nome de usuário, Lambdas de
desafio do Cognito e tokens RS256 validados por um JWT authorizer no API Gateway.

**C · Lambda authorizer no gateway, sem token.** O cliente enviaria o CPF em toda requisição, e
o authorizer consultaria o banco para liberar ou negar a chamada.

**D · Autenticação dentro da API.** Uma rota `/auth/cpf` no próprio FastAPI.

| Critério | A | B | C | D |
|---|---|---|---|---|
| Segue o fluxo do enunciado | sim | parcial: quem emite o token é o Cognito | não devolve JWT | não é serverless |
| Validação única na API | sim | não: RS256 para cliente, HS256 para funcionário | não | sim |
| Peças novas | uma Lambda | user pool, três Lambdas de desafio e sincronia de cadastros | uma Lambda | nenhuma |
| Consultas ao banco | uma por login | uma por login | uma por requisição | uma por login |

## Proposta

**Opção A.** É o fluxo do enunciado com o menor número de peças, e a API mantém um único
mecanismo de validação: o mesmo `jwt.decode`, com o claim `tipo` decidindo o que cada token
acessa.

Cada requisição de cliente ainda confere, na API, se o cadastro continua ativo. Desativar um
cliente corta o acesso na hora, sem lista de revogação.

## Consequências

- **Segredo compartilhado.** A mesma `SECRET_KEY` chega à Lambda, como variável de ambiente, e à
  API, como Secret do Kubernetes, ambas a partir do Secrets Manager. Trocar a chave exige
  republicar as duas.
- **O gateway não valida o token.** O JWT authorizer do API Gateway HTTP trabalha com chaves
  assimétricas publicadas por JWKS; com HS256, a validação fica na API, e toda rota nova precisa
  declarar a sua dependência de autenticação.
- **CPF não é segredo.** Quem conhece o CPF de um cliente obtém um token dele. O desafio adota
  esse modelo, e o alcance fica restrito às ordens de serviço daquele cliente. Hoje mitigam o
  risco o token de 60 minutos, o throttling do gateway e o CPF mascarado nos logs.

## Evolução

- Throttling específico para `POST /auth/cpf`, contra enumeração de CPFs.
- Segundo fator por código enviado ao e-mail ou telefone do cadastro.
- RS256 com chaves publicadas por JWKS, se mais serviços passarem a validar tokens; isso também
  permite validar no gateway.
