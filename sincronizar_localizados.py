#!/usr/bin/env python3
"""
Sincroniza datos de localizados-venezuela.com con Aquí Estoy
Identifica personas que están en ambas bases de datos (localizadas)
"""

import requests
import sys
from datetime import datetime
from difflib import SequenceMatcher

BASE_DIR = __file__.split('/sincronizar')[0]
sys.path.insert(0, BASE_DIR)

from app import create_app
from extensions import db
from models import Persona

LOCALIZADOS_API = "https://localizadosvenezuela.com/api/v1/localizados"

def normalize_name(nombre, apellido):
    """Normaliza nombre para comparación"""
    return f"{nombre.strip().lower()} {apellido.strip().lower()}"

def similarity(a, b):
    """Calcula similitud entre dos strings (0-1)"""
    return SequenceMatcher(None, a, b).ratio()

def fetch_all_localizados():
    """Descarga todos los datos de localizados-venezuela"""
    localizados = []
    page = 1
    limit = 100

    print(f"📥 Descargando datos de localizados-venezuela.com...")

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

    print(f"\n✓ {len(localizados)} registros descargados")
    return localizados

def find_matches(aquiestoy_personas, localizados):
    """Identifica personas en ambas bases de datos"""
    matches = []
    threshold = 0.85  # Similitud mínima para coincidir

    print(f"\n🔍 Comparando {len(aquiestoy_personas)} personas de Aquí Estoy...")
    print(f"   con {len(localizados)} personas de Localizados...")

    for ae_persona in aquiestoy_personas:
        ae_name = normalize_name(ae_persona.nombre, ae_persona.apellido)

        for loc_persona in localizados:
            loc_name = normalize_name(
                loc_persona['nombreCompleto'].split()[0],
                ' '.join(loc_persona['nombreCompleto'].split()[1:])
            )

            sim = similarity(ae_name, loc_name)

            if sim >= threshold:
                matches.append({
                    'aquiestoy_id': ae_persona.id,
                    'aquiestoy_name': ae_persona.nombre_completo,
                    'localizados_name': loc_persona['nombreCompleto'],
                    'lugar': loc_persona['lugarNombre'],
                    'edad': loc_persona.get('edad'),
                    'cedula': loc_persona.get('cedula'),
                    'similarity': sim,
                    'fecha_localizado': loc_persona['publicadoEn']
                })

    return matches

def main():
    app = create_app()

    with app.app_context():
        # Descargar datos de localizados-venezuela
        localizados = fetch_all_localizados()

        # Obtener personas de Aquí Estoy
        aquiestoy_personas = Persona.query.all()
        print(f"\n✓ {len(aquiestoy_personas)} personas en Aquí Estoy")

        # Encontrar coincidencias
        matches = find_matches(aquiestoy_personas, localizados)

        # Mostrar resultados
        print(f"\n{'='*60}")
        print(f"✓ COINCIDENCIAS ENCONTRADAS: {len(matches)}")
        print(f"{'='*60}\n")

        if matches:
            for i, match in enumerate(matches[:20], 1):  # Mostrar primeras 20
                print(f"{i}. {match['aquiestoy_name']}")
                print(f"   → Localizado en: {match['lugar']}")
                if match['edad']:
                    print(f"   → Edad: {match['edad']}")
                if match['cedula']:
                    print(f"   → Cédula: {match['cedula']}")
                print(f"   → Similitud: {match['similarity']:.0%}")
                print()

            if len(matches) > 20:
                print(f"... y {len(matches) - 20} más\n")

        print(f"{'='*60}")
        print(f"Resumen:")
        print(f"  • Total en Aquí Estoy: {len(aquiestoy_personas)}")
        print(f"  • Total en Localizados: {len(localizados)}")
        print(f"  • Coincidencias: {len(matches)} ({len(matches)/len(aquiestoy_personas)*100:.1f}%)")
        print(f"{'='*60}")

        # Guardar reporte
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f".tmp/sincronizacion_{timestamp}.txt"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"SINCRONIZACIÓN LOCALIZADOS - {datetime.now().isoformat()}\n")
            f.write(f"{'='*60}\n\n")
            f.write(f"Total en Aquí Estoy: {len(aquiestoy_personas)}\n")
            f.write(f"Total en Localizados: {len(localizados)}\n")
            f.write(f"Coincidencias: {len(matches)}\n\n")
            f.write(f"{'='*60}\n")
            f.write("COINCIDENCIAS DETALLADAS:\n")
            f.write(f"{'='*60}\n\n")

            for match in matches:
                f.write(f"{match['aquiestoy_name']}\n")
                f.write(f"  Localizado en: {match['lugar']}\n")
                if match['edad']:
                    f.write(f"  Edad: {match['edad']}\n")
                if match['cedula']:
                    f.write(f"  Cédula: {match['cedula']}\n")
                f.write(f"  Similitud: {match['similarity']:.0%}\n")
                f.write(f"  Fecha: {match['fecha_localizado']}\n\n")

        print(f"\n📄 Reporte guardado en: {report_file}")

if __name__ == '__main__':
    main()
