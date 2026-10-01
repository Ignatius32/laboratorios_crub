from datetime import timedelta

from flask import Flask, flash, redirect, request, url_for
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from app.models.models import db, Usuario
from app.utils.logging_config import setup_logging
from app.utils.request_logging import setup_request_logging
from config import Config, INSECURE_SECRET_KEYS
import os
import tempfile

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, inicie sesión para acceder a esta página.'
login_manager.login_message_category = 'info'

# Todo pide sesión salvo lo que aparece acá. Es al revés de poner un decorador
# en cada vista: si mañana se agrega una pantalla, nace protegida.
SIN_SESION = {'auth.login', 'auth.logout', 'main.index', 'main.about', 'static'}

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

    # Flask deriva el path de la cookie de sesión de APPLICATION_ROOT, y si no
    # hay valor la cookie sale sin atributo Path: el navegador la limita al
    # directorio de la petición, se emite en /auth/login y no se envía a /admin
    # ni /tecnicos, de modo que el login nunca persiste. Config ya garantiza que
    # APPLICATION_ROOT sea una cadena ('/' en desarrollo), así que acá alcanza
    # con copiarlo.
    app.config['SESSION_COOKIE_PATH'] = app.config['APPLICATION_ROOT']

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
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'laboratorios_crub:'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(
        hours=app.config['SESION_HORAS'])

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
    
    # El cliente de administración de Keycloak, que usa el panel para traerse
    # el padrón de laboratoristas. El ingreso no pasa por acá: va directo al
    # endpoint de token (app/utils/keycloak_auth.py).
    from app.integrations.keycloak_admin_client import keycloak_admin
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

    # Páginas de error propias, en vez de las crudas de Werkzeug.
    from app.routes.errors import register_error_handlers
    register_error_handlers(app)

    # Add template context processors
    from datetime import datetime
    from flask_wtf.csrf import generate_csrf
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}
    
    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf)

    # Nada de sembrar un administrador: no hay contraseñas locales que sembrar.
    # El primer administrador es la primera persona que entra con un usuario que
    # esté en USUARIOS_AUTORIZADOS y tenga el rol de administrador en el realm.
    @app.before_request
    def exigir_sesion():
        from app.utils import keycloak_auth

        if request.endpoint in SIN_SESION:
            return None
        if current_user.is_authenticated and not keycloak_auth.sesion_vencida():
            return None

        vencida = current_user.is_authenticated
        keycloak_auth.cerrar_sesion()
        # Un endpoint None es una URL que no existe: dejar que siga y conteste
        # 404 en vez de mandar al formulario de ingreso.
        if request.endpoint is None:
            return None
        flash('Su sesión expiró, vuelva a ingresar.' if vencida
              else 'Por favor, inicie sesión para acceder a esta página.', 'info')
        return redirect(url_for('auth.login', next=request.full_path))

    with app.app_context():
        db.create_all()
        app.logger.info("Aplicación CRUB inicializada correctamente")

    return app