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
}

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///laboratorios.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Environment detection
    ENVIRONMENT = os.environ.get('FLASK_ENV', 'development')
    IS_PRODUCTION = ENVIRONMENT == 'production'
    
    # Base URL configuration for Apache deployment
    APPLICATION_ROOT = os.environ.get('APPLICATION_ROOT', '/laboratorios-crub' if IS_PRODUCTION else None)
    
    # Server configuration
    SERVER_NAME = os.environ.get('SERVER_NAME', None)
    PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME', 'https' if IS_PRODUCTION else 'http')
    
    # Bootstrap admin password. Only used to seed the initial admin row on an
    # empty database; there is deliberately no default value. If it is unset the
    # seed user is created with an unusable random password and access has to go
    # through Keycloak.
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

    # Session cookie hardening (overridden with stricter values in production)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = IS_PRODUCTION
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = os.environ.get('LOG_DIR', 'logs')
    
    # Keycloak Configuration - Updated for v26
    # Note: Keycloak v26 changed URL structure from /auth to /keycloak
    KEYCLOAK_SERVER_URL = os.environ.get('KEYCLOAK_SERVER_URL', 'https://huayca.crub.uncoma.edu.ar/keycloak/')
    KEYCLOAK_REALM = os.environ.get('KEYCLOAK_REALM', 'CRUB')
    KEYCLOAK_CLIENT_ID = os.environ.get('KEYCLOAK_CLIENT_ID', 'laboratorios-crub-dev')
    KEYCLOAK_CLIENT_SECRET = os.environ.get('KEYCLOAK_CLIENT_SECRET', '')
    KEYCLOAK_REDIRECT_URI = os.environ.get('KEYCLOAK_REDIRECT_URI', '')
    KEYCLOAK_POST_LOGOUT_REDIRECT_URI = os.environ.get('KEYCLOAK_POST_LOGOUT_REDIRECT_URI', '')
    
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
    APPLICATION_ROOT = None
    
    # Override Keycloak URIs for development
    _base_url = "http://127.0.0.1:5000"
    KEYCLOAK_REDIRECT_URI = os.environ.get('KEYCLOAK_REDIRECT_URI', f"{_base_url}/auth/callback")
    KEYCLOAK_POST_LOGOUT_REDIRECT_URI = os.environ.get('KEYCLOAK_POST_LOGOUT_REDIRECT_URI', f"{_base_url}/")


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