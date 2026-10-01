#!/usr/bin/env python3
"""
Simple web endpoint to test environment variables in web context
"""

import os
import sys
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_dir))

from flask import Flask, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

@app.route('/test-env')
def test_env():
    """Test endpoint to check environment variables"""
    
    env_vars = {
        'FLASK_ENV': os.environ.get('FLASK_ENV'),
        'KEYCLOAK_SERVER_URL': os.environ.get('KEYCLOAK_SERVER_URL'),
        'KEYCLOAK_REALM': os.environ.get('KEYCLOAK_REALM'),
        'KEYCLOAK_CLIENT_ID': os.environ.get('KEYCLOAK_CLIENT_ID'),
        'KEYCLOAK_CLIENT_SECRET': '***' + os.environ.get('KEYCLOAK_CLIENT_SECRET', '')[-4:] if os.environ.get('KEYCLOAK_CLIENT_SECRET') else None,
        'KEYCLOAK_REDIRECT_URI': os.environ.get('KEYCLOAK_REDIRECT_URI'),
        'KEYCLOAK_DEBUG': os.environ.get('KEYCLOAK_DEBUG'),
        'APPLICATION_ROOT': os.environ.get('APPLICATION_ROOT'),
        'working_directory': os.getcwd(),
        'env_file_exists': os.path.exists('.env'),
        'env_file_path': os.path.abspath('.env')
    }
    
    return jsonify(env_vars)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
