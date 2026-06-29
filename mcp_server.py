#!/usr/bin/env python
"""
Aquí Estoy MCP Server

Modo HTTP (producción):
    python mcp_server.py --http
    Claude Code se conecta vía SSH tunnel a http://localhost:8765/mcp

Modo stdio (legacy/debug):
    python mcp_server.py
"""

import json
import sys
import threading
from functools import wraps
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("aquiestoy", host="127.0.0.1", port=8765)

# ---------------------------------------------------------------------------
# Lazy Flask init — loaded on first tool call, not at startup
# ---------------------------------------------------------------------------

_flask_app = None
_TOOL_LOCK = threading.Lock()


def _get_app():
    global _flask_app
    if _flask_app is None:
        from dotenv import load_dotenv
        load_dotenv(BASE_DIR / ".env")
        from app import create_app
        _flask_app = create_app()
    return _flask_app


def _db():
    from extensions import db
    return db


def _db_tool(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        with _TOOL_LOCK:
            with _get_app().app_context():
                return fn(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
@_db_tool
def buscar_persona(q: str) -> str:
    """
    Busca personas por nombre, apellido o cualquier texto en notas.
    Usar antes de crear para detectar duplicados.

    Args:
        q: Texto a buscar.

    Returns:
        JSON array con {id, nombre, apellido, notas}.
    """
    from models import Persona

    like = f"%{q}%"
    personas = Persona.query.filter(
        Persona.nombre.ilike(like) |
        Persona.apellido.ilike(like) |
        Persona.notas.ilike(like)
    ).order_by(Persona.apellido).limit(20).all()

    return json.dumps(
        [{"id": p.id, "nombre": p.nombre, "apellido": p.apellido, "notas": p.notas or ""} for p in personas],
        ensure_ascii=False,
    )


@mcp.tool()
@_db_tool
def crear_fuente(url: str = "", descripcion: str = "", imagen_hash: str = "") -> str:
    """
    Registra una fuente. Si ya existe una con el mismo URL o imagen_hash, devuelve la existente.

    Args:
        url:          Link original (tweet, post, etc.).
        descripcion:  Descripción legible de la fuente.
        imagen_hash:  SHA256 de la imagen (para detectar imágenes duplicadas).

    Returns:
        JSON con {id, creada} — creada=false si ya existía.
    """
    from models import Fuente

    if url:
        existing = Fuente.query.filter_by(url=url).first()
        if existing:
            return json.dumps({"id": existing.id, "creada": False, "razon": "url duplicada"})

    if imagen_hash:
        existing = Fuente.query.filter_by(imagen_hash=imagen_hash).first()
        if existing:
            return json.dumps({"id": existing.id, "creada": False, "razon": "imagen duplicada"})

    f = Fuente(url=url or None, descripcion=descripcion or None, imagen_hash=imagen_hash or None)
    _db().session.add(f)
    _db().session.commit()
    return json.dumps({"id": f.id, "creada": True})


@mcp.tool()
@_db_tool
def crear_persona(nombre: str, apellido: str, notas: str = "", fuente_id: int = 0) -> str:
    """
    Crea una persona y la vincula a una fuente.
    Llamar buscar_persona primero para verificar que no existe.

    Args:
        nombre:    Nombre de la persona.
        apellido:  Apellido de la persona.
        notas:     Texto libre con toda la información disponible.
        fuente_id: ID de la fuente (obtenido de crear_fuente).

    Returns:
        JSON con {id, nombre_completo}.
    """
    from models import Persona, Fuente

    db = _db()
    p = Persona(nombre=nombre, apellido=apellido, notas=notas or None)
    db.session.add(p)
    db.session.flush()

    if fuente_id:
        f = db.session.get(Fuente, fuente_id)
        if f:
            p.fuentes.append(f)

    db.session.commit()
    return json.dumps({"id": p.id, "nombre_completo": p.nombre_completo}, ensure_ascii=False)


@mcp.tool()
@_db_tool
def agregar_fuente_a_persona(persona_id: int, fuente_id: int) -> str:
    """
    Vincula una fuente existente a una persona existente.
    Útil cuando la misma imagen/tweet menciona a alguien ya registrado.

    Args:
        persona_id: ID de la persona.
        fuente_id:  ID de la fuente.

    Returns:
        JSON con {ok}.
    """
    from models import Persona, Fuente

    db = _db()
    p = db.session.get(Persona, persona_id)
    f = db.session.get(Fuente, fuente_id)

    if not p:
        return json.dumps({"ok": False, "error": f"Persona {persona_id} no encontrada"})
    if not f:
        return json.dumps({"ok": False, "error": f"Fuente {fuente_id} no encontrada"})

    if f not in p.fuentes:
        p.fuentes.append(f)
        db.session.commit()

    return json.dumps({"ok": True})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    if "--http" in sys.argv:
        mcp.run(transport="streamable-http")
    else:
        mcp.run()
