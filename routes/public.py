from flask import Blueprint, render_template, request
from models import Persona
import unicodedata
from rapidfuzz import fuzz

public_bp = Blueprint("public", __name__)

PER_PAGE = 30

def normalize(text):
    """Remove accents and convert to lowercase"""
    if not text:
        return ""
    nfd = unicodedata.normalize('NFD', text.lower())
    return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')

def fuzzy_match(query, text, threshold=92):
    """Check if query matches text with fuzzy matching"""
    from rapidfuzz import distance
    norm_query = normalize(query)
    norm_text = normalize(text)

    # For exact substring match, that's always valid
    if norm_query in norm_text or norm_text in norm_query:
        return True

    # Levenshtein distance - very strict
    lev_distance = distance.Levenshtein.distance(norm_query, norm_text)
    max_distance = 1  # Only allow 1 character difference

    return lev_distance <= max_distance

@public_bp.route("/")
def index():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    personas = Persona.query.all()
    resultados = []

    if q:
        palabras = q.split()

        for persona in personas:
            matches = True
            for palabra in palabras:
                # Only search in nombre and apellido with fuzzy matching
                palabra_match = (
                    fuzzy_match(palabra, persona.nombre) or
                    fuzzy_match(palabra, persona.apellido)
                )

                if not palabra_match:
                    matches = False
                    break

            if matches:
                resultados.append(persona)
    else:
        resultados = Persona.query.all()

    # Order by apellido, nombre
    resultados.sort(key=lambda p: (p.apellido or "", p.nombre or ""))

    # Manual pagination
    total = len(resultados)
    per_page = PER_PAGE
    offset = (page - 1) * per_page
    items = resultados[offset:offset + per_page]

    # Create a simple pagination-like object
    class Paginator:
        def __init__(self, items, total, page, per_page):
            self.items = items
            self.total = total
            self.page = page
            self.per_page = per_page
            self.pages = max(1, (total + per_page - 1) // per_page)
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1 if self.has_prev else None
            self.next_num = page + 1 if self.has_next else None

        def iter_pages(self, left_edge=1, right_edge=1, left_current=2, right_current=2):
            last = 0
            for num in range(1, self.pages + 1):
                if (num <= left_edge or
                    (self.page - left_current <= num <= self.page + right_current) or
                    num > self.pages - right_edge):
                    if last + 1 != num:
                        yield None
                    yield num
                    last = num

    paginacion = Paginator(items, total, page, per_page)

    return render_template("index.html", paginacion=paginacion, q=q)


@public_bp.route("/persona/<int:persona_id>")
def persona(persona_id):
    p = Persona.query.get_or_404(persona_id)
    return render_template("persona.html", persona=p)


RECURSOS = [
    {
        'nombre': 'Terremoto Venezuela App',
        'url': 'https://terremotovenezuela.app/',
        'descripcion': None
    },
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
    {
        'nombre': 'Hospitales en Venezuela',
        'url': 'https://hospitalesenvenezuela.com/',
        'descripcion': None
    },
    {
        'nombre': 'Terremoto VE',
        'url': 'https://terremotove.netlify.app/',
        'descripcion': None
    },
    {
        'nombre': 'Enlaza Venezuela',
        'url': 'https://www.enlazavenezuela.com/',
        'descripcion': None
    },
    {
        'nombre': 'SOS La Guaira',
        'url': 'https://soslaguaira.lat/',
        'descripcion': None
    },
    {
        'nombre': 'Venezuela Reporta',
        'url': 'https://venezuelareporta.org/',
        'descripcion': None
    },
    {
        'nombre': 'Terremoto VZLA Hospitales',
        'url': 'https://terremotovzla-hospitales.click/',
        'descripcion': None
    },
]


@public_bp.route("/recursos")
def recursos():
    return render_template("recursos.html", recursos=RECURSOS)
