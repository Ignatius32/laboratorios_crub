from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from app.models.models import db, Usuario
from app.utils.logging_config import setup_logging
from app.utils.request_logging import setup_request_logging
from config import Config
import os
import tempfile

login_manager = LoginManager()
login_manager.login_view = 'auth.keycloak_login'
login_manager.login_message = 'Por favor, inicie sesión para acceder a esta página.'
login_manager.login_message_category = 'info'

# Initialize CSRF protection
csrf = CSRFProtect()

# Initialize server-side session
sess = Session()

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(user_id)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configure APPLICATION_ROOT for Apache deployment
    if app.config.get('APPLICATION_ROOT'):
        app.config['APPLICATION_ROOT'] = app.config['APPLICATION_ROOT']
    
    # Configure server-side session storage to handle large session data
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(tempfile.gettempdir(), 'flask_sessions')
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'laboratorios_crub:'
    
    # Initialize logging first
    setup_logging(app)
    
    # Initialize request logging middleware
    setup_request_logging(app)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    sess.init_app(app)
    migrate = Migrate(app, db)
    
    # Initialize Keycloak integration
    from app.integrations.keycloak_oidc import keycloak_oidc
    from app.integrations.keycloak_admin_client import keycloak_admin
    keycloak_oidc.init_app(app)
    keycloak_admin.init_app(app)
    
    # Register blueprints
    from app.routes.auth import auth as auth_bp
    from app.routes.admin import admin as admin_bp
    from app.routes.tecnicos import tecnicos as tecnicos_bp
    from app.routes.main import main as main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(tecnicos_bp, url_prefix='/tecnicos')
    app.register_blueprint(main_bp)
    
    # Add template context processors
    from datetime import datetime
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}
    
    # Initialize database and create admin user
    with app.app_context():
        db.create_all()
        # Check if admin user exists
        admin = Usuario.query.filter_by(rol='admin').first()
        if not admin:
            admin = Usuario(
                idUsuario='ADMIN001',
                nombre='Administrador',
                apellido='Sistema',
                email='admin@crub.edu.ar',
                rol='admin'
            )
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin)
            db.session.commit()
            app.logger.info("Usuario administrador creado: ADMIN001")
        
        app.logger.info("Aplicación CRUB inicializada correctamente")
    
    return app