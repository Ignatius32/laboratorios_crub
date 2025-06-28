#!/usr/bin/env python3
"""
Debug script to test the actual Keycloak callback handling in Flask app
This will help identify issues in the token exchange process
"""
import os
import sys
from flask import Flask, request, session
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.production')

# Add app to Python path
sys.path.append('/var/www/laboratorios-crub')

from app import create_app
from app.integrations.keycloak_oidc import keycloak_oidc

def test_callback_handling():
    """Test the actual callback handling process"""
    print("Keycloak Callback Debug")
    print("=" * 50)
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        print(f"✅ Flask app context created")
        print(f"  Server name: {app.config.get('SERVER_NAME', 'Not set')}")
        print(f"  Application root: {app.config.get('APPLICATION_ROOT', 'Not set')}")
        print(f"  Preferred URL scheme: {app.config.get('PREFERRED_URL_SCHEME', 'Not set')}")
        
        # Test Keycloak OIDC configuration in app context
        print(f"\n=== Keycloak OIDC Configuration ===")
        print(f"  OAuth instance: {'✅ Available' if keycloak_oidc.oauth else '❌ Missing'}")
        print(f"  Keycloak client: {'✅ Available' if keycloak_oidc.keycloak else '❌ Missing'}")
        
        if keycloak_oidc.keycloak:
            # Test the server metadata URL that authlib uses
            try:
                metadata_url = keycloak_oidc.keycloak.server_metadata_url
                print(f"  Server metadata URL: {metadata_url}")
                
                # Try to load server metadata
                server_metadata = keycloak_oidc.keycloak.load_server_metadata()
                if server_metadata:
                    print(f"  ✅ Server metadata loaded successfully")
                    print(f"    Issuer: {server_metadata.get('issuer', 'Not found')}")
                    print(f"    Token endpoint: {server_metadata.get('token_endpoint', 'Not found')}")
                    print(f"    Authorization endpoint: {server_metadata.get('authorization_endpoint', 'Not found')}")
                    print(f"    Userinfo endpoint: {server_metadata.get('userinfo_endpoint', 'Not found')}")
                else:
                    print(f"  ❌ Failed to load server metadata")
                    
            except Exception as e:
                print(f"  ❌ Error loading server metadata: {e}")
        
        # Test creating authorization URL
        print(f"\n=== Authorization URL Test ===")
        try:
            with app.test_request_context():
                auth_response = keycloak_oidc.authorize_redirect()
                if hasattr(auth_response, 'location'):
                    print(f"  ✅ Authorization URL generated")
                    print(f"    Location: {auth_response.location}")
                else:
                    print(f"  ❌ Failed to generate authorization URL")
                    print(f"    Response: {auth_response}")
        except Exception as e:
            print(f"  ❌ Error generating authorization URL: {e}")
        
        # Test token exchange simulation
        print(f"\n=== Token Exchange Simulation ===")
        print("Note: This would normally require a real authorization code from Keycloak")
        print("Testing the token exchange method availability...")
        
        try:
            # Test if the method exists and is callable
            if hasattr(keycloak_oidc, 'authorize_access_token'):
                print("  ✅ authorize_access_token method available")
            else:
                print("  ❌ authorize_access_token method not found")
                
            if hasattr(keycloak_oidc, 'get_user_info'):
                print("  ✅ get_user_info method available")
            else:
                print("  ❌ get_user_info method not found")
                
        except Exception as e:
            print(f"  ❌ Error checking token exchange methods: {e}")

def test_session_configuration():
    """Test session configuration that might affect OAuth state"""
    print(f"\n=== Session Configuration Debug ===")
    
    app = create_app()
    
    with app.app_context():
        print(f"  Session configuration:")
        print(f"    SESSION_TYPE: {app.config.get('SESSION_TYPE', 'Not set')}")
        print(f"    SESSION_PERMANENT: {app.config.get('SESSION_PERMANENT', 'Not set')}")
        print(f"    SESSION_USE_SIGNER: {app.config.get('SESSION_USE_SIGNER', 'Not set')}")
        print(f"    SESSION_KEY_PREFIX: {app.config.get('SESSION_KEY_PREFIX', 'Not set')}")
        print(f"    SECRET_KEY: {'✅ Set' if app.config.get('SECRET_KEY') else '❌ Missing'}")
        
        # Test session functionality
        with app.test_request_context():
            try:
                session['test'] = 'value'
                retrieved = session.get('test')
                if retrieved == 'value':
                    print(f"  ✅ Session storage working")
                else:
                    print(f"  ❌ Session storage not working")
            except Exception as e:
                print(f"  ❌ Session error: {e}")

def check_common_issues():
    """Check for common OAuth/OIDC issues"""
    print(f"\n=== Common Issues Check ===")
    
    # Check URL configuration
    server_url = os.getenv('KEYCLOAK_SERVER_URL', '')
    redirect_uri = os.getenv('KEYCLOAK_REDIRECT_URI', '')
    
    print(f"URL Configuration:")
    print(f"  Server URL ends with /: {'✅ Yes' if server_url.endswith('/') else '❌ No (should end with /)'}")
    print(f"  Redirect URI uses HTTPS: {'✅ Yes' if redirect_uri.startswith('https://') else '❌ No'}")
    
    # Check for trailing slashes consistency
    if server_url.endswith('/') and not server_url.endswith('auth/'):
        print(f"  ⚠️  Warning: Server URL ends with / but not auth/ - check if this is correct")
    
    # Check environment variables
    required_vars = [
        'KEYCLOAK_SERVER_URL',
        'KEYCLOAK_REALM',
        'KEYCLOAK_CLIENT_ID',
        'KEYCLOAK_CLIENT_SECRET',
        'KEYCLOAK_REDIRECT_URI',
        'SECRET_KEY'
    ]
    
    print(f"\nRequired Environment Variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"  {var}: ✅ Set ({'***' + value[-4:] if 'SECRET' in var or 'PASSWORD' in var else value})")
        else:
            print(f"  {var}: ❌ Missing")

def test_error_logging():
    """Test if error logging is working properly"""
    print(f"\n=== Error Logging Test ===")
    
    try:
        from app.utils.logging_config import get_security_logger
        logger = get_security_logger()
        logger.info("Test log message from debug script", 
                   operation="debug_test", 
                   component="debug_script")
        print(f"  ✅ Security logger working")
        
        # Check if log files exist and are writable
        log_dir = os.getenv('LOG_DIR', '/var/www/laboratorios-crub/logs')
        security_log = os.path.join(log_dir, 'security_structured.log')
        
        if os.path.exists(security_log):
            print(f"  ✅ Security log file exists: {security_log}")
            if os.access(security_log, os.W_OK):
                print(f"  ✅ Security log file is writable")
            else:
                print(f"  ❌ Security log file is not writable")
        else:
            print(f"  ❌ Security log file does not exist: {security_log}")
            
    except Exception as e:
        print(f"  ❌ Error testing logger: {e}")

if __name__ == "__main__":
    test_callback_handling()
    test_session_configuration()
    check_common_issues()
    test_error_logging()
    
    print("\n" + "=" * 50)
    print("Callback Debug Complete!")
    print("\nNext steps if issues found:")
    print("1. Check the Apache error log: sudo tail -f /var/log/apache2/error.log")
    print("2. Check the application security log: sudo tail -f /var/www/laboratorios-crub/logs/security_structured.log")
    print("3. Test the actual login flow in a browser with developer tools open")
    print("4. Monitor the callback request parameters when authentication fails")
