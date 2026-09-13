import jwt
import pytest

from emissor import emitir

CHAVE = "chave-de-teste-com-mais-de-32-caracteres-ok"


def _token(**kwargs):
    return emitir(**{"cliente_id": "c-1", "cpf_cnpj": "52998224725", "nome": "Ana", "secret_key": CHAVE, **kwargs})


def test_token_carrega_identidade_e_tipo_cliente():
    payload = jwt.decode(_token()[0], CHAVE, algorithms=["HS256"])
    assert (payload["sub"], payload["tipo"], payload["cpf_cnpj"], payload["nome"]) == \
        ("c-1", "cliente", "52998224725", "Ana")


def test_expiracao_respeita_o_parametro():
    token, expira_em = _token(expiracao_minutos=30)
    payload = jwt.decode(token, CHAVE, algorithms=["HS256"])
    assert expira_em == payload["exp"] - payload["iat"] == 1800


def test_assinatura_de_outra_chave_e_rejeitada():
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(_token()[0], "outra-chave-completamente-diferente-aqui", algorithms=["HS256"])


def test_token_expirado_e_rejeitado():
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(_token(expiracao_minutos=-1)[0], CHAVE, algorithms=["HS256"])
