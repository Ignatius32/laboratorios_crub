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

# Debug: Print critical environment variables (remove in production)
print(f"[WSGI] FLASK_ENV: {os.environ.get('FLASK_ENV')}")
print(f"[WSGI] KEYCLOAK_SERVER_URL: {os.environ.get('KEYCLOAK_SERVER_URL')}")
print(f"[WSGI] KEYCLOAK_CLIENT_ID: {os.environ.get('KEYCLOAK_CLIENT_ID')}")
print(f"[WSGI] APPLICATION_ROOT: {os.environ.get('APPLICATION_ROOT')}")

from app import create_app

# Create the application instance with default config (will load from environment)
application = create_app()

if __name__ == "__main__":
    application.run()
