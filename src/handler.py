"""Autenticação por CPF: valida o documento, consulta o cliente e emite o JWT."""
import base64
import json
import logging
import os
import sys
from datetime import datetime, timezone

from cpf import DocumentoInvalido, mascarar, normalizar
from emissor import emitir
from repositorio import buscar_cliente

_ATRIBUTOS_PADRAO = frozenset((
    "args", "asctime", "created", "exc_info", "exc_text", "filename", "funcName",
    "levelname", "levelno", "lineno", "module", "msecs", "message", "msg", "name",
    "pathname", "process", "processName", "relativeCreated", "stack_info",
    "taskName", "thread", "threadName",
))


class _FormatadorJson(logging.Formatter):
    def format(self, registro):
        evento = {
            "timestamp": datetime.fromtimestamp(registro.created, timezone.utc).isoformat(),
            "level": registro.levelname,
            "logger": registro.name,
            "message": registro.getMessage(),
            **{k: v for k, v in registro.__dict__.items() if k not in _ATRIBUTOS_PADRAO and not k.startswith("_")},
        }
        if registro.exc_info:
            evento["exception"] = self.formatException(registro.exc_info)
        return json.dumps(evento, ensure_ascii=False, default=str)


_saida = logging.StreamHandler(sys.stdout)
_saida.setFormatter(_FormatadorJson())
logger = logging.getLogger("auth")
logger.handlers = [_saida]
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
logger.propagate = False


def _resposta(status: int, corpo: dict, request_id: str) -> dict:
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json", "x-request-id": request_id},
        "body": json.dumps(corpo, ensure_ascii=False),
    }


def handler(evento, contexto):
    request_id = getattr(contexto, "aws_request_id", "")
    log = {"request_id": request_id}

    try:
        corpo = evento.get("body") or ""
        if evento.get("isBase64Encoded"):
            corpo = base64.b64decode(corpo).decode()
        valor = json.loads(corpo).get("cpf") if corpo else None
        documento = normalizar(valor)
    except (ValueError, AttributeError) as erro:
        detalhe = str(erro) if isinstance(erro, DocumentoInvalido) else 'Envie {"cpf": "..."} no corpo'
        logger.warning("Documento rejeitado: %s", detalhe, extra=log)
        return _resposta(400, {"detail": detalhe}, request_id)

    try:
        cliente = buscar_cliente(documento)
    except Exception:
        logger.exception("Falha ao consultar o banco", extra={**log, "documento": mascarar(documento)})
        return _resposta(503, {"detail": "Serviço temporariamente indisponível"}, request_id)

    if cliente is None:
        logger.info("Cliente não encontrado", extra={**log, "documento": mascarar(documento)})
        return _resposta(404, {"detail": "Cliente não encontrado"}, request_id)
    if not cliente.ativo:
        logger.warning("Cliente inativo tentou autenticar", extra={**log, "cliente_id": cliente.id})
        return _resposta(403, {"detail": "Cadastro inativo — procure a oficina"}, request_id)

    token, expira_em = emitir(
        cliente_id=cliente.id,
        cpf_cnpj=cliente.cpf_cnpj,
        nome=cliente.nome,
        secret_key=os.environ["SECRET_KEY"],
        algoritmo=os.environ.get("ALGORITHM", "HS256"),
        expiracao_minutos=int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
    )
    logger.info("Cliente autenticado", extra={**log, "cliente_id": cliente.id, "documento": mascarar(documento)})
    return _resposta(200, {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expira_em,
        "cliente": {"id": cliente.id, "nome": cliente.nome},
    }, request_id)
