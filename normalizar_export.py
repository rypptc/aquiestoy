#!/usr/bin/env python3
"""
Normaliza pacientes_export.json (esquema externo con lat/lng) dejando el MISMO
esquema pero con valores limpios:

  - mojibake (doble codificación UTF-8) reparado con ftfy en todos los textos
  - estado_salud  -> conjunto canónico en Title Case
  - genero        -> Femenino / Masculino / Sin especificar
  - edad          -> string entera válida (0-120) o "" si es inválida/corrupta
  - cedula        -> solo dígitos; "Sin Documentos"/no-numérico -> ""
  - diagnostico   -> mojibake reparado + "se desconoce" -> "Se desconoce"
  - nombre/apellido -> mojibake reparado + strip (no se reordenan)

Uso: python normalizar_export.py [entrada.json] [salida.json]
"""
import json
import sys
import re
from collections import Counter

import ftfy

ENTRADA = sys.argv[1] if len(sys.argv) > 1 else "/Users/ro/Downloads/pacientes_export.json"
SALIDA  = sys.argv[2] if len(sys.argv) > 2 else ".tmp/pacientes_export_limpio.json"

ESTADO_MAP = {
    "estable": "Estable",
    "en_observacion": "En observación",
    "se desconoce": "Se desconoce",
    "encontrado": "Encontrado",
    "delicado": "Delicado",
    "crítico": "Crítico",
    "critico": "Crítico",
    "fallecido": "Fallecido",
    "de alta": "De alta",
}

GENERO_MAP = {
    "f": "Femenino",
    "femenino": "Femenino",
    "m": "Masculino",
    "masculino": "Masculino",
    "sin especificar": "Sin especificar",
}


def fix_text(v):
    if not isinstance(v, str):
        return v
    return ftfy.fix_text(v).strip()


def norm_estado(v):
    v = fix_text(v) or ""
    return ESTADO_MAP.get(v.lower(), v)


def norm_genero(v):
    v = fix_text(v) or ""
    return GENERO_MAP.get(v.lower(), v or "Sin especificar")


def norm_edad(v):
    # int o str; válida si 0 <= n <= 120
    if isinstance(v, bool):
        return ""
    if isinstance(v, (int, float)):
        n = int(v)
    else:
        s = str(v).strip()
        if not s:
            return ""
        m = re.match(r"-?\d+", s)
        if not m:
            return ""
        n = int(m.group())
    if 0 <= n <= 120:
        return str(n)
    return ""  # negativos / valores absurdos (cédulas filtradas, etc.)


def norm_cedula(v):
    v = fix_text(v) or ""
    digits = re.sub(r"\D", "", v)
    return digits  # "" si no había dígitos (p.ej. "Sin Documentos")


def norm_diag(v):
    v = fix_text(v) or ""
    if v.lower() == "se desconoce":
        return "Se desconoce"
    return v


def main():
    data = json.load(open(ENTRADA, encoding="utf-8"))

    stats = {
        "total": len(data),
        "edad_descartada": 0,
        "cedula_descartada": 0,
        "mojibake_reparado": 0,
        "sin_nombre": 0,
    }
    estado_despues = Counter()
    genero_despues = Counter()

    out = []
    for d in data:
        nombre = fix_text(d.get("nombre", "")) or ""
        apellido = fix_text(d.get("apellido", "")) or ""
        if not nombre and not apellido:
            stats["sin_nombre"] += 1

        cedula_orig = str(d.get("cedula", "") or "")
        cedula = norm_cedula(d.get("cedula"))
        if cedula_orig.strip() and not cedula:
            stats["cedula_descartada"] += 1

        edad = norm_edad(d.get("edad"))
        if str(d.get("edad", "")).strip() and not edad:
            stats["edad_descartada"] += 1

        estado = norm_estado(d.get("estado_salud"))
        estado_despues[estado] += 1

        genero = norm_genero(d.get("genero"))
        genero_despues[genero] += 1

        # detectar si algún campo tenía mojibake
        for k in ("nombre", "apellido", "hospital_albergue", "diagnostico"):
            orig = d.get(k)
            if isinstance(orig, str) and ftfy.fix_text(orig) != orig:
                stats["mojibake_reparado"] += 1
                break

        out.append({
            "nombre": nombre,
            "apellido": apellido,
            "cedula": cedula,
            "edad": edad,
            "genero": genero,
            "hospital_albergue": fix_text(d.get("hospital_albergue", "")) or "",
            "tipo": d.get("tipo", ""),
            "estado_salud": estado,
            "diagnostico": norm_diag(d.get("diagnostico")),
            "lat": d.get("lat"),
            "lng": d.get("lng"),
        })

    json.dump(out, open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"OK {stats['total']} registros normalizados -> {SALIDA}\n")
    print(f"  mojibake reparado:   {stats['mojibake_reparado']} registros")
    print(f"  edad descartada:     {stats['edad_descartada']} (invalida/corrupta)")
    print(f"  cedula descartada:   {stats['cedula_descartada']} (no numerica)")
    print(f"  sin nombre+apellido: {stats['sin_nombre']}")
    print("\n  estado_salud:")
    for v, c in estado_despues.most_common():
        print(f"    {v}: {c}")
    print("\n  genero:")
    for v, c in genero_despues.most_common():
        print(f"    {v}: {c}")


if __name__ == "__main__":
    main()
