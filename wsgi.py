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

# Set environment variables for production
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('APPLICATION_ROOT', '/laboratorios-crub')

from app import create_app
from config import ProductionConfig

# Create the application instance
application = create_app(ProductionConfig)

if __name__ == "__main__":
    application.run()
