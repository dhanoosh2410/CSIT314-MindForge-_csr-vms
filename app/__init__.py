
# BOUNDARY: Flask app factory and blueprint registration
from flask import Flask
from .entity.models import db, seed_database
from .boundary.routes import boundary_bp

def create_app(test_config=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-key-change-me'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///csr_vms.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ENTITY: bind SQLAlchemy
    db.init_app(app)

    # BOUNDARY: register routes
    app.register_blueprint(boundary_bp)

    # Create tables + seed on first run
    with app.app_context():
        db.create_all()
        seed_database()

    return app
