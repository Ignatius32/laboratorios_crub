#!/usr/bin/env python3
"""
WSGI application entry point for Apache deployment
"""
import os
import sys
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_dir))

# Explicitly load environment variables from .env file
# This ensures Apache/mod_wsgi gets the same environment as command line
from dotenv import load_dotenv
env_file = project_dir / '.env'
if env_file.exists():
    load_dotenv(env_file)
    print(f"[WSGI] Loaded environment from: {env_file}")
else:
    print(f"[WSGI] WARNING: .env file not found at: {env_file}")

# Set fallback environment variables for production
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('APPLICATION_ROOT', '/laboratorios-crub')

from app import create_app
from config import Config, DevelopmentConfig, ProductionConfig

# Select the configuration class explicitly. Calling create_app() without
# arguments falls back to the base Config, which does NOT set
# SESSION_COOKIE_SECURE / HTTPONLY / SAMESITE.
env = os.environ.get('FLASK_ENV', 'production')
if env == 'development':
    config_class = DevelopmentConfig
elif env == 'production':
    config_class = ProductionConfig
else:
    config_class = Config

print(f"[WSGI] FLASK_ENV: {env} -> {config_class.__name__}")

application = create_app(config_class)

if __name__ == "__main__":
    application.run()
