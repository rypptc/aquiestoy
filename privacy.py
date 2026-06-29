"""Saneo de datos sensibles para exposición pública.

Política (1B): ofuscar cédula de forma parcial, ELIMINAR teléfono y dirección.
Se aplica en la capa de serialización (API + plantillas Jinja); la BD no se modifica.
"""
import re

# Cédula con puntos/prefijo:  V-15.780.524 | 15.780.524
_CI_DOT_RE = re.compile(r'\b([VEve])?-?\s?(\d{1,2})\.(\d{3})\.(\d{3})\b')
# Cédula cruda: corrida de 6-9 dígitos no precedida/seguida de dígito o X
_CI_RAW_RE = re.compile(r'(?<![\dX.])(\d{6,9})(?![\dX])')

# Teléfono venezolano: 0?4(12|14|16|24|26) + 7 dígitos con separadores opcionales
_TEL_RE = re.compile(r'\b0?4(?:12|14|16|24|26)\D?\d{3}\D?\d{4}\b')

# Segmentos etiquetados a eliminar por completo (valor hasta el siguiente "|" o fin)
_SEG_RE = re.compile(
    r'\s*(?:Tel|Tel[eé]fono|Telf|Contacto|Direcci[oó]n|Dir|Procedencia)\s*:\s*[^|]*',
    re.IGNORECASE,
)


def _mask(digits):
    """53446 -> 53XXXX46  (conserva primeros 2 y últimos 2)."""
    if len(digits) < 4:
        return digits
    return f"{digits[:2]}XXXX{digits[-2:]}"


def _ci_dot_repl(m):
    prefix = (m.group(1) or '').upper()
    digits = m.group(2) + m.group(3) + m.group(4)
    masked = _mask(digits)
    return f"{prefix}-{masked}" if prefix else masked


def ofuscar_ci(text):
    """Ofusca cédulas dentro de un texto (usado para el campo estructurado `ci`)."""
    if not text:
        return text
    text = _CI_DOT_RE.sub(_ci_dot_repl, text)
    text = _CI_RAW_RE.sub(lambda m: _mask(m.group(1)), text)
    return text


def sanitizar_notas(text):
    """Sanea el campo libre `notas`: ofusca cédula, elimina teléfono y dirección."""
    if not text:
        return text
    # 1) eliminar segmentos etiquetados de teléfono y dirección/procedencia
    text = _SEG_RE.sub('', text)
    # 2) eliminar teléfonos sueltos restantes
    text = _TEL_RE.sub('[oculto]', text)
    # 3) ofuscar cédulas
    text = ofuscar_ci(text)
    # 4) normalizar separadores colgantes que dejaron los segmentos eliminados
    text = re.sub(r'(\s*\|\s*){2,}', ' || ', text)
    text = re.sub(r'\|\s*\|', ' || ', text)
    text = re.sub(r'^\s*\|+\s*|\s*\|+\s*$', '', text)
    text = re.sub(r'[ \t]{2,}', ' ', text).strip(' |')
    return text
