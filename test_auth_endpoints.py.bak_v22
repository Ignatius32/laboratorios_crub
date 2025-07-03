#!/usr/bin/env python3
"""
Simple test for Keycloak authentication in production
"""

import requests
import sys

def test_auth_endpoints():
    """Test the authentication endpoints"""
    
    base_url = "https://huayca.crub.uncoma.edu.ar/laboratorios-crub"
    
    print("Testing authentication endpoints...")
    print("=" * 50)
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/auth/keycloak-health", timeout=10)
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test login page
    try:
        response = requests.get(f"{base_url}/auth/login", timeout=10)
        print(f"Login page: {response.status_code}")
        if response.status_code == 200:
            print("✅ Login page accessible")
        else:
            print(f"❌ Login page error: {response.status_code}")
    except Exception as e:
        print(f"❌ Login page error: {e}")
    
    # Test Keycloak login endpoint (should redirect)
    try:
        response = requests.get(f"{base_url}/auth/keycloak-login", 
                              timeout=10, 
                              allow_redirects=False)
        print(f"Keycloak login: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            if 'huayca.crub.uncoma.edu.ar/auth/realms/CRUB' in location:
                print("✅ Keycloak login redirects to Keycloak server")
            elif '/auth/login' in location:
                print("⚠️  Keycloak login redirects back to login (check logs)")
            else:
                print(f"❓ Keycloak login redirects to: {location}")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Keycloak login error: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed.")

if __name__ == "__main__":
    test_auth_endpoints()
