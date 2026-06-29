#!/usr/bin/env python3
"""
Importa registros de localizados-venezuela.com a Aquí Estoy
Mapea los campos al formato: nombre, apellido, notas
"""

import requests
import sys
from datetime import datetime

BASE_DIR = __file__.split('/importar')[0]
sys.path.insert(0, BASE_DIR)

from app import create_app
from extensions import db
from models import Persona, Fuente

LOCALIZADOS_API = "https://localizadosvenezuela.com/api/v1/localizados"

def parse_nombre_completo(nombre_completo):
    """Parsea nombre completo en nombre y apellido"""
    partes = nombre_completo.strip().split(maxsplit=1)
    if len(partes) == 2:
        return partes[0], partes[1]
    elif len(partes) == 1:
        return partes[0], ""
    return "", ""

def build_notas(loc_data):
    """Construye campo notas con info adicional (sin URL)"""
    notas_parts = []

    if loc_data.get('edad'):
        notas_parts.append(f"Edad: {loc_data['edad']}")

    if loc_data.get('cedula'):
        notas_parts.append(f"CI: {loc_data['cedula']}")

    if loc_data.get('direccion'):
        notas_parts.append(f"Dirección: {loc_data['direccion']}")

    if loc_data.get('lugarNombre'):
        notas_parts.append(f"Hospital: {loc_data['lugarNombre']}")

    return " | ".join(notas_parts) if notas_parts else ""

def fetch_all_localizados():
    """Descarga todos los registros de localizados-venezuela"""
    localizados = []
    page = 1
    limit = 100

    print(f"📥 Descargando desde localizados-venezuela.com...")

    while True:
        try:
            url = f"{LOCALIZADOS_API}?page={page}&limit={limit}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            localizados.extend(data['data'])

            total_pages = data['meta']['totalPages']
            print(f"  Página {page}/{total_pages} ({len(localizados)} registros)...", end='\r')

            if page >= total_pages:
                break

            page += 1

        except Exception as e:
            print(f"\n❌ Error descargando página {page}: {e}")
            break

    print(f"\n✓ {len(localizados)} registros descargados\n")
    return localizados

def import_to_db(localizados):
    """Importa registros a la BD de Aquí Estoy"""
    creadas = 0
    duplicadas = 0

    print(f"📊 Importando {len(localizados)} registros...\n")

    for i, loc_data in enumerate(localizados, 1):
        nombre, apellido = parse_nombre_completo(loc_data['nombreCompleto'])

        if not nombre or not apellido:
            continue

        # Verificar si ya existe (nombre + apellido exacto)
        existe = Persona.query.filter_by(
            nombre=nombre,
            apellido=apellido
        ).first()

        if existe:
            duplicadas += 1
            continue

        # Crear notas (sin URL)
        notas = build_notas(loc_data)

        # Fuente individual con URL específica de esta persona
        url_persona = f"https://localizadosvenezuela.com/localizados/{loc_data['slug']}"
        fuente_individual = Fuente(
            url=url_persona,
            descripcion="Localizados Venezuela"
        )
        db.session.add(fuente_individual)
        db.session.flush()

        # Crear persona
        persona = Persona(
            nombre=nombre,
            apellido=apellido,
            notas=notas
        )
        persona.fuentes.append(fuente_individual)
        db.session.add(persona)

        creadas += 1

        if i % 100 == 0:
            print(f"  {i}/{len(localizados)} procesados... ({creadas} nuevas, {duplicadas} duplicadas)", end='\r')

    db.session.commit()

    print(f"\n\n{'='*60}")
    print(f"✓ IMPORTACIÓN COMPLETADA")
    print(f"{'='*60}")
    print(f"  • Registros procesados: {len(localizados)}")
    print(f"  • Personas creadas: {creadas}")
    print(f"  • Duplicadas (saltadas): {duplicadas}")
    print(f"{'='*60}\n")

    # Guardar reporte
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f".tmp/importacion_localizados_{timestamp}.txt"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"IMPORTACIÓN LOCALIZADOS - {datetime.now().isoformat()}\n")
        f.write(f"{'='*60}\n\n")
        f.write(f"Registros procesados: {len(localizados)}\n")
        f.write(f"Personas creadas: {creadas}\n")
        f.write(f"Duplicadas (saltadas): {duplicadas}\n\n")
        f.write(f"{'='*60}\n")

    print(f"📄 Reporte: {report_file}\n")

def main():
    import os
    os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL') or 'postgresql://aquiestoy:aquiestoy2026@localhost/aquiestoy'

    app = create_app()

    with app.app_context():
        localizados = fetch_all_localizados()
        import_to_db(localizados)

if __name__ == '__main__':
    main()
