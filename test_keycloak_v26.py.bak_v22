"""
Test script for Keycloak v26 endpoint
Tests the new endpoint at huayca.crub.uncoma.edu.ar/keycloak/
"""
import requests
import json
from keycloak import KeycloakAdmin, KeycloakOpenID
import sys
import os

# Add the app directory to the path so we can import config
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from config import Config
    config = Config()
    
    # Get configuration from Flask config or use defaults for testing
    KEYCLOAK_SERVER_URL = "https://huayca.crub.uncoma.edu.ar/keycloak/"  # New v26 URL
    KEYCLOAK_REALM = getattr(config, 'KEYCLOAK_REALM', 'laboratorios')
    KEYCLOAK_CLIENT_ID = getattr(config, 'KEYCLOAK_CLIENT_ID', 'laboratorios-app')
    KEYCLOAK_CLIENT_SECRET = getattr(config, 'KEYCLOAK_CLIENT_SECRET', '')
    
except ImportError:
    print("⚠️  Could not import Flask config, using test defaults")
    KEYCLOAK_SERVER_URL = "https://huayca.crub.uncoma.edu.ar/keycloak/"
    KEYCLOAK_REALM = "laboratorios"  # Replace with your actual realm
    KEYCLOAK_CLIENT_ID = "laboratorios-app"  # Replace with your actual client ID
    KEYCLOAK_CLIENT_SECRET = ""  # Replace with your actual client secret

def test_server_accessibility():
    """Test if the server is accessible"""
    print("0. Testing Server Accessibility...")
    try:
        # Test basic connectivity
        base_url = KEYCLOAK_SERVER_URL.rstrip('/')
        response = requests.get(base_url, timeout=10, verify=True)
        
        if response.status_code in [200, 301, 302, 404]:  # 404 is OK for root
            print("✓ Server is accessible")
            print(f"  - Status Code: {response.status_code}")
            return True
        else:
            print(f"✗ Server returned unexpected status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Server not accessible: {str(e)}")
        return False

def test_openid_configuration():
    """Test OpenID configuration endpoint"""
    print("\n1. Testing OpenID Configuration Endpoint...")
    try:
        # Keycloak v26 uses /realms/ instead of /auth/realms/
        url = f"{KEYCLOAK_SERVER_URL}realms/{KEYCLOAK_REALM}/.well-known/openid-configuration"
        print(f"  Testing URL: {url}")
        
        response = requests.get(url, verify=True, timeout=10)
        
        if response.status_code == 200:
            print("✓ OpenID Configuration endpoint accessible")
            config = response.json()
            print(f"  - Token endpoint: {config.get('token_endpoint')}")
            print(f"  - Authorization endpoint: {config.get('authorization_endpoint')}")
            print(f"  - Userinfo endpoint: {config.get('userinfo_endpoint')}")
            print(f"  - Logout endpoint: {config.get('end_session_endpoint')}")
            
            # Save config for later use
            return config
        else:
            print(f"✗ Failed to access OpenID configuration: {response.status_code}")
            print(f"  Response: {response.text[:200]}...")
            return None
    except Exception as e:
        print(f"✗ Error accessing OpenID configuration: {str(e)}")
        return None

