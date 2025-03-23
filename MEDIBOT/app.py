import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_jwt_extended import JWTManager
from flask_login import LoginManager

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)

# Configure the app from config.py
app.config.from_object('config.Config')

# Set secret key from environment variable
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Initialize JWT
jwt = JWTManager(app)

# Initialize SQLAlchemy with app
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'auth_bp.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Import routes after app is created to avoid circular imports
with app.app_context():
    # First import models to ensure they are registered with SQLAlchemy
    import models

    # Then import and register blueprints
    from routes.auth import auth_bp
    from routes.patient import patient_bp
    from routes.attender import attender_bp
    from routes.hospital import hospital_bp
    from routes.insurance import insurance_bp
    from routes.mental_health import mental_health_bp
    from routes.google_auth import google_auth as google_auth_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp, url_prefix='/patient')
    app.register_blueprint(attender_bp, url_prefix='/attender')
    app.register_blueprint(hospital_bp, url_prefix='/hospital')
    app.register_blueprint(insurance_bp, url_prefix='/insurance')
    app.register_blueprint(mental_health_bp, url_prefix='/mental-health')
    app.register_blueprint(google_auth_bp)

    # Create all database tables
    db.create_all()
