"""
Test del formulario de login refactorizado para Keycloak v26
Verifica que todos los componentes del nuevo diseño funcionen correctamente
"""

import requests
import time
import json
import re

def test_login_page_accessibility():
    """Test que la página de login sea accesible"""
    print("🌐 Testing Login Page Accessibility...")
    
    try:
        response = requests.get("http://127.0.0.1:5000/auth/login", timeout=10)
        
        if response.status_code == 200:
            print("✓ Login page is accessible")
            
            # Check for key elements in the HTML
            content = response.text
            
            checks = {
                "Keycloak login button": 'id="keycloak-login-btn"' in content,
                "Local login form": 'id="localLoginForm"' in content,
                "Bootstrap collapse": 'data-bs-toggle="collapse"' in content,
                "Keycloak status indicator": 'id="keycloak-status"' in content,
                "Version meta tag": 'keycloak-version" content="26"' in content,
                "CRUB branding": 'Iniciar sesión con cuenta CRUB' in content,
                "Primary button styling": 'btn btn-primary btn-lg' in content,
                "Collapse functionality": 'collapse' in content and 'data-bs-target' in content,
                "JavaScript functions": 'testKeycloakConnection' in content,
                "Debug panel": 'debug-panel' in content or 'KEYCLOAK_DEBUG' in content
            }
            
            for check_name, result in checks.items():
                status = "✓" if result else "✗"
                print(f"  {status} {check_name}")
            
            # Check for v26 specific elements
            v26_checks = {
                "v26 meta tag": 'keycloak-version" content="26"' in content,
                "v26 debug logging": 'AUTH-DEBUG-v26' in content,
                "v26 endpoint reference": 'keycloak/realms/' in content,
                "Connection test function": 'testKeycloakConnection' in content
            }
            
            print("\n  🔍 Keycloak v26 Specific Elements:")
            for check_name, result in v26_checks.items():
                status = "✓" if result else "✗"
                print(f"    {status} {check_name}")
            
            all_passed = all(checks.values()) and all(v26_checks.values())
            return all_passed
        else:
            print(f"✗ Login page returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error accessing login page: {str(e)}")
        return False

