#!/usr/bin/env python3
"""
Importa pacientes del PDF 'PACIENTES HMPC 2' (.tmp/hmpc.json) a la BD.
SOLO AGREGA NUEVOS (dedup por nombre, nombre invertido y cédula).

  hospital = "Hospital Miguel Pérez Carreño"   (HMPC)
  fuente   = "Grupo de localización WhatsApp"   (compartida)
  status   = "Por confirmar"
  nombres/apellidos -> de MAYÚSCULAS a Capitalización (de/los/la en minúscula)

Uso: python importar_hmpc.py [--commit]
"""
import json
import os
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

ARCHIVO = ".tmp/hmpc.json"
COMMIT = "--commit" in sys.argv
HOSPITAL = "Hospital Miguel Pérez Carreño"
FUENTE_DESC = "Grupo de localización WhatsApp"

MINUS = {"de", "del", "la", "las", "los", "y", "e"}


def titlecase(s):
    s = (s or "").strip()
    if not s:
        return ""
    out = []
    for i, w in enumerate(s.split()):
        lw = w.lower()
        out.append(lw if (lw in MINUS and i > 0) else lw.capitalize())
    return " ".join(out)


def nz(s):
    return (s or "").strip().lower()


def main():
    data = json.load(open(ARCHIVO, encoding="utf-8"))
    app = create_app()

    with app.app_context():
        nombres, cis = set(), set()
        for p in Persona.query.with_entities(Persona.nombre, Persona.apellido, Persona.ci):
            nombres.add(f"{nz(p.nombre)}||{nz(p.apellido)}")
            c = "".join(ch for ch in (p.ci or "") if ch.isdigit())
            if c:
                cis.add(c)

        fuente = Fuente.query.filter_by(descripcion=FUENTE_DESC).first()
        if not fuente:
            fuente = Fuente(descripcion=FUENTE_DESC)
            db.session.add(fuente)
            db.session.flush()

        creadas = dup_n = dup_s = dup_c = interno = sin_nombre = 0
        vistos = set()

        for d in data:
            nombre = (d.get("nombre") or "").strip()
            apellido = (d.get("apellido") or "").strip()
            if not nombre and not apellido:
                sin_nombre += 1
                continue

            n, a = nz(nombre), nz(apellido)
            k1, k2 = f"{n}||{a}", f"{a}||{n}"
            ci = "".join(ch for ch in (d.get("cedula") or "") if ch.isdigit())

            if k1 in vistos or k2 in vistos:
                interno += 1
                continue
            if k1 in nombres:
                dup_n += 1
                continue
            if k2 in nombres:
                dup_s += 1
                continue
            if ci and ci in cis:
                dup_c += 1
                continue

            vistos.add(k1)
            if ci:
                cis.add(ci)

            p = Persona(
                nombre=titlecase(nombre),
                apellido=titlecase(apellido),
                ci=ci or None,
                hospital=HOSPITAL,
                status="Por confirmar",
                num_reportes=1,
            )
            p.fuentes.append(fuente)
            db.session.add(p)
            creadas += 1

        print(f"  A insertar (NUEVOS):   {creadas}")
        print(f"  Ya en BD nombre:       {dup_n}")
        print(f"  Ya en BD invertido:    {dup_s}")
        print(f"  Ya en BD cedula:       {dup_c}")
        print(f"  Dup interno:           {interno}")
        print(f"  Sin nombre (skip):     {sin_nombre}")
        print(f"  control: {creadas+dup_n+dup_s+dup_c+interno+sin_nombre} == {len(data)}")

        if COMMIT:
            db.session.commit()
            print(f"\nOK COMMIT — {creadas} insertadas. Total: {Persona.query.count()}")
        else:
            db.session.rollback()
            print("\n(DRY-RUN — nada escrito. Usar --commit)")


if __name__ == "__main__":
    main()
