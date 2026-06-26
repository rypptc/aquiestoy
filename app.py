import os
import re
from flask import Flask
from extensions import db


def ofuscar_ci(text):
    """Obfusca números de cédula en texto"""
    if not text:
        return text

    pattern = r'([VE])?[-.]?(\d{2})[-.]?\d{3}[-.]?\d{3}([-.]?\d{2})'

    def replace_func(match):
        prefix = match.group(1) or ''
        primeros = match.group(2)
        ultimos = match.group(3)

        if prefix:
            return f"{prefix}-{primeros}XXXX{ultimos}"
        else:
            return f"{primeros}XXXX{ultimos}"

    return re.sub(pattern, replace_func, text, flags=re.IGNORECASE)


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
    db_url = os.environ.get("DATABASE_URL", "sqlite:///aquiestoy.db")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.path.join(app.static_folder, "uploads")
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

    db.init_app(app)
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')

    # Agregar filtro Jinja2 para ofuscar CIs
    app.jinja_env.filters['ofuscar_ci'] = ofuscar_ci

    from routes.public import public_bp
    from routes.api import api_bp
    from routes.auth import auth_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
