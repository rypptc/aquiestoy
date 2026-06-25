#!/usr/bin/env python3
"""
Importa archivos JSON del directorio .tmp/batch/ a la base de datos.

Uso:
    python importar.py                    # procesa todos los JSON en .tmp/batch/
    python importar.py archivo.json       # procesa un archivo específico
    python importar.py .tmp/batch/        # procesa todos los JSON en el directorio dado

Formato JSON esperado:
    {
        "fuente": {
            "url": "https://...",
            "descripcion": "Texto libre",
            "imagen_hash": "sha256hex"
        },
        "personas": [
            {"nombre": "Juan", "apellido": "García", "notas": "..."},
            ...
        ]
    }
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

from app import create_app
from extensions import db
from models import Fuente, Persona


def _buscar_persona_existente(nombre: str, apellido: str) -> Persona | None:
    like_nombre = f"%{nombre}%"
    like_apellido = f"%{apellido}%"
    return Persona.query.filter(
        Persona.nombre.ilike(like_nombre),
        Persona.apellido.ilike(like_apellido),
    ).first()


def _procesar_archivo(path: Path) -> dict:
    resultado = {"archivo": path.name, "fuente_id": None, "fuente_nueva": False,
                 "personas_creadas": [], "personas_existentes": [], "error": None}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        resultado["error"] = f"JSON inválido: {e}"
        return resultado

    fuente_data = data.get("fuente", {})
    personas_data = data.get("personas", [])

    # --- Fuente ---
    fuente = None
    url = fuente_data.get("url", "").strip()
    imagen_hash = fuente_data.get("imagen_hash", "").strip()
    descripcion = fuente_data.get("descripcion", "").strip()

    if url:
        fuente = Fuente.query.filter_by(url=url).first()
    if not fuente and imagen_hash:
        fuente = Fuente.query.filter_by(imagen_hash=imagen_hash).first()

    if not fuente:
        fuente = Fuente(
            url=url or None,
            descripcion=descripcion or None,
            imagen_hash=imagen_hash or None,
        )
        db.session.add(fuente)
        db.session.flush()
        resultado["fuente_nueva"] = True

    resultado["fuente_id"] = fuente.id

    # --- Personas ---
    for p_data in personas_data:
        nombre = p_data.get("nombre", "").strip()
        apellido = p_data.get("apellido", "").strip()
        notas = p_data.get("notas", "").strip()
        persona_id = p_data.get("persona_id")

        if not nombre or not apellido:
            continue

        existente = None
        if persona_id:
            existente = db.session.get(Persona, int(persona_id))
        if not existente:
            existente = _buscar_persona_existente(nombre, apellido)

        if existente:
            if fuente not in existente.fuentes:
                existente.fuentes.append(fuente)
            resultado["personas_existentes"].append(existente.nombre_completo)
        else:
            nueva = Persona(nombre=nombre, apellido=apellido, notas=notas or None)
            db.session.add(nueva)
            db.session.flush()
            nueva.fuentes.append(fuente)
            resultado["personas_creadas"].append(nueva.nombre_completo)

    db.session.commit()
    return resultado


def _mover_procesado(path: Path):
    destino = path.parent / "procesados"
    destino.mkdir(exist_ok=True)
    path.rename(destino / path.name)


def main():
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    else:
        target = BASE_DIR / ".tmp" / "batch"

    if target.is_file():
        archivos = [target]
    elif target.is_dir():
        archivos = sorted(target.glob("*.json"))
    else:
        print(f"No existe: {target}")
        sys.exit(1)

    if not archivos:
        print(f"No hay archivos JSON en {target}")
        sys.exit(0)

    app = create_app()
    totales = {"creadas": 0, "existentes": 0, "fuentes_nuevas": 0, "errores": 0}

    with app.app_context():
        for archivo in archivos:
            r = _procesar_archivo(archivo)

            if r["error"]:
                print(f"[ERROR] {r['archivo']}: {r['error']}")
                totales["errores"] += 1
                continue

            estado_fuente = "nueva" if r["fuente_nueva"] else f"id={r['fuente_id']}"
            print(f"\n{r['archivo']}  (fuente {estado_fuente})")

            for nombre in r["personas_creadas"]:
                print(f"  + {nombre}")
                totales["creadas"] += 1

            for nombre in r["personas_existentes"]:
                print(f"  ~ {nombre}  (ya existía, fuente vinculada)")
                totales["existentes"] += 1

            if r["fuente_nueva"]:
                totales["fuentes_nuevas"] += 1

            _mover_procesado(archivo)

    print(f"\n--- Resumen ---")
    print(f"  Personas creadas:   {totales['creadas']}")
    print(f"  Personas existentes: {totales['existentes']}")
    print(f"  Fuentes nuevas:     {totales['fuentes_nuevas']}")
    if totales["errores"]:
        print(f"  Errores:            {totales['errores']}")


if __name__ == "__main__":
    main()
