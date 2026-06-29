from flask import Blueprint, request, jsonify, send_file, current_app
from extensions import db
from models import Persona, Fuente
from privacy import sanitizar_notas
from io import StringIO
import csv
import json

api_bp = Blueprint('api', __name__, url_prefix='/api')

# GET /api/personas/buscar?q=juan
@api_bp.route('/personas/buscar', methods=['GET'])
def buscar_personas():
    """
    Busca personas por nombre o apellido.
    
    Parámetros:
        q: string de búsqueda (requerido)
        limit: máximo de resultados (default 50)
    
    Retorna: lista de personas que coinciden
    """
    q = request.args.get('q', '').strip()
    limit = request.args.get('limit', 50, type=int)
    
    if not q or len(q) < 2:
        return jsonify({'error': 'Búsqueda muy corta (mín. 2 caracteres)'}), 400
    
    like_q = f"%{q}%"
    personas = Persona.query.filter(
        db.or_(
            Persona.nombre.ilike(like_q),
            Persona.apellido.ilike(like_q)
        )
    ).limit(limit).all()
    
    resultado = []
    for p in personas:
        resultado.append({
            'id': p.id,
            'nombre': p.nombre,
            'apellido': p.apellido,
            'nombre_completo': p.nombre_completo,
            'fuentes_cantidad': len(p.fuentes)
        })
    
    return jsonify({
        'total': len(resultado),
        'personas': resultado
    })

# GET /api/personas/<id>
@api_bp.route('/personas/<int:persona_id>', methods=['GET'])
def obtener_persona(persona_id):
    """
    Obtiene detalle completo de una persona con TODAS sus fuentes.
    """
    persona = Persona.query.get_or_404(persona_id)
    
    fuentes = []
    for fuente in persona.fuentes:
        fuentes.append({
            'id': fuente.id,
            'url': fuente.url,
            'descripcion': fuente.descripcion,
            'created_at': fuente.created_at.isoformat() if fuente.created_at else None
        })
    
    return jsonify({
        'id': persona.id,
        'nombre': persona.nombre,
        'apellido': persona.apellido,
        'nombre_completo': persona.nombre_completo,
        'notas': sanitizar_notas(persona.notas),
        'created_at': persona.created_at.isoformat() if persona.created_at else None,
        'fuentes': fuentes,
        'fuentes_cantidad': len(fuentes)
    })

# GET /api/personas/export
@api_bp.route('/personas/export', methods=['GET'])
def exportar_personas():
    """
    Exporta todas las personas en CSV.
    Solo autorizado para terremotovenezuela.app (200.50.233.147)
    """
    AUTHORIZED_IPS = ['200.50.233.147', '190.6.8.149']
    client_ip = request.headers.get('X-Real-IP', request.remote_addr)

    if client_ip not in AUTHORIZED_IPS:
        return jsonify({'error': 'Acceso denegado - IP no autorizada'}), 403

    formato = request.args.get('formato', 'csv').lower()
    
    personas = Persona.query.all()
    
    if formato == 'json':
        datos = []
        for p in personas:
            urls = [f.url for f in p.fuentes if f.url]
            datos.append({
                'nombre': p.nombre,
                'apellido': p.apellido,
                'notas': p.notas,
                'fuentes': urls,
                'created_at': p.created_at.isoformat() if p.created_at else None
            })
        return jsonify({'total': len(datos), 'personas': datos})
    
    else:  # CSV
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['nombre', 'apellido', 'notas', 'fuentes'])
        
        for p in personas:
            urls = ' | '.join([f.url for f in p.fuentes if f.url])
            writer.writerow([p.nombre, p.apellido, p.notas or '', urls])
        
        output.seek(0)
        return output.getvalue(), 200, {
            'Content-Disposition': 'attachment; filename=personas.csv',
            'Content-Type': 'text/csv'
        }

# GET /api/stats
@api_bp.route('/stats', methods=['GET'])
def estadisticas():
    """
    Retorna estadísticas rápidas de la base de datos.
    """
    total_personas = Persona.query.count()
    total_fuentes = Fuente.query.count()
    
    # Última persona añadida
    ultima_persona = Persona.query.order_by(Persona.created_at.desc()).first()
    ultima_fuente = Fuente.query.order_by(Fuente.created_at.desc()).first()
    
    return jsonify({
        'total_personas': total_personas,
        'total_fuentes': total_fuentes,
        'ultima_actualizacion': {
            'persona': ultima_persona.created_at.isoformat() if ultima_persona else None,
            'fuente': ultima_fuente.created_at.isoformat() if ultima_fuente else None
        },
        'status': 'operativo'
    })

# GET /api/fuentes
@api_bp.route('/fuentes', methods=['GET'])
def listar_fuentes():
    """
    Lista todas las fuentes disponibles.
    """
    fuentes = Fuente.query.all()
    
    resultado = []
    for f in fuentes:
        resultado.append({
            'id': f.id,
            'url': f.url,
            'descripcion': f.descripcion,
            'personas_cantidad': len(f.personas),
            'created_at': f.created_at.isoformat() if f.created_at else None
        })
    
    return jsonify({
        'total': len(resultado),
        'fuentes': resultado
    })

