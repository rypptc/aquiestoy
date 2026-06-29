#!/usr/bin/env python3
"""
Importa personas desde el CSV de terremotovenezuela.
Borra todos los registros existentes y reimporta desde cero.
"""
import csv
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import Persona, Fuente, persona_fuente

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else 'personas.csv'

app = create_app()

with app.app_context():
    print("Borrando datos existentes...")
    db.session.execute(persona_fuente.delete())
    Fuente.query.delete()
    Persona.query.delete()
    db.session.commit()
    print("  Listo.")

    creadas = 0
    skipped = 0
    fuentes_cache = {}

    with open(CSV_PATH, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            nombre   = row.get('Nombre', '').strip()
            apellido = row.get('Apellido', '').strip()

            if not nombre:
                skipped += 1
                continue

            ci           = row.get('CI', '').strip() or None
            edad         = row.get('Edad', '').strip() or None
            sexo         = row.get('Sexo', '').strip() or None
            hospital     = row.get('Hospital', '').strip() or None
            status       = row.get('Status', 'Confirmado').strip() or 'Confirmado'
            num_reportes = row.get('NumReportes', '1').strip()
            notas        = row.get('Notas', '').strip() or None

            try:
                num_reportes = int(num_reportes)
            except:
                num_reportes = 1

            p = Persona(
                nombre=nombre,
                apellido=apellido,
                ci=ci,
                edad=edad,
                sexo=sexo,
                hospital=hospital,
                status=status,
                num_reportes=num_reportes,
                notas=notas,
            )

            db.session.add(p)
            db.session.flush()

            fuentes_raw = row.get('Fuentes', '').strip()
            if fuentes_raw:
                for url in fuentes_raw.split(';'):
                    url = url.strip()
                    if not url:
                        continue
                    if url not in fuentes_cache:
                        f_obj = Fuente(url=url)
                        db.session.add(f_obj)
                        db.session.flush()
                        fuentes_cache[url] = f_obj
                    p.fuentes.append(fuentes_cache[url])
            creadas += 1

            if creadas % 500 == 0:
                db.session.commit()
                print(f"  {creadas} importadas...")

    db.session.commit()
    print(f"\nResumen:")
    print(f"  Creadas:  {creadas}")
    print(f"  Saltadas: {skipped}")
