from datetime import datetime
from extensions import db

persona_fuente = db.Table(
    "persona_fuente",
    db.Column("persona_id", db.Integer, db.ForeignKey("persona.id"), primary_key=True),
    db.Column("fuente_id",  db.Integer, db.ForeignKey("fuente.id"),  primary_key=True),
)


class Persona(db.Model):
    __tablename__ = "persona"

    id         = db.Column(db.Integer, primary_key=True)
    nombre     = db.Column(db.String(100), nullable=False)
    apellido   = db.Column(db.String(100), nullable=False)
    notas      = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
