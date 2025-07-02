#!/usr/bin/env python3
"""
Debug script to test Keycloak server accessibility and URL construction
"""
import requests
import json
from urllib.parse import urljoin

def test_keycloak_urls():
    """Test different Keycloak URL configurations"""
    
    # Configuration from .env.production
    server_url = "https://huayca.crub.uncoma.edu.ar/auth"
    realm = "CRUB"
    
    # Test different base URLs
    base_urls = [
        "https://huayca.crub.uncoma.edu.ar/auth",  # Your current config
        "https://huayca.crub.uncoma.edu.ar",       # Modern Keycloak (no /auth)
    ]
    
    for base_url in base_urls:
        print(f"\n=== Testing base URL: {base_url} ===")
        
        # Test OpenID configuration endpoint
        oidc_config_url = f"{base_url}/realms/{realm}/.well-known/openid-configuration"
        print(f"Testing OIDC config: {oidc_config_url}")
        
        try:
            response = requests.get(oidc_config_url, timeout=10, verify=True)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                config = response.json()
                print("✅ SUCCESS - OpenID configuration found")
                print(f"  Issuer: {config.get('issuer', 'Not found')}")
                print(f"  Authorization endpoint: {config.get('authorization_endpoint', 'Not found')}")
                print(f"  Token endpoint: {config.get('token_endpoint', 'Not found')}")
                print(f"  Userinfo endpoint: {config.get('userinfo_endpoint', 'Not found')}")
                print(f"  End session endpoint: {config.get('end_session_endpoint', 'Not found')}")
            else:
                print(f"❌ FAILED - HTTP {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ FAILED - Network error: {e}")
        
        # Test realm info endpoint
        realm_info_url = f"{base_url}/realms/{realm}"
        print(f"Testing realm info: {realm_info_url}")
        
        try:
            response = requests.get(realm_info_url, timeout=10, verify=True)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                realm_info = response.json()
                print("✅ SUCCESS - Realm info found")
                print(f"  Realm: {realm_info.get('realm', 'Not found')}")
                print(f"  Public key: {'Found' if 'public_key' in realm_info else 'Not found'}")
            else:
                print(f"❌ FAILED - HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ FAILED - Network error: {e}")

def test_client_endpoints():
    """Test client-specific endpoints"""
    client_id = "laboratorios-crub"
    
    # Test the authorization URL that would be constructed
    base_url = "https://huayca.crub.uncoma.edu.ar/auth"
    realm = "CRUB"
    redirect_uri = "https://huayca.crub.uncoma.edu.ar/laboratorios-crub/auth/callback"
    
    auth_url = f"{base_url}/realms/{realm}/protocol/openid-connect/auth"
    print(f"\n=== Testing Authorization URL Construction ===")
    print(f"Authorization URL: {auth_url}")
    print(f"Client ID: {client_id}")
    print(f"Redirect URI: {redirect_uri}")
    
    # Build complete authorization URL
    from urllib.parse import urlencode
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile'
    }
    
    complete_auth_url = f"{auth_url}?{urlencode(params)}"
    print(f"Complete auth URL: {complete_auth_url}")
    
    # Test if the authorization endpoint is accessible
    try:
        response = requests.get(auth_url, timeout=10, verify=True)
        print(f"Auth endpoint status: {response.status_code}")
        if response.status_code in [200, 302, 400]:  # 400 is expected without proper params
            print("✅ Authorization endpoint is accessible")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error accessing auth endpoint: {e}")

if __name__ == "__main__":
    print("Keycloak URL Debug Script")
    print("=" * 50)
    
    test_keycloak_urls()
    test_client_endpoints()
    
    print("\n" + "=" * 50)
    print("Debug complete!")
