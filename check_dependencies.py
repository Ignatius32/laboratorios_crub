#!/usr/bin/env python3
"""
Check if all required dependencies are installed
"""

def check_dependencies():
    """Check if all required dependencies for Keycloak are installed"""
    
    print("=" * 50)
    print("DEPENDENCY CHECK")
    print("=" * 50)
    
    required_packages = [
        ('authlib', 'OAuth2/OIDC client library'),
        ('requests', 'HTTP library'),
        ('PyJWT', 'JWT token handling'),
        ('flask', 'Web framework'),
        ('flask-login', 'User session management'),
        ('python-dotenv', 'Environment variable loading')
    ]
    
    missing_packages = []
    
    for package, description in required_packages:
        try:
            if package == 'PyJWT':
                import jwt
                print(f"✅ {package}: {jwt.__version__} - {description}")
            elif package == 'python-dotenv':
                import dotenv
                print(f"✅ {package}: {dotenv.__version__} - {description}")
            elif package == 'flask-login':
                import flask_login
                print(f"✅ {package}: {flask_login.__version__} - {description}")
            else:
                module = __import__(package)
                version = getattr(module, '__version__', 'unknown')
                print(f"✅ {package}: {version} - {description}")
                
        except ImportError:
            print(f"❌ {package}: NOT INSTALLED - {description}")
            missing_packages.append(package)
        except Exception as e:
            print(f"⚠️  {package}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    
    if missing_packages:
        print("❌ MISSING PACKAGES:")
        print("Run the following command to install missing packages:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    else:
        print("✅ ALL DEPENDENCIES INSTALLED")
        return True

if __name__ == "__main__":
    check_dependencies()
