#!/usr/bin/env python3
"""
Debug script to test the complete Keycloak authentication flow
"""
import os
import sys
import requests
from urllib.parse import urlencode, parse_qs, urlparse
import json

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def load_env_file(env_file='.env.production'):
    """Load environment variables from file"""
    env_vars = {}
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"❌ Environment file {env_file} not found")
        return {}
    return env_vars

def test_client_credentials_flow(env_vars):
    """Test client credentials with Keycloak"""
    print("\n=== Testing Client Credentials ===")
    
    token_url = f"{env_vars['KEYCLOAK_SERVER_URL']}/realms/{env_vars['KEYCLOAK_REALM']}/protocol/openid-connect/token"
    
    data = {
        'grant_type': 'client_credentials',
        'client_id': env_vars['KEYCLOAK_CLIENT_ID'],
        'client_secret': env_vars['KEYCLOAK_CLIENT_SECRET']
    }
    
    try:
        response = requests.post(token_url, data=data, timeout=10)
        print(f"Token endpoint: {token_url}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Client credentials are valid")
            token_data = response.json()
            print(f"  Access token received (length: {len(token_data.get('access_token', ''))})")
            print(f"  Token type: {token_data.get('token_type', 'unknown')}")
            return True
        else:
            print("❌ Client credentials failed")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing client credentials: {e}")
        return False

def test_authorization_code_flow(env_vars):
    """Test authorization code flow construction"""
    print("\n=== Testing Authorization Code Flow ===")
    
    auth_url = f"{env_vars['KEYCLOAK_SERVER_URL']}/realms/{env_vars['KEYCLOAK_REALM']}/protocol/openid-connect/auth"
    
    params = {
        'client_id': env_vars['KEYCLOAK_CLIENT_ID'],
        'redirect_uri': env_vars['KEYCLOAK_REDIRECT_URI'],
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': 'test_state_12345'  # Add state parameter
    }
    
    full_auth_url = f"{auth_url}?{urlencode(params)}"
    
    print(f"Authorization URL: {auth_url}")
    print(f"Full auth URL: {full_auth_url}")
    print(f"Client ID: {env_vars['KEYCLOAK_CLIENT_ID']}")
    print(f"Redirect URI: {env_vars['KEYCLOAK_REDIRECT_URI']}")
    
    # Test if the auth endpoint accepts our parameters
    try:
        response = requests.get(full_auth_url, allow_redirects=False, timeout=10)
        print(f"Auth endpoint status: {response.status_code}")
        
        if response.status_code in [200, 302]:
            print("✅ Authorization endpoint accepts our parameters")
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                print(f"  Redirect to: {location[:100]}...")
        else:
            print("❌ Authorization endpoint rejected our parameters")
            print(f"  Response: {response.text[:500]}...")
            
    except Exception as e:
        print(f"❌ Error testing authorization endpoint: {e}")

def test_flask_app_config():
    """Test Flask app configuration"""
    print("\n=== Testing Flask App Configuration ===")
    
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            print("✅ Flask app created successfully")
            
            # Check critical config values
            required_configs = [
                'KEYCLOAK_SERVER_URL',
                'KEYCLOAK_REALM', 
                'KEYCLOAK_CLIENT_ID',
                'KEYCLOAK_CLIENT_SECRET',
                'KEYCLOAK_REDIRECT_URI'
            ]
            
            for config in required_configs:
                value = app.config.get(config)
                if value:
                    # Hide sensitive values
                    display_value = value if 'SECRET' not in config else f"***{value[-4:]}"
                    print(f"  {config}: {display_value}")
                else:
                    print(f"  ❌ {config}: NOT SET")
            
            # Test Keycloak OIDC initialization
            try:
                from app.integrations.keycloak_oidc import keycloak_oidc
                print("✅ Keycloak OIDC integration loaded")
                
                if keycloak_oidc.keycloak:
                    print("✅ Keycloak client initialized")
                else:
                    print("❌ Keycloak client not initialized")
                    
            except Exception as e:
                print(f"❌ Error loading Keycloak OIDC: {e}")
                
    except Exception as e:
        print(f"❌ Error creating Flask app: {e}")
        return False
        
    return True

def test_session_config():
    """Test session configuration"""
    print("\n=== Testing Session Configuration ===")
    
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            session_configs = [
                'SECRET_KEY',
                'SESSION_TYPE',
                'SESSION_PERMANENT',
                'SESSION_USE_SIGNER',
                'SESSION_KEY_PREFIX'
            ]
            
            for config in session_configs:
                value = app.config.get(config)
                if value is not None:
                    # Hide secret key
                    display_value = value if config != 'SECRET_KEY' else f"***{str(value)[-4:]}"
                    print(f"  {config}: {display_value}")
                else:
                    print(f"  {config}: NOT SET")
                    
    except Exception as e:
        print(f"❌ Error checking session config: {e}")

def main():
    print("Keycloak Authentication Flow Debug")
    print("=" * 50)
    
    # Load environment variables
    env_vars = load_env_file()
    if not env_vars:
        print("❌ Could not load environment variables")
        return
    
    print(f"✅ Loaded {len(env_vars)} environment variables")
    
    # Required environment variables
    required_vars = [
        'KEYCLOAK_SERVER_URL',
        'KEYCLOAK_REALM',
        'KEYCLOAK_CLIENT_ID', 
        'KEYCLOAK_CLIENT_SECRET',
        'KEYCLOAK_REDIRECT_URI'
    ]
    
    missing_vars = [var for var in required_vars if var not in env_vars]
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        return
    
    # Set environment variables for Flask app
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print(f"Keycloak Server: {env_vars['KEYCLOAK_SERVER_URL']}")
    print(f"Realm: {env_vars['KEYCLOAK_REALM']}")
    print(f"Client ID: {env_vars['KEYCLOAK_CLIENT_ID']}")
    print(f"Redirect URI: {env_vars['KEYCLOAK_REDIRECT_URI']}")
    
    # Run tests
    test_client_credentials_flow(env_vars)
    test_authorization_code_flow(env_vars)
    test_flask_app_config()
    test_session_config()
    
    print("\n" + "=" * 50)
    print("Debug complete!")
    
    print("\n=== Troubleshooting Recommendations ===")
    print("1. If client credentials fail:")
    print("   - Check client secret in Keycloak admin console")
    print("   - Verify client ID is correct")
    print("   - Ensure client is enabled in Keycloak")
    
    print("\n2. If authorization flow fails:")
    print("   - Check redirect URI matches exactly in Keycloak client config")
    print("   - Verify valid redirect URIs include your callback URL")
    print("   - Check web origins include your domain")
    
    print("\n3. If Flask app config fails:")
    print("   - Check .env.production file is in correct location")
    print("   - Verify all required environment variables are set")
    print("   - Check for any import errors in the Flask app")

if __name__ == "__main__":
    main()
