from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from app.models.models import db, Usuario
from app.utils.logging_config import setup_logging
from app.utils.request_logging import setup_request_logging
from config import Config, INSECURE_SECRET_KEYS
import os
import secrets
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

    # Refuse to start in production with a SECRET_KEY that is public knowledge.
    # Signed session cookies and CSRF tokens are forgeable with a known key.
    if app.config.get('IS_PRODUCTION') and app.config.get('SECRET_KEY') in INSECURE_SECRET_KEYS:
        raise RuntimeError(
            "SECRET_KEY is set to a well-known placeholder value. Generate a new "
            "one (python -c \"import secrets; print(secrets.token_urlsafe(64))\") "
            "and set it in the environment before starting in production."
        )

    # Configure APPLICATION_ROOT for Apache deployment
    if app.config.get('APPLICATION_ROOT'):
        app.config['APPLICATION_ROOT'] = app.config['APPLICATION_ROOT']

    # Flask deriva el path de la cookie de sesión de APPLICATION_ROOT. En
    # desarrollo ese valor es None (y en .env viene como cadena vacía), con lo
    # cual la cookie sale sin atributo Path y el navegador la limita al
    # directorio de la petición: se emite en /auth/login y no se envía a
    # /admin ni /tecnicos, de modo que el login nunca persiste. Fijarlo
    # explícitamente cubre tanto el despliegue bajo subruta como el local.
    app.config['SESSION_COOKIE_PATH'] = app.config.get('APPLICATION_ROOT') or '/'

    # Configure server-side session storage to handle large session data.
    # The directory is created with 0700 so other accounts on the host cannot
    # read the Keycloak tokens stored in the session files.
    session_dir = os.path.join(tempfile.gettempdir(), 'flask_sessions')
    os.makedirs(session_dir, mode=0o700, exist_ok=True)
    try:
        os.chmod(session_dir, 0o700)
    except OSError:
        pass
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = session_dir
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
    from flask_wtf.csrf import generate_csrf
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}
    
    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf)
    
    # Initialize database and seed the bootstrap admin user
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
            bootstrap_password = app.config.get('ADMIN_PASSWORD')
            if bootstrap_password:
                admin.set_password(bootstrap_password)
                app.logger.info(
                    "Usuario administrador ADMIN001 creado con la contraseña de ADMIN_PASSWORD"
                )
            else:
                # No bootstrap password configured: create the row with an
                # unusable random password so the account cannot be logged into
                # locally. Admin access comes from Keycloak (app_admin role).
                admin.set_password(secrets.token_urlsafe(64))
                app.logger.warning(
                    "Usuario administrador ADMIN001 creado sin contraseña utilizable "
                    "(ADMIN_PASSWORD no configurada). Acceda con un usuario de "
                    "Keycloak que tenga el rol de administrador."
                )
            db.session.add(admin)
            db.session.commit()

        app.logger.info("Aplicación CRUB inicializada correctamente")
    
    return app