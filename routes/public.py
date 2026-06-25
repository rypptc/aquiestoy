from flask import Blueprint, render_template, request
from models import Persona

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def index():
    q = request.args.get("q", "").strip()

    personas = Persona.query

    if q:
        like = f"%{q}%"
        personas = personas.filter(
            Persona.nombre.ilike(like) |
            Persona.apellido.ilike(like) |
            Persona.notas.ilike(like)
        )

    personas = personas.order_by(Persona.apellido, Persona.nombre).all()

    return render_template("index.html", personas=personas, q=q)


@public_bp.route("/persona/<int:persona_id>")
def persona(persona_id):
    p = Persona.query.get_or_404(persona_id)
    return render_template("persona.html", persona=p)
