from flask import Blueprint, render_template, request
from models import Persona
import unicodedata

public_bp = Blueprint("public", __name__)

PER_PAGE = 30

def normalize(text):
    """Remove accents and convert to lowercase"""
    if not text:
        return ""
    nfd = unicodedata.normalize('NFD', text.lower())
    return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')

@public_bp.route("/")
def index():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    personas = Persona.query.all()
    resultados = []

    if q:
        palabras = q.split()
        norm_palabras = [normalize(p) for p in palabras]

        for persona in personas:
            matches = True
            for norm_palabra in norm_palabras:
                # Exact match on normalized nombre/apellido
                palabra_match = (
                    norm_palabra in normalize(persona.nombre) or
                    norm_palabra in normalize(persona.apellido)
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
    {
        'nombre': 'Rescata Venezuela',
        'url': 'https://www.rescatavenezuela.com/',
        'descripcion': None
    },
]


@public_bp.route("/recursos")
def recursos():
    return render_template("recursos.html", recursos=RECURSOS)


@public_bp.route("/muestra")
def muestra():
    """Random sample of 20 people for quality check"""
    from sqlalchemy import func

    sample = Persona.query.order_by(func.random()).limit(20).all()

    data = []
    for persona in sample:
        item = {
            'nombre_completo': persona.nombre_completo,
            'notas': persona.notas,
            'fuentes': [{'url': f.url, 'descripcion': f.descripcion} for f in persona.fuentes]
        }
        data.append(item)

    return render_template('muestra.html', sample=data, count=len(data))


@public_bp.route("/stats")
def stats_page():
    from datetime import datetime, timedelta
    from sqlalchemy import func

    # Estadísticas de datos
    total_personas = Persona.query.count()
    total_fuentes = Persona.query.join(Persona.fuentes).distinct().count()

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    new_today = Persona.query.filter(Persona.created_at >= today).count()

    week_ago = today - timedelta(days=7)
    new_week = Persona.query.filter(Persona.created_at >= week_ago).count()

    # Estadísticas de búsqueda (sin nombres)
    import subprocess
    try:
        # Contar búsquedas (queries con "?q=")
        result = subprocess.run(
            ["grep", "-o", "?q=[^\\s]*", "/var/log/nginx/access.log"],
            capture_output=True,
            text=True,
            timeout=5
        )
        searches = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
    except:
        searches = 0

    stats_data = {
        'total_personas': total_personas,
        'total_fuentes': total_fuentes,
        'nuevas_hoy': new_today,
        'nuevas_semana': new_week,
        'total_searches': searches,
    }

    return render_template('stats.html', stats=stats_data)
