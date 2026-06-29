#!/usr/bin/env python3
"""
Importa pacientes_export_limpio.json a la BD de Aquí Estoy.
SOLO AGREGA NUEVOS (no toca ni pisa registros existentes).

Dedup multi-clave contra los registros existentes:
    - (nombre, apellido)
    - (apellido, nombre)  -> atrapa nombres con orden invertido
    - cédula (solo dígitos)
    - además dedup interno dentro del propio export

Mapeo de campos:
    cedula -> ci                edad -> edad
    genero -> sexo (F/M; "Sin especificar" -> NULL)
    hospital_albergue -> hospital
    estado_salud -> estado_salud (columna nueva; NO se toca 'status')
    diagnostico -> notas (salvo "Se desconoce"/vacío)
    status = 'Por confirmar'    (lista externa, sin verificar)
    Ref: localizadosvenezuela.com/... -> Fuente individual
    resto -> Fuente compartida del batch
    lat/lng/tipo -> no se importan

Uso: python importar_export.py [archivo_limpio.json] [--commit]
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except Exception:
    pass

from app import create_app
from extensions import db
from models import Persona, Fuente

ARCHIVO = next((a for a in sys.argv[1:] if not a.startswith("-")),
               ".tmp/pacientes_export_limpio.json")
COMMIT = "--commit" in sys.argv

FUENTE_BATCH_DESC = "Export pacientes hospitales/albergues — importado 28JUN26"
REF_RE = re.compile(r"Ref:\s*(localizadosvenezuela\.com/\S+)")


def norm(s):
    return (s or "").strip().lower()


def only_digits(s):
    return "".join(c for c in (s or "") if c.isdigit())


def map_sexo(genero):
    return genero if genero in ("Femenino", "Masculino") else None


def map_notas(diag):
    d = (diag or "").strip()
    if not d or d.lower() == "se desconoce":
        return None
    return d


def main():
    data = json.load(open(ARCHIVO, encoding="utf-8"))
    app = create_app()

    with app.app_context():
        # claves existentes en la BD
        nombres = set()
        cis = set()
        for p in Persona.query.with_entities(Persona.nombre, Persona.apellido, Persona.ci):
            nombres.add(f"{norm(p.nombre)}||{norm(p.apellido)}")
            c = only_digits(p.ci)
            if c:
                cis.add(c)

        fuente_batch = Fuente.query.filter_by(descripcion=FUENTE_BATCH_DESC).first()
        if not fuente_batch:
            fuente_batch = Fuente(descripcion=FUENTE_BATCH_DESC)
            db.session.add(fuente_batch)
            db.session.flush()

        ref_cache = {}
        creadas = dup_nombre = dup_swap = dup_ci = dup_interno = sin_nombre = 0
        vistos = set()

        for d in data:
            nombre = (d.get("nombre") or "").strip()
            apellido = (d.get("apellido") or "").strip()
            if not nombre and not apellido:
                sin_nombre += 1
                continue

            n, a = norm(nombre), norm(apellido)
            k1, k2 = f"{n}||{a}", f"{a}||{n}"
            ci = only_digits(d.get("cedula"))

            if k1 in vistos or k2 in vistos:
                dup_interno += 1
                continue
            if k1 in nombres:
                dup_nombre += 1
                continue
            if k2 in nombres:
                dup_swap += 1
                continue
            if ci and ci in cis:
                dup_ci += 1
                continue

            vistos.add(k1)
            if ci:
                cis.add(ci)

            p = Persona(
                nombre=nombre,
                apellido=apellido,
                ci=ci or None,
                edad=(str(d.get("edad")).strip() or None) if d.get("edad") else None,
                sexo=map_sexo(d.get("genero")),
                hospital=(d.get("hospital_albergue") or "").strip() or None,
                status="Por confirmar",
                estado_salud=(d.get("estado_salud") or "").strip() or None,
                num_reportes=1,
                notas=map_notas(d.get("diagnostico")),
            )

            m = REF_RE.search(d.get("diagnostico") or "")
            if m:
                url = "https://" + m.group(1)
                fobj = ref_cache.get(url)
                if not fobj:
                    fobj = Fuente(url=url, descripcion="Localizados Venezuela")
                    db.session.add(fobj)
                    db.session.flush()
                    ref_cache[url] = fobj
                p.fuentes.append(fobj)
            else:
                p.fuentes.append(fuente_batch)

            db.session.add(p)
            creadas += 1

        print(f"  A insertar (NUEVOS):    {creadas}")
        print(f"  Ya en BD por nombre:    {dup_nombre}")
        print(f"  Ya en BD nombre invert: {dup_swap}")
        print(f"  Ya en BD por cedula:    {dup_ci}")
        print(f"  Dup interno export:     {dup_interno}")
        print(f"  Sin nombre (skip):      {sin_nombre}")
        print(f"  Fuentes 'Ref' creadas:  {len(ref_cache)}")
        total = creadas + dup_nombre + dup_swap + dup_ci + dup_interno + sin_nombre
        print(f"  (control: {total} == {len(data)} registros)")

        if COMMIT:
            db.session.commit()
            print(f"\nOK COMMIT — {creadas} personas insertadas")
            print(f"  Total personas ahora: {Persona.query.count()}")
        else:
            db.session.rollback()
            print("\n(DRY-RUN — nada escrito. Usar --commit para aplicar)")


if __name__ == "__main__":
    main()
