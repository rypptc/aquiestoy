from flask import Blueprint, render_template, request
from models import Persona

public_bp = Blueprint("public", __name__)

PER_PAGE = 30


@public_bp.route("/")
def index():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    personas = Persona.query

    if q:
        like = f"%{q}%"
        personas = personas.filter(
            Persona.nombre.ilike(like) |
            Persona.apellido.ilike(like) |
            Persona.notas.ilike(like)
        )

    personas = personas.order_by(Persona.apellido, Persona.nombre)
    paginacion = personas.paginate(page=page, per_page=PER_PAGE, error_out=False)

    return render_template("index.html", paginacion=paginacion, q=q)


@public_bp.route("/persona/<int:persona_id>")
def persona(persona_id):
    p = Persona.query.get_or_404(persona_id)
    return render_template("persona.html", persona=p)


RECURSOS = [
    {
        'nombre': 'Desaparecidos Terremoto Venezuela',
        'url': 'https://desaparecidosterremotovenezuela.com/',
        'descripcion': None
    },
    {
        'nombre': 'Venezuela Te Busca',
        'url': 'https://venezuelatebusca.com/',
        'descripcion': None
    },
]


@public_bp.route("/recursos")
def recursos():
    return render_template("recursos.html", recursos=RECURSOS)
