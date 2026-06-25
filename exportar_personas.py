#!/usr/bin/env python3
"""
Exporta datos de producción a .tmp/ para consulta offline por Claude.

Genera:
    .tmp/personas.txt  — id, apellido, nombre de todas las personas
    .tmp/hashes.txt    — imagen_hash de todas las fuentes ya importadas

Uso:
    python exportar_personas.py
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

from app import create_app
from models import Persona, Fuente

TMP = BASE_DIR / ".tmp"


def main():
    app = create_app()
    with app.app_context():
        personas = Persona.query.order_by(Persona.apellido, Persona.nombre).all()
        hashes = [f.imagen_hash for f in Fuente.query.all() if f.imagen_hash]

    TMP.mkdir(exist_ok=True)

    personas_txt = TMP / "personas.txt"
    personas_txt.write_text(
        "\n".join(f"{p.id}\t{p.apellido}, {p.nombre}" for p in personas) + "\n",
        encoding="utf-8",
    )

    hashes_txt = TMP / "hashes.txt"
    hashes_txt.write_text("\n".join(hashes) + "\n", encoding="utf-8")

    print(f"{len(personas)} personas  → {personas_txt}")
    print(f"{len(hashes)} hashes     → {hashes_txt}")


if __name__ == "__main__":
    main()
