import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# SECRET_KEY values that were committed to the repository at some point and are
# therefore public knowledge. create_app() refuses to boot in production with
# any of these.
INSECURE_SECRET_KEYS = {
    'fallback-secret-key',
    'your_secure_secret_key_change_this',
    'your_secure_secret_key_change_this_in_production',
    # El relleno que trae .env.production.template. Faltaba, y el template es
    # justamente lo que deploy.sh copia a .env en el servidor: quien desplegara
    # sin editar esta clave arrancaba en produccion con una clave que esta
    # publicada en el repositorio, y esta defensa no lo detectaba.
    'generar-una-clave-nueva-y-unica',
}

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///laboratorios.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Environment detection
    ENVIRONMENT = os.environ.get('FLASK_ENV', 'development')
    IS_PRODUCTION = ENVIRONMENT == 'production'
    
    # El subdirectorio del host donde Apache sirve la aplicación. Flask exige
    # una cadena: con None revienta al construir URLs ('NoneType' has no
    # attribute 'lstrip'), y con cadena vacía la cookie de sesión sale sin Path.
    # '/' es el valor neutro para desarrollo, que corre en la raíz.
    APPLICATION_ROOT = (os.environ.get('APPLICATION_ROOT')
                        or ('/laboratorios-crub' if IS_PRODUCTION else '/'))

    # Server configuration
    SERVER_NAME = os.environ.get('SERVER_NAME', None)
    PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME', 'https' if IS_PRODUCTION else 'http')
    
    # Session cookie hardening (overridden with stricter values in production)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = IS_PRODUCTION

    # Tope duro de la sesión, se siga usando o no. Sin esto una pestaña abierta
    # quedaría autenticada para siempre, porque la cookie se renueva sola.
    SESION_HORAS = int(os.environ.get('SESION_HORAS', '12'))

    # Freno a los intentos por fuerza bruta: cuántos fallos seguidos desde una
    # misma IP antes de hacer esperar, y cuánto.
    INTENTOS_MAX = int(os.environ.get('INTENTOS_MAX', '8'))
    ESPERA_SEGUNDOS = int(os.environ.get('ESPERA_SEGUNDOS', '300'))
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = os.environ.get('LOG_DIR', 'logs')
    
    # Keycloak Configuration - Updated for v26
    # Note: Keycloak v26 changed URL structure from /auth to /keycloak
    KEYCLOAK_SERVER_URL = os.environ.get('KEYCLOAK_SERVER_URL', 'https://huayca.crub.uncoma.edu.ar/keycloak/')
    KEYCLOAK_REALM = os.environ.get('KEYCLOAK_REALM', 'CRUB')
    KEYCLOAK_CLIENT_ID = os.environ.get('KEYCLOAK_CLIENT_ID', 'laboratorios-crub-dev')
    KEYCLOAK_CLIENT_SECRET = os.environ.get('KEYCLOAK_CLIENT_SECRET', '')

    # Sólo ponerlo en false para probar contra un Keycloak con certificado propio.
    KEYCLOAK_VERIFY_SSL = os.environ.get('KEYCLOAK_VERIFY_SSL', 'true').lower() == 'true'

    # Restablecer la contraseña lo resuelven las pantallas de cuenta de Huayca,
    # que ya existen y sirven a todas las aplicaciones del CRUB. Esta aplicación
    # no toca contraseñas: sólo manda a la persona allá.
    URL_RESET_PASSWORD = os.environ.get(
        'URL_RESET_PASSWORD',
        'https://huayca.crub.uncoma.edu.ar/quintral/reset-password')

    # Role mapping
    KEYCLOAK_ADMIN_ROLE = os.environ.get('KEYCLOAK_ADMIN_ROLE', 'app_admin')
    KEYCLOAK_TECNICO_ROLE = os.environ.get('KEYCLOAK_TECNICO_ROLE', 'laboratorista')

    # Debug configuration
    KEYCLOAK_DEBUG = os.environ.get('KEYCLOAK_DEBUG', 'false').lower() == 'true'
    BROWSER_DEBUG = os.environ.get('BROWSER_DEBUG', 'false').lower() == 'true'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    ENVIRONMENT = 'development'
    IS_PRODUCTION = False
    APPLICATION_ROOT = '/'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    ENVIRONMENT = 'production'
    IS_PRODUCTION = True
    APPLICATION_ROOT = '/laboratorios-crub'
    
    # Production-specific settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'