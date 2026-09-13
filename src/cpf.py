import re


class DocumentoInvalido(ValueError):
    """CPF ou CNPJ com formato ou dígito verificador inválido."""


PESOS_CNPJ = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]


def _digito(base: str, pesos) -> str:
    resto = sum(int(d) * p for d, p in zip(base, pesos)) % 11
    return "0" if resto < 2 else str(11 - resto)


def normalizar(valor) -> str:
    """Valida o CPF ou CNPJ e devolve só os dígitos."""
    if not isinstance(valor, str) or not re.fullmatch(r"[\d.\-/\s]+", valor):
        raise DocumentoInvalido("Informe um CPF ou CNPJ válido")
    d = re.sub(r"\D", "", valor)
    if len(d) == 11:
        pesos = range(10, 1, -1), range(11, 1, -1)
    elif len(d) == 14:
        pesos = PESOS_CNPJ, [6] + PESOS_CNPJ
    else:
        raise DocumentoInvalido("CPF deve ter 11 dígitos ou CNPJ 14 dígitos")
    if len(set(d)) == 1 or d[-2:] != _digito(d[:-2], pesos[0]) + _digito(d[:-1], pesos[1]):
        raise DocumentoInvalido("Dígitos verificadores incorretos")
    return d


def mascarar(digitos: str) -> str:
    """Oculta o miolo do documento para uso em log (LGPD)."""
    return f"{digitos[:3]}***{digitos[-2:]}"
