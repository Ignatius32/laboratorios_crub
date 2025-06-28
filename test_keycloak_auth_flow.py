#!/usr/bin/env python3
"""
Test Keycloak Authentication Flow
Simulates the authentication process to identify issues
"""

import os
import sys

# Add the application directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from flask import url_for

def test_keycloak_initialization():
    """Test Keycloak initialization and configuration"""
    
    print("=" * 60)
    print("KEYCLOAK INITIALIZATION TEST")
    print("=" * 60)
    
    try:
        # Create Flask app
        app = create_app()
        
        with app.app_context():
            print("✅ Flask app created successfully")
            
            # Test configuration
            print("\n=== Configuration Test ===")
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
                    if 'SECRET' in config:
                        print(f"✅ {config}: ***{value[-4:]}")
                    else:
                        print(f"✅ {config}: {value}")
                else:
                    print(f"❌ {config}: NOT SET")
            
            # Test Keycloak OIDC initialization
            print("\n=== Keycloak OIDC Test ===")
            try:
                from app.integrations.keycloak_oidc import keycloak_oidc
                
                if keycloak_oidc:
                    print("✅ keycloak_oidc object exists")
                    
                    if hasattr(keycloak_oidc, 'keycloak') and keycloak_oidc.keycloak:
                        print("✅ keycloak client is initialized")
                        
                        # Test authorize_redirect method
                        try:
                            # This will fail because we're not in a request context
                            # But it will tell us if the method exists and is callable
                            if hasattr(keycloak_oidc.keycloak, 'authorize_redirect'):
                                print("✅ authorize_redirect method available")
                            else:
                                print("❌ authorize_redirect method not available")
                                
                        except Exception as e:
                            if "Working outside of request context" in str(e):
                                print("✅ authorize_redirect method works (request context needed)")
                            else:
                                print(f"❌ authorize_redirect error: {e}")
                    else:
                        print("❌ keycloak client is not initialized")
                        print("   Check if Keycloak server is accessible")
                        
                else:
                    print("❌ keycloak_oidc object is None")
                    
            except ImportError as e:
                print(f"❌ Failed to import keycloak_oidc: {e}")
            except Exception as e:
                print(f"❌ Error testing keycloak_oidc: {e}")
            
            # Test URL generation
            print("\n=== URL Generation Test ===")
            try:
                with app.test_request_context():
                    keycloak_login_url = url_for('auth.keycloak_login')
                    print(f"✅ Keycloak login URL: {keycloak_login_url}")
                    
                    callback_url = url_for('auth.keycloak_callback')
                    print(f"✅ Callback URL: {callback_url}")
                    
            except Exception as e:
                print(f"❌ URL generation error: {e}")
            
            # Test manual authorization URL construction
            print("\n=== Manual Auth URL Test ===")
            try:
                server_url = app.config['KEYCLOAK_SERVER_URL']
                realm = app.config['KEYCLOAK_REALM']
                client_id = app.config['KEYCLOAK_CLIENT_ID']
                redirect_uri = app.config['KEYCLOAK_REDIRECT_URI']
                
                if not server_url.endswith('/'):
                    server_url += '/'
                
                auth_url = f"{server_url}realms/{realm}/protocol/openid-connect/auth"
                
                from urllib.parse import urlencode
                params = {
                    'response_type': 'code',
                    'client_id': client_id,
                    'redirect_uri': redirect_uri,
                    'scope': 'openid email profile',
                    'state': 'test-state',
                    'nonce': 'test-nonce'
                }
                
                full_auth_url = f"{auth_url}?{urlencode(params)}"
                print(f"✅ Manual auth URL constructed:")
                print(f"   {full_auth_url}")
                
            except Exception as e:
                print(f"❌ Manual auth URL construction failed: {e}")
            
    except Exception as e:
        print(f"❌ Failed to create Flask app: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Test completed. Check results above for any issues.")

if __name__ == "__main__":
    test_keycloak_initialization()
