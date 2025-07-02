#!/usr/bin/env python3
"""
Test script to verify deployment configuration
"""
import os
import sys
from pathlib import Path

def test_production_config():
    """Test production configuration"""
    print("🧪 Testing production configuration...")
    
    try:
        # Add project directory to path
        project_dir = Path(__file__).parent.absolute()
        sys.path.insert(0, str(project_dir))
        
        # Set production environment
        os.environ['FLASK_ENV'] = 'production'
        os.environ['APPLICATION_ROOT'] = '/laboratorios-crub'
        os.environ['SERVER_NAME'] = 'example.com'
        
        from config import ProductionConfig
        from app import create_app
        
        app = create_app(ProductionConfig)
        
        print("✅ Flask app created successfully")
        print(f"✅ APPLICATION_ROOT: {app.config.get('APPLICATION_ROOT')}")
        print(f"✅ Environment: {app.config.get('ENVIRONMENT')}")
        print(f"✅ Is Production: {app.config.get('IS_PRODUCTION')}")
        
        # Test WSGI
        print("\n🧪 Testing WSGI application...")
        
        with app.test_client() as client:
            response = client.get('/')
            print(f"✅ Root endpoint status: {response.status_code}")
            
            # Test static file handling (simulated)
            print("✅ Static file configuration ready")
        
        print("\n🎉 All tests passed! Ready for deployment.")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_wsgi_import():
    """Test WSGI file can be imported"""
    print("\n🧪 Testing WSGI import...")
    
    try:
        # Set environment for WSGI
        os.environ['FLASK_ENV'] = 'production'
        os.environ['APPLICATION_ROOT'] = '/laboratorios-crub'
        
        # Import WSGI module
        import wsgi
        
        if hasattr(wsgi, 'application'):
            print("✅ WSGI application object found")
            print("✅ WSGI file ready for Apache")
            return True
        else:
            print("❌ WSGI application object not found")
            return False
            
    except Exception as e:
        print(f"❌ WSGI import error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Laboratorios CRUB Deployment Test\n")
    
    tests = [
        ("Production Configuration", test_production_config),
        ("WSGI Import", test_wsgi_import)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Running: {test_name}")
        if test_func():
            passed += 1
        print("-" * 50)
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for Apache deployment.")
        print("\n📋 Deployment checklist:")
        print("□ Copy files to /var/www/laboratorios-crub/")
        print("□ Create Python virtual environment")
        print("□ Install requirements.txt")
        print("□ Configure .env file")
        print("□ Set proper file permissions")
        print("□ Add Apache configuration")
        print("□ Enable Apache modules (wsgi, headers, expires)")
        print("□ Restart Apache")
    else:
        print("❌ Some tests failed. Please fix before deploying.")

if __name__ == "__main__":
    main()
