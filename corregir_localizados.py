#!/usr/bin/env python3
"""
Corrige los registros importados de localizados-venezuela.com:
- Extrae la URL de notas → crea Fuente individual por persona
- Limpia notas (quita la línea "Fuente: ...")
"""

import sys
import re

BASE_DIR = __file__.split('/corregir')[0]
sys.path.insert(0, BASE_DIR)

from app import create_app
from extensions import db
from models import Persona, Fuente

def main():
    app = create_app()

    with app.app_context():
        # Buscar personas con URL de localizados en sus notas
        personas = Persona.query.filter(
            Persona.notas.like('%localizadosvenezuela.com/localizados/%')
        ).all()

        print(f"✓ {len(personas)} personas con URL en notas\n")

        corregidas = 0
        errores = 0

        for persona in personas:
            if not persona.notas:
                continue

            # Extraer URL de notas (puede estar obfuscada o no)
            # Buscar el slug entre /localizados/ y el final o el separador
            match = re.search(r'https://localizadosvenezuela\.com/localizados/([^\s|]+)', persona.notas)
            if not match:
                errores += 1
                continue

            url_completa = match.group(0).strip()

            # Verificar si ya tiene esa fuente individual
            fuente_existente = next(
                (f for f in persona.fuentes if f.url == url_completa),
                None
            )

            if not fuente_existente:
                # Buscar si ya existe esa fuente en la BD
                fuente = Fuente.query.filter_by(url=url_completa).first()

                if not fuente:
                    fuente = Fuente(
                        url=url_completa,
                        descripcion="Localizados Venezuela"
                    )
                    db.session.add(fuente)
                    db.session.flush()

                # Quitar la fuente genérica si tiene solo esa
                fuente_generica = next(
                    (f for f in persona.fuentes if f.url == "https://localizadosvenezuela.com"),
                    None
                )
                if fuente_generica:
                    persona.fuentes.remove(fuente_generica)

                persona.fuentes.append(fuente)

            # Limpiar notas: quitar la línea " | Fuente: ..."
            notas_limpias = re.sub(r'\s*\|\s*Fuente:.*$', '', persona.notas).strip()
            # También limpiar si empieza con "Fuente:"
            notas_limpias = re.sub(r'^Fuente:.*$', '', notas_limpias).strip()

            persona.notas = notas_limpias if notas_limpias else None

            corregidas += 1

        db.session.commit()

        print(f"{'='*50}")
        print(f"✓ Corregidas: {corregidas}")
        print(f"✗ Errores:    {errores}")
        print(f"{'='*50}\n")

        # Eliminar fuente genérica si ya no tiene personas
        fuente_generica = Fuente.query.filter_by(url="https://localizadosvenezuela.com").first()
        if fuente_generica and len(fuente_generica.personas) == 0:
            db.session.delete(fuente_generica)
            db.session.commit()
            print("✓ Fuente genérica eliminada (sin personas)")

if __name__ == '__main__':
    main()
