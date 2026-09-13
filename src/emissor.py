from datetime import datetime, timedelta, timezone

import jwt


def emitir(*, cliente_id: str, cpf_cnpj: str, nome: str, secret_key: str,
           algoritmo: str = "HS256", expiracao_minutos: int = 60) -> tuple[str, int]:
    """Assina o JWT do cliente; o claim `tipo` o separa do token de funcionário."""
    agora = datetime.now(timezone.utc)
    payload = {
        "sub": cliente_id,
        "tipo": "cliente",
        "cpf_cnpj": cpf_cnpj,
        "nome": nome,
        "iat": agora,
        "exp": agora + timedelta(minutes=expiracao_minutos),
    }
    return jwt.encode(payload, secret_key, algorithm=algoritmo), expiracao_minutos * 60
