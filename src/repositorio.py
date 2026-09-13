import os
import ssl
from dataclasses import dataclass

import pg8000.dbapi


@dataclass(frozen=True)
class Cliente:
    id: str
    nome: str
    cpf_cnpj: str
    ativo: bool


def buscar_cliente(digitos: str) -> Cliente | None:
    """Busca o cliente pelo CPF/CNPJ já normalizado, via pg8000 (ADR-009)."""
    # TLS exigido pelo RDS; o certificado não é verificado porque a conexão não sai da VPC.
    contexto = ssl.create_default_context()
    contexto.check_hostname = False
    contexto.verify_mode = ssl.CERT_NONE
    conexao = pg8000.dbapi.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        ssl_context=contexto,
        timeout=5,
    )
    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT id, nome, cpf_cnpj, ativo FROM clientes WHERE cpf_cnpj = %s", (digitos,))
        linha = cursor.fetchone()
    finally:
        conexao.close()
    return Cliente(str(linha[0]), linha[1], linha[2], bool(linha[3])) if linha else None
