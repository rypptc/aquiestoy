from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from extensions import db
from models import User, Submission
import csv
from io import StringIO

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if not email or not password:
            return render_template('register.html', error='Email y contraseña requeridos'), 400
        
        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='Email ya existe'), 400
        
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        return redirect(url_for('auth.upload'))
    
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return render_template('login.html', error='Email o contraseña incorrectos'), 401
        
        session['user_id'] = user.id
        return redirect(url_for('auth.upload'))
    
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('public.index'))


@auth_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        fuente_url = request.form.get('fuente_url', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        csv_file = request.files.get('csv_file')
        
        if not fuente_url or not csv_file:
            return render_template('upload.html', error='Fuente y CSV requeridos'), 400
        
        try:
            csv_content = csv_file.read().decode('utf-8')

            # Validar CSV: debe tener al menos nombre y apellido
            reader = csv.DictReader(StringIO(csv_content))
            if not reader.fieldnames or 'nombre' not in reader.fieldnames or 'apellido' not in reader.fieldnames:
                return render_template('upload.html', error='CSV debe tener columnas "nombre" y "apellido"'), 400

            # Contar filas
            rows = list(reader)
            if not rows:
                return render_template('upload.html', error='CSV está vacío'), 400

        except Exception as e:
            return render_template('upload.html', error=f'Error al leer CSV: {str(e)}'), 400
        
        # Guardar submission
        submission = Submission(
            user_id=session['user_id'],
            fuente_url=fuente_url,
            descripcion=descripcion,
            csv_data=csv_content,
            estado='pendiente'
        )
        db.session.add(submission)
        db.session.commit()
        
        return render_template('upload_success.html', filas=len(rows))
    
    return render_template('upload.html')


@auth_bp.route('/admin')
def admin():
    # TODO: Agregar verificación de admin
    submissions = Submission.query.filter_by(estado='pendiente').all()
    return render_template('admin.html', submissions=submissions)


@auth_bp.route('/admin/aprobar/<int:submission_id>', methods=['POST'])
def aprobar_submission(submission_id):
    # TODO: Verificar que es admin
    submission = Submission.query.get_or_404(submission_id)

    # Parsear CSV e insertar en BD
    reader = csv.DictReader(StringIO(submission.csv_data))

    # Crear fuente
    from models import Fuente, Persona
    fuente = Fuente(
        url=submission.fuente_url,
        descripcion=submission.descripcion
    )
    db.session.add(fuente)
    db.session.flush()

    # Crear personas
    for row in reader:
        nombre = row.get('nombre', '').strip()
        apellido = row.get('apellido', '').strip()

        # Tomar todas las columnas excepto nombre y apellido como notas
        notas_parts = []
        for col in reader.fieldnames:
            if col not in ['nombre', 'apellido'] and row.get(col, '').strip():
                notas_parts.append(row[col].strip())
        notas = ' | '.join(notas_parts) if notas_parts else ''

        if nombre and apellido:
            persona = Persona(
                nombre=nombre,
                apellido=apellido,
                notas=notas
            )
            db.session.add(persona)
            db.session.flush()
            persona.fuentes.append(fuente)

    submission.estado = 'aprobado'
    db.session.commit()

    return redirect(url_for('auth.admin'))


@auth_bp.route('/admin/rechazar/<int:submission_id>', methods=['POST'])
def rechazar_submission(submission_id):
    # TODO: Verificar que es admin
    submission = Submission.query.get_or_404(submission_id)
    submission.estado = 'rechazado'
    db.session.commit()
    
    return redirect(url_for('auth.admin'))
