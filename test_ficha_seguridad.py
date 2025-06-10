#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de ficha de seguridad
"""

import os
import sys
import base64

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.integrations.google_drive import drive_integration

def test_upload_ficha_seguridad():
    """
    Prueba la subida de una ficha de seguridad
    """
    print("Iniciando prueba de subida de ficha de seguridad...")
    
    # Crear un archivo de prueba simple
    test_content = b"PDF de prueba para ficha de seguridad"
    test_b64 = base64.b64encode(test_content).decode('utf-8')
    
    # Datos de prueba
    producto_id = "TEST001"
    file_extension = "pdf"
    
    try:
        # Llamar al método de subida
        result = drive_integration.upload_ficha_seguridad(
            producto_id=producto_id,
            file_data=test_b64,
            file_extension=file_extension
        )
        
        if result:
            print(f"✅ Subida exitosa!")
            print(f"   - File ID: {result.get('file_id')}")
            print(f"   - File URL: {result.get('file_url')}")
            print(f"   - Nombre esperado: ficha_seg_{producto_id}.{file_extension}")
        else:
            print("❌ Error en la subida")
            
    except Exception as e:
        print(f"❌ Excepción durante la prueba: {str(e)}")

def test_integration_config():
    """
    Verifica la configuración de la integración
    """
    print("Verificando configuración de Google Drive...")
    
    if drive_integration.script_url:
        print(f"✅ Script URL configurada: {drive_integration.script_url}")
    else:
        print("❌ Script URL no configurada")
        
    if drive_integration.secure_token:
        print(f"✅ Token de seguridad configurado: {drive_integration.secure_token}")
    else:
        print("❌ Token de seguridad no configurado")

if __name__ == "__main__":
    print("=== Prueba de Ficha de Seguridad ===\n")
    
    test_integration_config()
    print()
    
    # Solo hacer la prueba de subida si la configuración está lista
    if drive_integration.script_url:
        test_upload_ficha_seguridad()
    else:
        print("⚠️ Configuración incompleta. No se ejecutará la prueba de subida.")
    
    print("\n=== Fin de prueba ===")
