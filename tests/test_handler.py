import json

import jwt
import pytest

import handler as modulo
from repositorio import Cliente

CHAVE = "chave-de-teste-com-mais-de-32-caracteres-ok"
CPF = "52998224725"


@pytest.fixture
def banco(monkeypatch):
    """Substitui o PostgreSQL por um dublê que registra o documento consultado."""
    estado = {"cliente": Cliente("c-1", "Ana", CPF, True), "erro": None, "consultado": None}

    def buscar(digitos):
        estado["consultado"] = digitos
        if estado["erro"]:
            raise estado["erro"]
        return estado["cliente"]

    monkeypatch.setattr(modulo, "buscar_cliente", buscar)
    return estado


def chamar(corpo=None, query=None, bruto=None):
    evento = {
        "body": bruto if bruto is not None else (json.dumps(corpo) if corpo is not None else None),
        "queryStringParameters": query,
        "isBase64Encoded": False,
    }
    resposta = modulo.handler(evento, type("Contexto", (), {"aws_request_id": "req-1"})())
    return resposta["statusCode"], json.loads(resposta["body"]), resposta["headers"]


def test_cliente_ativo_recebe_token(banco):
    status, corpo, _ = chamar({"cpf": CPF})
    assert status == 200
    assert corpo["cliente"] == {"id": "c-1", "nome": "Ana"}
    assert jwt.decode(corpo["access_token"], CHAVE, algorithms=["HS256"])["tipo"] == "cliente"


def test_cpf_pontuado_e_normalizado_antes_da_consulta(banco):
    assert chamar({"cpf": "529.982.247-25"})[0] == 200
    assert banco["consultado"] == CPF


def test_aceita_cpf_na_query_string(banco):
    assert chamar(query={"cpf": CPF})[0] == 200


def test_cpf_invalido_nao_chega_ao_banco(banco):
    assert chamar({"cpf": "11111111111"})[0] == 400
    assert banco["consultado"] is None


def test_documento_ausente(banco):
    status, corpo, _ = chamar({})
    assert status == 400
    assert "cpf" in corpo["detail"].lower()


def test_corpo_que_nao_e_json(banco):
    assert chamar(bruto="isto não é json")[0] == 400


def test_cliente_inexistente(banco):
    banco["cliente"] = None
    assert chamar({"cpf": CPF})[:2] == (404, {"detail": "Cliente não encontrado"})


def test_cliente_inativo_nao_autentica(banco):
    banco["cliente"] = Cliente("c-1", "Ana", CPF, False)
    assert chamar({"cpf": CPF})[0] == 403


def test_banco_indisponivel_responde_503_sem_vazar_detalhe(banco):
    banco["erro"] = ConnectionError("host=10.0.128.42 password=segredo")
    status, corpo, _ = chamar({"cpf": CPF})
    assert status == 503
    assert "10.0.128" not in json.dumps(corpo) and "segredo" not in json.dumps(corpo)


def test_request_id_volta_no_cabecalho(banco):
    assert chamar({"cpf": CPF})[2]["x-request-id"] == "req-1"
