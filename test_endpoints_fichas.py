#!/usr/bin/env python3
"""
Script para probar los endpoints de fichas de seguridad
"""

import requests

def test_endpoint():
    """Prueba un endpoint básico"""
    try:
        response = requests.get("http://localhost:5000/", timeout=5)
        print(f"✅ Flask está corriendo - Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Error conectando a Flask: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing básico de Flask")
    if test_endpoint():
        print("🎉 ¡Flask está funcionando!")
        print("🔧 Para probar las fichas de seguridad:")
        print("   1. Inicia sesión en la aplicación")
        print("   2. Ve a la lista de productos")  
        print("   3. Haz clic en un botón de ficha de seguridad")
    else:
        print("⚠️ Flask no está corriendo")
        print("   Ejecuta: python run.py")