def test_keycloak_integration():
    """Test que la integración con Keycloak v26 funcione"""
    print("\n🔑 Testing Keycloak v26 Integration...")
    
    try:
        # Test health endpoint
        response = requests.get("http://127.0.0.1:5000/auth/keycloak-health", timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            print("✓ Keycloak health endpoint accessible")
            
            checks = {
                "Status OK": health_data.get('status') == 'ok',
                "OIDC imported": health_data.get('keycloak_oidc_imported', False),
                "OIDC exists": health_data.get('keycloak_oidc_exists', False),
                "OAuth client exists": health_data.get('oauth_client_exists', False),
                "Keycloak client exists": health_data.get('keycloak_client_exists', False),
                "Server URL configured": bool(health_data.get('config', {}).get('server_url'))
            }
            
            for check_name, result in checks.items():
                status = "✓" if result else "✗"
                print(f"  {status} {check_name}")
            
            # Show configuration details
            config = health_data.get('config', {})
            server_url = config.get('server_url', 'Not set')
            print(f"  📍 Server URL: {server_url}")
            print(f"  🏛️  Realm: {config.get('realm', 'Not set')}")
            print(f"  🆔 Client ID: {config.get('client_id', 'Not set')}")
            
            # Verify v26 URL structure
            v26_url_correct = 'keycloak/' in server_url and 'https://' in server_url
            status = "✓" if v26_url_correct else "✗"
            print(f"  {status} v26 URL structure correct")
            
            return all(checks.values()) and v26_url_correct
        else:
            print(f"✗ Health endpoint returned status {response.status_code}")
            if response.status_code == 500:
                try:
                    error_data = response.json()
                    print(f"  Error details: {error_data.get('error', 'Unknown error')}")
                except:
                    pass
            return False
            
    except Exception as e:
        print(f"✗ Error testing Keycloak integration: {str(e)}")
        return False

def test_keycloak_redirect_url():
    """Test que la URL de redirect de Keycloak sea correcta"""
    print("\n🔄 Testing Keycloak Redirect URL Generation...")
    
    try:
        # Get the login page to extract the Keycloak URL
        response = requests.get("http://127.0.0.1:5000/auth/login", timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Extract the Keycloak URL from the href attribute
            # Look for: href="/auth/keycloak-login"
            keycloak_login_pattern = r'href="([^"]*keycloak-login[^"]*)"'
            match = re.search(keycloak_login_pattern, content)
            
            if match:
                keycloak_path = match.group(1)
                print(f"✓ Keycloak login path found: {keycloak_path}")
                
                # Test the keycloak-login endpoint (this should redirect to Keycloak)
                full_url = f"http://127.0.0.1:5000{keycloak_path}"
                
                # Use allow_redirects=False to capture the redirect response
                redirect_response = requests.get(full_url, allow_redirects=False, timeout=10)
                
                if redirect_response.status_code in [302, 301]:
                    location = redirect_response.headers.get('Location', '')
                    print(f"✓ Redirect response received (status: {redirect_response.status_code})")
                    print(f"  📍 Redirect URL: {location[:80]}...")
                    
                    # Verify v26 URL structure
                    v26_checks = {
                        "HTTPS protocol": location.startswith('https://'),
                        "Keycloak v26 path": '/keycloak/realms/' in location,
                        "CRUB realm": '/CRUB/' in location,
                        "OpenID Connect": '/protocol/openid-connect/auth' in location,
                        "Client ID parameter": 'client_id=' in location,
                        "Redirect URI parameter": 'redirect_uri=' in location,
                        "Response type": 'response_type=code' in location,
                        "Scope parameter": 'scope=' in location
                    }
                    
                    print("\n  🔍 URL Structure Validation:")
                    for check_name, result in v26_checks.items():
                        status = "✓" if result else "✗"
                        print(f"    {status} {check_name}")
                    
                    return all(v26_checks.values())
                else:
                    print(f"✗ Expected redirect, got status {redirect_response.status_code}")
                    return False
            else:
                print("✗ Keycloak login URL not found in page")
                return False
        else:
            print(f"✗ Could not load login page: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing Keycloak redirect URL: {str(e)}")
        return False

def test_api_endpoints():
    """Test de endpoints API relacionados con autenticación"""
    print("\n🔌 Testing Authentication API Endpoints...")
    
    endpoints = [
        ("/auth/keycloak-health", "Keycloak Health Check"),
        ("/auth/login", "Login Page"),
    ]
    
    results = {}
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"http://127.0.0.1:5000{endpoint}", timeout=10)
            success = response.status_code == 200
            status = "✓" if success else "✗"
            print(f"  {status} {description} ({endpoint}) - Status: {response.status_code}")
            results[endpoint] = success
        except Exception as e:
            print(f"  ✗ {description} ({endpoint}) - Error: {str(e)}")
            results[endpoint] = False
    
    return all(results.values())

def test_static_resources():
    """Test que los recursos estáticos estén disponibles"""
    print("\n📁 Testing Static Resources...")
    
    # Test the login page for static resource references
    try:
        response = requests.get("http://127.0.0.1:5000/auth/login", timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Check for common static resources
            static_checks = {
                "Bootstrap CSS/JS": 'bootstrap' in content.lower(),
                "FontAwesome icons": 'fas fa-' in content or 'fontawesome' in content.lower(),
                "Logo image": 'logo-web.png' in content or 'logo' in content.lower(),
                "CSS classes": 'btn' in content and 'form-control' in content,
                "Custom JavaScript": 'testKeycloakConnection' in content
            }
            
            for check_name, result in static_checks.items():
                status = "✓" if result else "✗"
                print(f"  {status} {check_name}")
            
            return all(static_checks.values())
        else:
            print(f"✗ Could not load login page: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing static resources: {str(e)}")
        return False

def main():
    """Ejecutar todos los tests del formulario de login"""
    print("🧪 Testing Refactored Login Form for Keycloak v26")
    print("=" * 60)
    
    tests = [
        ("Page Accessibility", test_login_page_accessibility),
        ("Keycloak Integration", test_keycloak_integration),
        ("Keycloak Redirect URL", test_keycloak_redirect_url),
        ("API Endpoints", test_api_endpoints),
        ("Static Resources", test_static_resources)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        print("-" * 40)
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ Test failed with exception: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📈 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Login form refactoring successful.")
        print("✅ Keycloak v26 integration working correctly")
        print("✅ UI components functioning as expected")
        print("✅ API endpoints responding correctly")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the results above.")
    
    print("\n📋 Next Steps:")
    print("1. Test the actual login flow with real credentials")
    print("2. Verify logout functionality")
    print("3. Test in production environment")
    print("4. Monitor logs for any issues")
    print("5. Remove backup files when confident migration is successful")

if __name__ == "__main__":
    main()
