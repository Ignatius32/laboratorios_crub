#!/usr/bin/env python3
"""
Simplified test to pinpoint the exact Keycloak authentication issue
"""
import os
import sys
sys.path.append(os.getcwd())

from dotenv import load_dotenv
from flask import Flask
from app.integrations.keycloak_oidc import KeycloakOIDC
from app.utils.logging_config import setup_structured_logging
import traceback

def test_keycloak_initialization():
    """Test just the Keycloak client initialization"""
    print("Testing Keycloak OIDC Initialization")
    print("=" * 50)
    
    # Load environment
    load_dotenv('.env.production')
    
    # Create minimal Flask app
    app = Flask(__name__)
    app.config.update({
        'SECRET_KEY': os.getenv('SECRET_KEY', 'test_key'),
        'KEYCLOAK_SERVER_URL': os.getenv('KEYCLOAK_SERVER_URL'),
        'KEYCLOAK_REALM': os.getenv('KEYCLOAK_REALM'),
        'KEYCLOAK_CLIENT_ID': os.getenv('KEYCLOAK_CLIENT_ID'),
        'KEYCLOAK_CLIENT_SECRET': os.getenv('KEYCLOAK_CLIENT_SECRET'),
        'KEYCLOAK_REDIRECT_URI': os.getenv('KEYCLOAK_REDIRECT_URI'),
        'KEYCLOAK_POST_LOGOUT_REDIRECT_URI': os.getenv('KEYCLOAK_POST_LOGOUT_REDIRECT_URI'),
    })
    
    # Setup logging
    setup_structured_logging(app)
    
    print(f"Server URL: {app.config['KEYCLOAK_SERVER_URL']}")
    print(f"Realm: {app.config['KEYCLOAK_REALM']}")
    print(f"Client ID: {app.config['KEYCLOAK_CLIENT_ID']}")
    
    with app.app_context():
        try:
            # Test Keycloak initialization
            keycloak_oidc = KeycloakOIDC()
            print("✅ KeycloakOIDC instance created")
            
            # Initialize with app
            keycloak_oidc.init_app(app)
            print("✅ Keycloak client initialized")
            
            # Check if client was registered
            if hasattr(keycloak_oidc, 'keycloak') and keycloak_oidc.keycloak:
                print("✅ OAuth client registered")
                
                # Try to access server metadata
                try:
                    client = keycloak_oidc.keycloak
                    if hasattr(client, 'server_metadata'):
                        metadata = client.server_metadata
                        print(f"✅ Server metadata loaded:")
                        print(f"  - Issuer: {metadata.get('issuer', 'Not found')}")
                        print(f"  - Authorization endpoint: {metadata.get('authorization_endpoint', 'Not found')}")
                        print(f"  - Token endpoint: {metadata.get('token_endpoint', 'Not found')}")
                    else:
                        print("❌ No server_metadata attribute found")
                        print(f"Available attributes: {[attr for attr in dir(client) if not attr.startswith('_')]}")
                        
                except Exception as e:
                    print(f"❌ Error accessing server metadata: {e}")
                    print(f"Error type: {type(e).__name__}")
                    traceback.print_exc()
                
                # Test authorization URL generation
                try:
                    auth_url = keycloak_oidc.authorize_redirect()
                    print(f"✅ Authorization redirect generated")
                    if hasattr(auth_url, 'location'):
                        print(f"  Redirect location: {auth_url.location[:100]}...")
                except Exception as e:
                    print(f"❌ Error generating authorization URL: {e}")
                    traceback.print_exc()
                    
            else:
                print("❌ OAuth client not registered")
                print(f"keycloak_oidc.keycloak = {keycloak_oidc.keycloak}")
                
        except Exception as e:
            print(f"❌ Error during initialization: {e}")
            print(f"Error type: {type(e).__name__}")
            traceback.print_exc()

if __name__ == "__main__":
    test_keycloak_initialization()
