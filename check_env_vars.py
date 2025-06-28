#!/usr/bin/env python3
"""
Check environment variables and configuration loading
"""

import os
import sys
from dotenv import load_dotenv

def check_environment_loading():
    """Check how environment variables are being loaded"""
    
    print("=" * 60)
    print("ENVIRONMENT VARIABLE CHECK")
    print("=" * 60)
    
    # Check if .env file exists
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"✅ .env file exists: {os.path.abspath(env_file)}")
    else:
        print(f"❌ .env file not found: {os.path.abspath(env_file)}")
    
    # Load .env file
    print(f"\nLoading .env file...")
    load_dotenv()
    
    # Check critical environment variables
    env_vars = [
        'FLASK_ENV',
        'KEYCLOAK_SERVER_URL',
        'KEYCLOAK_REALM',
        'KEYCLOAK_CLIENT_ID',
        'KEYCLOAK_CLIENT_SECRET',
        'KEYCLOAK_REDIRECT_URI',
        'KEYCLOAK_POST_LOGOUT_REDIRECT_URI',
        'KEYCLOAK_DEBUG',
        'APPLICATION_ROOT'
    ]
    
    print("\n=== Environment Variables ===")
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            if 'SECRET' in var:
                print(f"✅ {var}: ***{value[-4:]}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
    
    # Test Flask config loading
    print("\n=== Flask Config Test ===")
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from config import Config
        
        config = Config()
        
        print(f"KEYCLOAK_SERVER_URL: {config.KEYCLOAK_SERVER_URL}")
        print(f"KEYCLOAK_CLIENT_ID: {config.KEYCLOAK_CLIENT_ID}")
        print(f"KEYCLOAK_REDIRECT_URI: {config.KEYCLOAK_REDIRECT_URI}")
        print(f"KEYCLOAK_DEBUG: {config.KEYCLOAK_DEBUG}")
        print(f"APPLICATION_ROOT: {config.APPLICATION_ROOT}")
        print(f"IS_PRODUCTION: {config.IS_PRODUCTION}")
        
    except Exception as e:
        print(f"❌ Error loading Flask config: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_environment_loading()
