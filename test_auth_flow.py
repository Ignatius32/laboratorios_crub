#!/usr/bin/env python3
"""
Test the actual user authentication flow step by step
"""
import os
import sys
sys.path.append(os.getcwd())

from dotenv import load_dotenv
from flask import Flask
from app.integrations.keycloak_oidc import KeycloakOIDC
from app.utils.keycloak_auth import login_user_from_keycloak
from app.utils.logging_config import setup_structured_logging
import traceback

def create_mock_token():
    """Create a mock token structure for testing"""
    return {
        'access_token': 'mock_access_token_for_testing',
        'id_token': 'mock_id_token_for_testing',
        'token_type': 'Bearer',
        'expires_in': 3600,
        'refresh_token': 'mock_refresh_token'
    }

def test_user_authentication_flow():
    """Test the complete user authentication flow"""
    print("Testing User Authentication Flow")
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
        'KEYCLOAK_ADMIN_ROLE': os.getenv('KEYCLOAK_ADMIN_ROLE', 'app_admin'),
        'KEYCLOAK_TECNICO_ROLE': os.getenv('KEYCLOAK_TECNICO_ROLE', 'laboratorista'),
    })
    
    # Setup logging
    setup_structured_logging(app)
    
    with app.app_context():
        try:
            # Initialize Keycloak
            keycloak_oidc = KeycloakOIDC()
            keycloak_oidc.init_app(app)
            print("✅ Keycloak OIDC initialized")
            
            # Test token processing with mock token
            print("\n=== Testing Token Processing ===")
            mock_token = create_mock_token()
            
            # Test get_user_info
            try:
                user_info = keycloak_oidc.get_user_info(mock_token)
                print(f"get_user_info result: {user_info}")
                if user_info is None:
                    print("⚠️  get_user_info returned None (expected with mock token)")
                else:
                    print("✅ get_user_info returned data")
            except Exception as e:
                print(f"❌ Error in get_user_info: {e}")
                traceback.print_exc()
            
            # Test get_user_roles
            try:
                user_roles = keycloak_oidc.get_user_roles(mock_token)
                print(f"get_user_roles result: {user_roles}")
                print("✅ get_user_roles completed")
            except Exception as e:
                print(f"❌ Error in get_user_roles: {e}")
                traceback.print_exc()
            
            # Test login_user_from_keycloak
            print("\n=== Testing login_user_from_keycloak ===")
            try:
                result = login_user_from_keycloak(mock_token)
                print(f"login_user_from_keycloak result: {result}")
                if result:
                    print("✅ login_user_from_keycloak completed successfully")
                else:
                    print("⚠️  login_user_from_keycloak returned False")
            except Exception as e:
                print(f"❌ Error in login_user_from_keycloak: {e}")
                print(f"Error type: {type(e).__name__}")
                traceback.print_exc()
                
                # This is likely where our real error is occurring
                print("\n🔍 This error might be the cause of authentication failures!")
                
        except Exception as e:
            print(f"❌ Error during setup: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    test_user_authentication_flow()
