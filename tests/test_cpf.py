import pytest

from cpf import DocumentoInvalido, mascarar, normalizar


@pytest.mark.parametrize("valor", ["529.982.247-25", "52998224725", " 529.982.247-25 "])
def test_cpf_valido_com_ou_sem_pontuacao(valor):
    assert normalizar(valor) == "52998224725"


def test_cnpj_valido():
    assert normalizar("11.222.333/0001-81") == "11222333000181"


@pytest.mark.parametrize("valor, mensagem", [
    ("52998224726", "verificadores"),
    ("11111111111", "verificadores"),
    ("11222333000182", "verificadores"),
    ("123", "11 dígitos"),
    ("529.982.24A-25", "válido"),
    ("", "válido"),
    (None, "válido"),
])
def test_documento_invalido(valor, mensagem):
    with pytest.raises(DocumentoInvalido, match=mensagem):
        normalizar(valor)


@pytest.mark.parametrize("digitos", ["52998224725", "11222333000181"])
def test_mascara_nao_expoe_o_documento(digitos):
    assert digitos not in mascarar(digitos)
