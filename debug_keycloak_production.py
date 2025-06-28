#!/usr/bin/env python3
"""
Production Authentication Debug Script
Tests Keycloak authentication flow in production environment
"""

import os
import sys
import requests
from urllib.parse import urlencode, urlparse, parse_qs
import json
from datetime import datetime

# Add the application directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_keycloak_production():
    """Debug Keycloak configuration in production"""
    
    print("=" * 60)
    print("PRODUCTION KEYCLOAK AUTHENTICATION DEBUG")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Production configuration
    server_url = "https://huayca.crub.uncoma.edu.ar/auth/"
    realm = "CRUB"
    client_id = "laboratorios-crub"
    redirect_uri = "https://huayca.crub.uncoma.edu.ar/laboratorios-crub/auth/callback"
    
    print("=== Production Configuration ===")
    print(f"Server URL: {server_url}")
    print(f"Realm: {realm}")
    print(f"Client ID: {client_id}")
    print(f"Redirect URI: {redirect_uri}")
    print()
    
    # Test 1: Well-known configuration endpoint
    print("=== Test 1: Well-known Configuration ===")
    wellknown_url = f"{server_url}realms/{realm}/.well-known/openid-configuration"
    try:
        response = requests.get(wellknown_url, timeout=10)
        if response.status_code == 200:
            config = response.json()
            print("✅ Well-known configuration accessible")
            print(f"   Authorization endpoint: {config.get('authorization_endpoint')}")
            print(f"   Token endpoint: {config.get('token_endpoint')}")
            print(f"   Userinfo endpoint: {config.get('userinfo_endpoint')}")
            print(f"   Logout endpoint: {config.get('end_session_endpoint')}")
            print(f"   Supported scopes: {config.get('scopes_supported')}")
            print(f"   Supported response types: {config.get('response_types_supported')}")
        else:
            print(f"❌ Well-known configuration not accessible: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Error accessing well-known configuration: {e}")
    print()
    
    # Test 2: Authorization URL construction
    print("=== Test 2: Authorization URL Construction ===")
    try:
        auth_endpoint = f"{server_url}realms/{realm}/protocol/openid-connect/auth"
        auth_params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': 'openid email profile',
            'state': 'test-state-12345',
            'nonce': 'test-nonce-12345'
        }
        
        auth_url = f"{auth_endpoint}?{urlencode(auth_params)}"
        print("✅ Authorization URL constructed:")
        print(f"   {auth_url}")
        
        # Test if the authorization endpoint is accessible
        try:
            response = requests.get(auth_endpoint, timeout=10, allow_redirects=False)
            print(f"✅ Authorization endpoint accessible (status: {response.status_code})")
        except Exception as e:
            print(f"⚠️  Authorization endpoint test failed: {e}")
            
    except Exception as e:
        print(f"❌ Error constructing authorization URL: {e}")
    print()
    
    # Test 3: Application endpoints
    print("=== Test 3: Application Endpoints ===")
    app_base_url = "https://huayca.crub.uncoma.edu.ar/laboratorios-crub"
    endpoints_to_test = [
        ("/", "Main page"),
        ("/auth/login", "Login page"),
        ("/auth/keycloak-login", "Keycloak login endpoint"),
        ("/auth/callback", "Callback endpoint (should require parameters)")
    ]
    
    for endpoint, description in endpoints_to_test:
        url = f"{app_base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=10, allow_redirects=False)
            print(f"✅ {description}: {response.status_code}")
            if response.status_code == 302:
                print(f"   Redirects to: {response.headers.get('Location')}")
        except Exception as e:
            print(f"❌ {description}: Error - {e}")
    print()
    
    # Test 4: SSL Certificate
    print("=== Test 4: SSL Certificate Verification ===")
    try:
        response = requests.get(f"{server_url}realms/{realm}", verify=True, timeout=10)
        print("✅ SSL certificate is valid")
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL certificate error: {e}")
    except Exception as e:
        print(f"⚠️  SSL test failed: {e}")
    print()
    
    # Test 5: Network connectivity
    print("=== Test 5: Network Connectivity ===")
    try:
        import socket
        hostname = urlparse(server_url).hostname
        port = urlparse(server_url).port or (443 if server_url.startswith('https') else 80)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((hostname, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Network connectivity to {hostname}:{port} is working")
        else:
            print(f"❌ Network connectivity to {hostname}:{port} failed")
    except Exception as e:
        print(f"❌ Network connectivity test failed: {e}")
    print()
    
    # Test 6: Common issues check
    print("=== Test 6: Common Issues Check ===")
    issues_found = []
    
    # Check if server URL ends with /
    if not server_url.endswith('/'):
        issues_found.append("Server URL should end with '/'")
    
    # Check if redirect URI uses HTTPS
    if not redirect_uri.startswith('https://'):
        issues_found.append("Redirect URI should use HTTPS in production")
    
    # Check if client ID matches
    if 'dev' in client_id.lower():
        issues_found.append("Client ID appears to be for development environment")
    
    if issues_found:
        print("⚠️  Potential issues found:")
        for issue in issues_found:
            print(f"   - {issue}")
    else:
        print("✅ No common issues detected")
    print()
    
    print("=== Browser Debug Instructions ===")
    print("To debug authentication issues in the browser:")
    print("1. Open browser developer tools (F12)")
    print("2. Go to the Console tab")
    print("3. Navigate to the login page")
    print("4. Click 'Iniciar sesión con CRUB'")
    print("5. Monitor console logs for [KEYCLOAK-DEBUG] messages")
    print("6. Check Network tab for failed requests")
    print("7. Look for any JavaScript errors in the console")
    print()
    
    print("=== Log File Locations ===")
    print("Check these log files for detailed error information:")
    print("- Security log: /var/www/laboratorios-crub/logs/security_structured.log")
    print("- Application log: /var/www/laboratorios-crub/logs/app_structured.log")
    print("- Apache error log: /var/log/apache2/error.log")
    print()
    
    print("=== Manual Testing Steps ===")
    print("1. Try accessing the login page directly")
    print("2. Click the Keycloak login button")
    print("3. Check if you're redirected to Keycloak")
    print("4. After authentication, check if you're redirected back")
    print("5. Look for any error messages in the flash notifications")
    print()
    
    print("Debug completed. Check the above results for any issues.")
    print("=" * 60)

if __name__ == "__main__":
    debug_keycloak_production()
