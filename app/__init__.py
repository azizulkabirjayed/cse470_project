# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bracu_cafe.db'  # Adjust as needed
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    CSRFProtect(app)

    # Import models after db initialization to avoid circular imports
    from app.models import models

    # Create database tables
    with app.app_context():
        db.create_all()

    # Register blueprints
    from app.controllers.routes import routes_bp
    app.register_blueprint(routes_bp)

    return app