#!/usr/bin/env python3
"""
Debug script to test Keycloak configuration
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== Keycloak Configuration Debug ===")
print(f"KEYCLOAK_SERVER_URL: {os.environ.get('KEYCLOAK_SERVER_URL')}")
print(f"KEYCLOAK_REALM: {os.environ.get('KEYCLOAK_REALM')}")
print(f"KEYCLOAK_CLIENT_ID: {os.environ.get('KEYCLOAK_CLIENT_ID')}")
print(f"KEYCLOAK_CLIENT_SECRET: {'***' if os.environ.get('KEYCLOAK_CLIENT_SECRET') else 'Not set'}")
print(f"KEYCLOAK_REDIRECT_URI: {os.environ.get('KEYCLOAK_REDIRECT_URI')}")
print()

# Test importing the Flask app
try:
    from app import create_app
    print("✓ Successfully imported Flask app")
    
    app = create_app()
    print("✓ Successfully created Flask app")
    
    with app.app_context():
        print("\n=== App Configuration ===")
        print(f"KEYCLOAK_CLIENT_ID: {app.config.get('KEYCLOAK_CLIENT_ID')}")
        print(f"KEYCLOAK_SERVER_URL: {app.config.get('KEYCLOAK_SERVER_URL')}")
        print(f"KEYCLOAK_REALM: {app.config.get('KEYCLOAK_REALM')}")
        print(f"KEYCLOAK_REDIRECT_URI: {app.config.get('KEYCLOAK_REDIRECT_URI')}")
        
        # Test Keycloak OIDC initialization
        try:
            from app.integrations.keycloak_oidc import keycloak_oidc
            print("✓ Successfully imported keycloak_oidc")
            
            # Try to access the keycloak client
            if hasattr(keycloak_oidc, 'keycloak') and keycloak_oidc.keycloak:
                print("✓ Keycloak client is initialized")
                
                # Test metadata URL
                metadata_url = f"{app.config['KEYCLOAK_SERVER_URL']}realms/{app.config['KEYCLOAK_REALM']}/.well-known/openid-configuration"
                print(f"Metadata URL: {metadata_url}")
                
                # Try to get authorization URL
                try:
                    redirect_uri = app.config['KEYCLOAK_REDIRECT_URI']
                    print(f"Redirect URI: {redirect_uri}")
                    
                    # This might fail, but let's see what happens
                    auth_url = keycloak_oidc.keycloak.create_authorization_url(redirect_uri)
                    print(f"✓ Successfully created authorization URL: {auth_url['url'][:100]}...")
                    
                except Exception as e:
                    print(f"✗ Failed to create authorization URL: {e}")
                    print(f"Error type: {type(e).__name__}")
                    
            else:
                print("✗ Keycloak client is not initialized")
                
        except Exception as e:
            print(f"✗ Failed to import or test keycloak_oidc: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            
except Exception as e:
    print(f"✗ Failed to import or create Flask app: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()

print("\n=== Debug Complete ===")
