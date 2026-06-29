from datetime import datetime
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

persona_fuente = db.Table(
    "persona_fuente",
    db.Column("persona_id", db.Integer, db.ForeignKey("persona.id"), primary_key=True),
    db.Column("fuente_id",  db.Integer, db.ForeignKey("fuente.id"),  primary_key=True),
)


class Persona(db.Model):
    __tablename__ = "persona"

    id           = db.Column(db.Integer, primary_key=True)
    nombre       = db.Column(db.String(100), nullable=False)
    apellido     = db.Column(db.String(100), nullable=False)
    ci           = db.Column(db.String(20))
    edad         = db.Column(db.String(20))
    sexo         = db.Column(db.String(10))
    hospital     = db.Column(db.String(200))
    status       = db.Column(db.String(30), default='Confirmado')
    estado_salud = db.Column(db.String(30))
    num_reportes = db.Column(db.Integer, default=1)
    notas        = db.Column(db.Text)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    fuentes = db.relationship("Fuente", secondary=persona_fuente, back_populates="personas")

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"


class Fuente(db.Model):
    __tablename__ = "fuente"

    id          = db.Column(db.Integer, primary_key=True)
    url         = db.Column(db.String(500))
    imagen_path = db.Column(db.String(300))
    imagen_hash = db.Column(db.String(64), unique=True, nullable=True)
    descripcion = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    personas = db.relationship("Persona", secondary=persona_fuente, back_populates="fuentes")


class User(db.Model):
    __tablename__ = "user"

    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    submissions = db.relationship("Submission", back_populates="user")

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Submission(db.Model):
    __tablename__ = "submission"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    fuente_url = db.Column(db.String(500))
    descripcion = db.Column(db.Text)
    csv_data   = db.Column(db.Text)  # CSV content as text
    estado     = db.Column(db.String(20), default="pendiente")  # pendiente, aprobado, rechazado
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="submissions")
