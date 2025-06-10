#!/usr/bin/env python3
"""
Script de diagnóstico para el problema de ficha de seguridad
"""

import os
import sys
import base64
import requests
import json

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_google_script_connection():
    """
    Prueba la conexión directa al Google Apps Script
    """
    print("🔍 Probando conexión con Google Apps Script...")
    
    script_url = os.environ.get('GOOGLE_SCRIPT_URL')
    secure_token = os.environ.get('GOOGLE_DRIVE_SECURE_TOKEN', '1250')
    
    if not script_url:
        print("❌ GOOGLE_SCRIPT_URL no está configurada")
        return False
    
    print(f"✅ Script URL: {script_url}")
    print(f"✅ Token: {secure_token}")
    
    # Probar con una acción conocida que funciona
    test_data = {
        'action': 'sendEmail',  # Esta acción ya funciona
        'token': str(secure_token),
        'to': 'test@example.com',
        'subject': 'Test de conexión',
        'htmlBody': 'Este es un test de conexión'
    }
    
    try:
        print("📤 Enviando request de prueba...")
        response = requests.post(
            script_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📥 Status Code: {response.status_code}")
        print(f"📥 Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Conexión exitosa con Google Apps Script")
                return True
            else:
                print(f"❌ Error del script: {result.get('error')}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción: {str(e)}")
        return False

def test_ficha_seguridad_action():
    """
    Prueba específicamente la acción uploadFichaSeguridad
    """
    print("\n🔍 Probando acción uploadFichaSeguridad...")
    
    script_url = os.environ.get('GOOGLE_SCRIPT_URL')
    secure_token = os.environ.get('GOOGLE_DRIVE_SECURE_TOKEN', '1250')
    
    if not script_url:
        print("❌ GOOGLE_SCRIPT_URL no está configurada")
        return False
    
    # Crear un archivo de prueba pequeño
    test_content = b"Test PDF content for ficha de seguridad"
    test_b64 = base64.b64encode(test_content).decode('utf-8')
    
    test_data = {
        'action': 'uploadFichaSeguridad',
        'token': str(secure_token),
        'fileName': 'ficha_seg_TEST001.pdf',
        'fileData': test_b64,
        'fileExtension': 'pdf'
    }
    
    try:
        print("📤 Enviando request de ficha de seguridad...")
        response = requests.post(
            script_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        print(f"📥 Status Code: {response.status_code}")
        print(f"📥 Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Upload de ficha de seguridad exitoso!")
                print(f"   - File ID: {result.get('fileId')}")
                print(f"   - File URL: {result.get('fileUrl')}")
                return True
            else:
                error = result.get('error', 'Error desconocido')
                print(f"❌ Error del script: {error}")
                
                # Analizar errores específicos
                if 'Unknown action' in error:
                    print("🔧 SOLUCIÓN: El Google Apps Script no tiene la nueva función.")
                    print("   1. Copie el código actualizado de app.gs")
                    print("   2. Guarde y haga un nuevo deployment")
                    print("   3. Use la nueva URL del deployment")
                
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción: {str(e)}")
        return False

def test_environment_config():
    """
    Verifica la configuración del entorno
    """
    print("\n🔍 Verificando configuración del entorno...")
    
    config_issues = []
    
    script_url = os.environ.get('GOOGLE_SCRIPT_URL')
    if not script_url:
        config_issues.append("GOOGLE_SCRIPT_URL no está configurada")
    else:
        print(f"✅ GOOGLE_SCRIPT_URL: {script_url}")
    
    token = os.environ.get('GOOGLE_DRIVE_SECURE_TOKEN')
    if not token:
        config_issues.append("GOOGLE_DRIVE_SECURE_TOKEN no está configurada")
    else:
        print(f"✅ GOOGLE_DRIVE_SECURE_TOKEN: {token}")
    
    if config_issues:
        print(f"❌ Problemas de configuración encontrados:")
        for issue in config_issues:
            print(f"   - {issue}")
        return False
    
    return True

def main():
    print("=== DIAGNÓSTICO DE FICHA DE SEGURIDAD ===\n")
    
    # 1. Verificar configuración
    config_ok = test_environment_config()
    
    if not config_ok:
        print("\n❌ Configure las variables de entorno antes de continuar")
        return
    
    # 2. Probar conexión general
    connection_ok = test_google_script_connection()
    
    if not connection_ok:
        print("\n❌ No se puede conectar al Google Apps Script")
        print("🔧 Verifique la URL y que el script esté desplegado")
        return
    
    # 3. Probar función específica
    ficha_ok = test_ficha_seguridad_action()
    
    if ficha_ok:
        print("\n✅ ¡Todo funciona correctamente!")
    else:
        print("\n❌ La función de ficha de seguridad no está funcionando")
        print("\n🔧 PASOS PARA SOLUCIONAR:")
        print("1. Abra Google Apps Script en script.google.com")
        print("2. Copie el código actualizado de app.gs")
        print("3. Guarde el proyecto")
        print("4. Haga Deploy > New deployment")
        print("5. Copie la nueva URL y actualice GOOGLE_SCRIPT_URL")
        print("6. Ejecute este diagnóstico nuevamente")

if __name__ == "__main__":
    main()
