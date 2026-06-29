import os
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from extensions import db
from privacy import ofuscar_ci, sanitizar_notas


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

    # Rate limiting (sin límite global)
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[]
    )
    app.limiter = limiter

    # Filtros Jinja2 de saneo: ofuscar_ci (campo cédula) y sanitizar (notas libres)
    app.jinja_env.filters['ofuscar_ci'] = ofuscar_ci
    app.jinja_env.filters['sanitizar'] = sanitizar_notas

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
