#!/usr/bin/env python3
"""
Test Flask app configuration loading in production environment
"""

import os
import sys

# Add the application directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_flask_config():
    """Test Flask configuration loading"""
    
    print("=" * 60)
    print("FLASK CONFIGURATION TEST")
    print("=" * 60)
    
    try:
        from app import create_app
        
        # Create app
        app = create_app()
        
        with app.app_context():
            print("✅ Flask app created successfully")
            
            # Print critical configuration values
            critical_configs = [
                'FLASK_ENV',
                'APPLICATION_ROOT',
                'KEYCLOAK_SERVER_URL',
                'KEYCLOAK_REALM',
                'KEYCLOAK_CLIENT_ID',
                'KEYCLOAK_CLIENT_SECRET',
                'KEYCLOAK_REDIRECT_URI',
                'KEYCLOAK_POST_LOGOUT_REDIRECT_URI',
                'KEYCLOAK_DEBUG',
                'BROWSER_DEBUG'
            ]
            
            print("\n=== Flask App Configuration ===")
            for config in critical_configs:
                value = app.config.get(config)
                if value is not None:
                    if 'SECRET' in config:
                        print(f"✅ {config}: ***{str(value)[-4:]}")
                    else:
                        print(f"✅ {config}: {value}")
                else:
                    print(f"❌ {config}: NOT SET")
            
            # Test Keycloak OIDC import and initialization
            print("\n=== Keycloak OIDC Status ===")
            try:
                from app.integrations.keycloak_oidc import keycloak_oidc
                
                print(f"keycloak_oidc exists: {keycloak_oidc is not None}")
                print(f"oauth exists: {keycloak_oidc.oauth is not None if keycloak_oidc else False}")
                print(f"keycloak client exists: {keycloak_oidc.keycloak is not None if keycloak_oidc else False}")
                
                if keycloak_oidc and keycloak_oidc.keycloak:
                    print(f"keycloak client type: {type(keycloak_oidc.keycloak)}")
                    print(f"has authorize_redirect: {hasattr(keycloak_oidc.keycloak, 'authorize_redirect')}")
                
            except Exception as e:
                print(f"❌ Error checking Keycloak OIDC: {e}")
            
            print("\n" + "=" * 60)
            print("Configuration test completed")
            
    except Exception as e:
        print(f"❌ Error creating Flask app: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_flask_config()