def test_realm_endpoint():
    """Test direct realm endpoint"""
    print("\n2. Testing Realm Endpoint...")
    try:
        # Keycloak v26 endpoint structure
        url = f"{KEYCLOAK_SERVER_URL}realms/{KEYCLOAK_REALM}"
        print(f"  Testing URL: {url}")
        
        response = requests.get(url, verify=True, timeout=10)
        
        if response.status_code == 200:
            print("✓ Realm endpoint accessible")
            realm_data = response.json()
            print(f"  - Realm: {realm_data.get('realm')}")
            print(f"  - Public key available: {'public_key' in realm_data}")
            return True
        else:
            print(f"✗ Failed to access realm endpoint: {response.status_code}")
            print(f"  Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"✗ Error accessing realm endpoint: {str(e)}")
        return False

def test_admin_api():
    """Test Admin API access"""
    print("\n3. Testing Admin API...")
    
    if not KEYCLOAK_CLIENT_SECRET:
        print("⚠️  No client secret provided, skipping Admin API test")
        return False
        
    try:
        # Initialize admin client with new URL structure
        admin = KeycloakAdmin(
            server_url=KEYCLOAK_SERVER_URL,
            realm_name=KEYCLOAK_REALM,
            client_id=KEYCLOAK_CLIENT_ID,
            client_secret_key=KEYCLOAK_CLIENT_SECRET,
            verify=True
        )
        
        # Try to get realm info
        realm_info = admin.get_realm(KEYCLOAK_REALM)
        print("✓ Admin API accessible")
        print(f"  - Realm: {realm_info.get('realm')}")
        print(f"  - Display Name: {realm_info.get('displayName', 'N/A')}")
        return True
        
    except Exception as e:
        print(f"✗ Error accessing Admin API: {str(e)}")
        return False

def test_token_endpoint():
    """Test token endpoint with client credentials"""
    print("\n4. Testing Token Endpoint...")
    
    if not KEYCLOAK_CLIENT_SECRET:
        print("⚠️  No client secret provided, skipping token test")
        return False
        
    try:
        keycloak_openid = KeycloakOpenID(
            server_url=KEYCLOAK_SERVER_URL,
            client_id=KEYCLOAK_CLIENT_ID,
            realm_name=KEYCLOAK_REALM,
            client_secret_key=KEYCLOAK_CLIENT_SECRET
        )
        
        # Get token using client credentials
        token = keycloak_openid.token(grant_type=['client_credentials'])
        
        print("✓ Token endpoint accessible")
        print(f"  - Access token obtained: {token['access_token'][:50]}...")
        print(f"  - Token type: {token.get('token_type')}")
        print(f"  - Expires in: {token.get('expires_in')} seconds")
        return True
        
    except Exception as e:
        print(f"✗ Error getting token: {str(e)}")
        return False

def test_authorization_url():
    """Test authorization URL generation"""
    print("\n5. Testing Authorization URL Generation...")
    try:
        keycloak_openid = KeycloakOpenID(
            server_url=KEYCLOAK_SERVER_URL,
            client_id=KEYCLOAK_CLIENT_ID,
            realm_name=KEYCLOAK_REALM
        )
        
        # Generate authorization URL
        auth_url = keycloak_openid.auth_url(
            redirect_uri="http://localhost:5000/auth/callback",
            scope="openid email profile"
        )
        
        print("✓ Authorization URL generated successfully")
        print(f"  - URL: {auth_url[:100]}...")
        return True
        
    except Exception as e:
        print(f"✗ Error generating authorization URL: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("Testing Keycloak v26 Endpoints")
    print("=" * 60)
    print(f"Server URL: {KEYCLOAK_SERVER_URL}")
    print(f"Realm: {KEYCLOAK_REALM}")
    print(f"Client ID: {KEYCLOAK_CLIENT_ID}")
    print(f"Client Secret: {'***' if KEYCLOAK_CLIENT_SECRET else 'NOT SET'}")
    print("=" * 60)
    
    # Run tests
    results = {}
    results["Server Accessibility"] = test_server_accessibility()
    
    oidc_config = test_openid_configuration()
    results["OpenID Configuration"] = oidc_config is not None
    
    results["Realm Endpoint"] = test_realm_endpoint()
    results["Admin API"] = test_admin_api()
    results["Token Endpoint"] = test_token_endpoint()
    results["Authorization URL"] = test_authorization_url()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    # Configuration recommendations
    print("\n" + "=" * 60)
    print("CONFIGURATION RECOMMENDATIONS")
    print("=" * 60)
    
    if results["OpenID Configuration"]:
        print("✓ Update your Flask app configuration:")
        print(f"KEYCLOAK_SERVER_URL = '{KEYCLOAK_SERVER_URL}'")
        print("\n✓ URL migration successful:")
        print("- Old v22: huayca.crub.uncoma.edu.ar/auth/")
        print("- New v26: huayca.crub.uncoma.edu.ar/keycloak/")
        
        if oidc_config:
            print(f"\n✓ Available endpoints:")
            print(f"- Authorization: {oidc_config.get('authorization_endpoint', 'N/A')}")
            print(f"- Token: {oidc_config.get('token_endpoint', 'N/A')}")
            print(f"- UserInfo: {oidc_config.get('userinfo_endpoint', 'N/A')}")
            print(f"- Logout: {oidc_config.get('end_session_endpoint', 'N/A')}")
    else:
        print("✗ OpenID configuration failed. Check:")
        print("- Server URL is correct")
        print("- Realm name is correct")
        print("- Network connectivity")
        print("- SSL certificate issues")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    
    if all(results.values()):
        print("🎉 All tests passed! Your Keycloak v26 setup is working correctly.")
        print("You can now update your Flask application configuration.")
    else:
        failed_tests = [name for name, result in results.items() if not result]
        print(f"⚠️  Some tests failed: {', '.join(failed_tests)}")
        print("Please check the configuration and try again.")

if __name__ == "__main__":
    main()
