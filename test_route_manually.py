#!/usr/bin/env python3
"""
Manually test Keycloak login route in Flask context
"""

import os
import sys

# Add the application directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_keycloak_login_route():
    """Test the Keycloak login route manually"""
    
    print("=" * 60)
    print("KEYCLOAK LOGIN ROUTE TEST")
    print("=" * 60)
    
    try:
        from app import create_app
        from flask import url_for
        
        # Create app
        app = create_app()
        
        with app.test_client() as client:
            print("✅ Test client created")
            
            # Test the login page first
            print("\n=== Testing login page ===")
            response = client.get('/auth/login')
            print(f"Login page status: {response.status_code}")
            
            # Test the health endpoint
            print("\n=== Testing health endpoint ===")
            try:
                response = client.get('/auth/keycloak-health')
                print(f"Health endpoint status: {response.status_code}")
                if response.status_code == 200:
                    print("Health response:")
                    print(response.get_data(as_text=True))
            except Exception as e:
                print(f"Health endpoint error: {e}")
            
            # Test the Keycloak login endpoint
            print("\n=== Testing Keycloak login endpoint ===")
            try:
                response = client.get('/auth/keycloak-login', follow_redirects=False)
                print(f"Keycloak login status: {response.status_code}")
                
                if response.status_code == 302:
                    location = response.headers.get('Location', '')
                    print(f"Redirect location: {location}")
                    
                    if 'huayca.crub.uncoma.edu.ar/auth/realms/CRUB' in location:
                        print("✅ Successfully redirects to Keycloak")
                    elif '/auth/login' in location:
                        print("⚠️  Redirects back to login - check for error messages")
                        
                        # Check for flash messages in session
                        with client.session_transaction() as sess:
                            flashes = sess.get('_flashes', [])
                            if flashes:
                                print("Flash messages:")
                                for category, message in flashes:
                                    print(f"  {category}: {message}")
                    else:
                        print(f"❓ Unexpected redirect: {location}")
                        
                elif response.status_code == 200:
                    print("❌ No redirect - check for errors in response")
                    
            except Exception as e:
                print(f"❌ Keycloak login error: {e}")
                import traceback
                traceback.print_exc()
            
            print("\n" + "=" * 60)
            print("Route test completed")
            
    except Exception as e:
        print(f"❌ Error in route test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_keycloak_login_route()
