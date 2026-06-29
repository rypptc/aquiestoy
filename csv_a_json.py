#!/usr/bin/env python3
"""
Convierte CSVs de hospitales al formato JSON de importar.py
Uso: python csv_a_json.py archivo.csv [url_fuente]
"""

import csv
import json
import sys
from pathlib import Path

FUENTE_URL = "https://x.com/la_katuar/status/2070535453317456335"
FUENTE_DESC = "Lista consolidada de pacientes en hospitales de Venezuela — 25JUN26 7PM"

def csv_a_json(csv_path: Path, url: str, descripcion: str) -> dict:
    rows = []
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.reader(f)
        all_rows = list(reader)

    # Fila 0: nombre del hospital
    hospital = all_rows[0][0].strip() if all_rows else ""

    # Fila 1: encabezados — saltar
    # Filas 2+: datos
    personas = []
    for row in all_rows[2:]:
        if not row or not any(row):
            continue

        nombre_completo = row[1].strip() if len(row) > 1 else ""
        if not nombre_completo:
            continue

        edad       = row[2].strip() if len(row) > 2 else ""
        cedula     = row[3].strip() if len(row) > 3 else ""
        telefono   = row[4].strip() if len(row) > 4 else ""
        direccion  = row[5].strip() if len(row) > 5 else ""
        observ     = row[6].strip() if len(row) > 6 else ""

        # Notas: solo lo que está en el CSV, exactamente
        notas_parts = []
        if hospital:
            notas_parts.append(f"Hospital: {hospital}")
        if edad:
            notas_parts.append(f"Edad: {edad}")
        if cedula:
            notas_parts.append(f"CI: {cedula}")
        if telefono:
            notas_parts.append(f"Tel: {telefono}")
        if direccion:
            notas_parts.append(f"Dirección: {direccion}")
        if observ:
            notas_parts.append(f"Obs: {observ}")

        notas = " | ".join(notas_parts)

        personas.append({
            "nombre": nombre_completo,
            "apellido": nombre_completo,
            "notas": notas
        })

    return {
        "fuente": {
            "url": url,
            "descripcion": descripcion
        },
        "personas": personas
    }

def main():
    if len(sys.argv) < 2:
        print("Uso: python csv_a_json.py archivo.csv")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        print(f"No existe: {csv_path}")
        sys.exit(1)

    output_dir = Path(".tmp/batch")
    output_dir.mkdir(parents=True, exist_ok=True)

    data = csv_a_json(csv_path, FUENTE_URL, FUENTE_DESC)
    output_path = output_dir / (csv_path.stem + ".json")
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f"✓ {len(data['personas'])} personas → {output_path}")

if __name__ == "__main__":
    main()
