"""
Uso:
  python cargar.py fuente --url "https://x.com/..." --descripcion "Tweet @usuario"
  python cargar.py persona "Juan" "Pérez" --estado herido --notas "45 años, Los Frailes, Periférico de Catia" --fuente 1
  python cargar.py lista
"""
import argparse
from app import create_app
from extensions import db
from models import Persona, Fuente

app = create_app()


def cmd_fuente(args):
    with app.app_context():
        if args.url:
            existing = Fuente.query.filter_by(url=args.url).first()
            if existing:
                print(f"Fuente ya existe #{existing.id}: {args.url}")
                return
        f = Fuente(url=args.url, descripcion=args.descripcion)
        db.session.add(f)
        db.session.commit()
        print(f"Fuente #{f.id} creada")


def cmd_persona(args):
    with app.app_context():
        p = Persona(
            nombre=args.nombre,
            apellido=args.apellido,
            notas=args.notas,
        )
        db.session.add(p)
        db.session.flush()

        if args.fuente:
            f = db.session.get(Fuente, args.fuente)
            if f:
                p.fuentes.append(f)

        db.session.commit()
        print(f"Persona #{p.id}: {p.nombre_completo}")


def cmd_lista(args):
    with app.app_context():
        print("\n=== FUENTES ===")
        for f in Fuente.query.all():
            print(f"  [{f.id}] {f.descripcion or ''} | {f.url or ''}")

        print("\n=== PERSONAS ===")
        for p in Persona.query.order_by(Persona.apellido).all():
            fuentes = ", ".join(str(f.id) for f in p.fuentes)
            print(f"  [{p.id}] {p.nombre_completo} | fuentes:[{fuentes}] | {p.notas or ''}")


parser = argparse.ArgumentParser()
sub = parser.add_subparsers(dest="cmd")

p_fuente = sub.add_parser("fuente")
p_fuente.add_argument("--url")
p_fuente.add_argument("--descripcion")

p_pers = sub.add_parser("persona")
p_pers.add_argument("nombre")
p_pers.add_argument("apellido")
p_pers.add_argument("--notas")
p_pers.add_argument("--fuente", type=int)

sub.add_parser("lista")

args = parser.parse_args()
if args.cmd == "fuente":    cmd_fuente(args)
elif args.cmd == "persona": cmd_persona(args)
elif args.cmd == "lista":   cmd_lista(args)
else:                       parser.print_help()
