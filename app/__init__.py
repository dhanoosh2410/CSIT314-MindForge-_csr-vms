# BOUNDARY: Flask app factory and blueprint registration
from flask import Flask, request, redirect, url_for, flash, session
from .entity.models import db, seed_database
import os
from .boundary.routes import boundary_bp

def create_app(test_config=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-key-change-me'
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        db_path = os.path.join(app.instance_path, 'csr_vms.db')
        try:
            if not os.path.exists(db_path):
                open(db_path, 'a').close()
        except Exception:
            pass
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ENTITY: bind SQLAlchemy
    db.init_app(app)

    # BOUNDARY: register routes
    app.register_blueprint(boundary_bp)

    # Global authentication: require login for all routes except allowed endpoints
    @app.before_request
    def require_login():
        # Endpoints that don't require authentication
        exempt_endpoints = {
            'boundary.home',
            'boundary.login',
            'boundary.logout',
        }
        endpoint = request.endpoint
        # If no endpoint (static file or other), allow
        if endpoint is None:
            return
        # Allow static files and exempt endpoints
        if endpoint.startswith('static') or endpoint in exempt_endpoints:
            return
        # Require session user_id for everything else
        if not session.get('user_id'):
            flash('Please log in to access that page.')
            return redirect(url_for('boundary.home'))

    # Create tables + seed on first run
    with app.app_context():
        db.create_all()
        seed_database()

    return app