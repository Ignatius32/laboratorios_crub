#!/usr/bin/env python3
"""
Test Completo del Sistema de Logging Estructurado
=================================================

Este script verifica que todos los componentes del sistema de logging estructurado
estén funcionando correctamente después de la implementación completa.

Autores: Sistema de Gestión CRUB
Versión: 2.0
Fecha: Diciembre 2024
"""

import os
import sys
import json
import time
import requests
import logging
from datetime import datetime

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_logging_configuration():
    """Verificar la configuración básica del logging"""
    print("🔍 Verificando configuración del logging...")
    
    try:
        from app.utils.logging_config import (
            get_app_logger, get_security_logger,
            get_audit_logger, get_business_logger, get_database_logger,
            get_performance_logger
        )
        
        print("✅ Configuración del logging inicializada correctamente")
        
        # Test de todos los loggers
        loggers = {
            'app': get_app_logger(),
            'security': get_security_logger(),
            'audit': get_audit_logger(),
            'business': get_business_logger(),
            'database': get_database_logger(),
            'performance': get_performance_logger()
        }
        
        for name, logger in loggers.items():
            logger.info(f"Test de logger {name} - {datetime.now().isoformat()}")
            print(f"✅ Logger '{name}' funcionando correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en configuración del logging: {e}")
        return False

def test_decorators():
    """Verificar que los decoradores estén funcionando"""
    print("\n🔍 Verificando decoradores de logging...")
    
    try:
        from app.utils.logging_decorators import (
            log_admin_action, audit_user_action, monitor_performance,
            log_business_operation, log_data_modification, log_security_event
        )
        
        # Test simple de decoradores
        @log_admin_action("test action")
        def test_function():
            return "success"
        
        @monitor_performance(threshold_ms=100)
        def test_performance():
            time.sleep(0.05)  # 50ms
            return "performance test"
        
        # Ejecutar tests
        result1 = test_function()
        result2 = test_performance()
        
        print("✅ Decoradores funcionando correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en decoradores: {e}")
        return False

def test_request_logging():
    """Verificar el middleware de logging de requests"""
    print("\n🔍 Verificando middleware de logging de requests...")
    
    try:
        from app.utils.request_logging import RequestLoggingMiddleware
        from flask import Flask
        
        # Crear app de test
        app = Flask(__name__)
        middleware = RequestLoggingMiddleware()
        
        print("✅ Middleware de requests creado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en middleware de requests: {e}")
        return False

def verify_log_files():
    """Verificar que los archivos de log se estén creando"""
    print("\n🔍 Verificando archivos de log...")
    
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    
    expected_files = [
        'app_structured.log',
        'security.log',
        'audit_structured.log',
        'business_structured.log',
        'database_structured.log',
        'performance.log'
    ]
    
    for log_file in expected_files:
        file_path = os.path.join(logs_dir, log_file)
        if os.path.exists(file_path):
            print(f"✅ Archivo encontrado: {log_file}")
            
            # Verificar que el archivo tenga contenido reciente
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1]
                        if datetime.now().strftime('%Y-%m-%d') in last_line:
                            print(f"  📝 Contenido reciente encontrado")
                        else:
                            print(f"  ⚠️  No hay contenido reciente")
                    else:
                        print(f"  ⚠️  Archivo vacío")
            except Exception as e:
                print(f"  ⚠️  Error leyendo archivo: {e}")
        else:
            print(f"❌ Archivo no encontrado: {log_file}")

def test_json_format():
    """Verificar que los logs estén en formato JSON"""
    print("\n🔍 Verificando formato JSON de los logs...")
    
    try:
        from app.utils.logging_config import get_app_logger
        
        logger = get_app_logger()
        test_message = f"Test JSON format - {datetime.now().isoformat()}"
        
        # Generar un log de test
        logger.info(test_message, extra={
            'user_id': 'test_user',
            'action': 'json_format_test',
            'ip_address': '127.0.0.1'
        })
        
        # Verificar en el archivo
        logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
        app_log_file = os.path.join(logs_dir, 'app_structured.log')
        
        if os.path.exists(app_log_file):
            with open(app_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Buscar la línea más reciente
            for line in reversed(lines):
                if test_message in line:
                    try:
                        log_data = json.loads(line.strip())
                        print("✅ Formato JSON válido encontrado:")
                        print(f"  📝 Timestamp: {log_data.get('timestamp')}")
                        print(f"  📝 Level: {log_data.get('level')}")
                        print(f"  📝 Logger: {log_data.get('logger')}")
                        print(f"  📝 User ID: {log_data.get('user_id')}")
                        return True
                    except json.JSONDecodeError:
                        print("❌ Formato JSON inválido")
                        return False
            
            print("⚠️  Log de test no encontrado en el archivo")
        else:
            print("❌ Archivo de log no encontrado")
        
        return False
        
    except Exception as e:
        print(f"❌ Error verificando formato JSON: {e}")
        return False

def test_flask_app_integration():
    """Verificar la integración con la aplicación Flask"""
    print("\n🔍 Verificando integración con Flask...")
    
    try:
        # Intentar importar la aplicación
        from app import create_app
        from config import Config
        
        # Crear app de test
        app = create_app(Config)
        
        with app.app_context():
            print("✅ Aplicación Flask cargada correctamente")
            
            # Verificar que el logging esté configurado
            if hasattr(app, 'logger'):
                app.logger.info("Test de integración Flask - logging funcional")
                print("✅ Logger de Flask configurado")
            
            return True
            
    except Exception as e:
        print(f"❌ Error en integración Flask: {e}")
        return False

def generate_test_logs():
    """Generar logs de test para todos los loggers"""
    print("\n🔍 Generando logs de test...")
    
    try:
        from app.utils.logging_config import (
            get_app_logger, get_security_logger, get_audit_logger,
            get_business_logger, get_database_logger, get_performance_logger
        )
        
        timestamp = datetime.now().isoformat()
        
        # Test logs para cada categoría
        test_data = {
            'app': {
                'logger': get_app_logger(),
                'message': f"Test aplicación - {timestamp}",
                'extra': {'component': 'test_suite', 'action': 'app_test'}
            },
            'security': {
                'logger': get_security_logger(),
                'message': f"Test seguridad - {timestamp}",
                'extra': {'event_type': 'test_security', 'ip_address': '127.0.0.1'}
            },
            'audit': {
                'logger': get_audit_logger(),
                'message': f"Test auditoría - {timestamp}",
                'extra': {'action': 'test_audit', 'entity_type': 'test', 'entity_id': 'test123'}
            },
            'business': {
                'logger': get_business_logger(),
                'message': f"Test negocio - {timestamp}",
                'extra': {'operation': 'test_business', 'lab_id': 'test_lab'}
            },
            'database': {
                'logger': get_database_logger(),
                'message': f"Test base de datos - {timestamp}",
                'extra': {'query_type': 'test', 'table': 'test_table'}
            },
            'performance': {
                'logger': get_performance_logger(),
                'message': f"Test rendimiento - {timestamp}",
                'extra': {'function': 'test_performance', 'duration_ms': 50}
            }
        }
        
        for category, data in test_data.items():
            try:
                data['logger'].info(data['message'], extra=data['extra'])
                print(f"✅ Log de test generado para: {category}")
            except Exception as e:
                print(f"❌ Error generando log para {category}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generando logs de test: {e}")
        return False

def run_complete_test():
    """Ejecutar el test completo del sistema"""
    print("=" * 60)
    print("🚀 INICIO DE PRUEBAS DEL SISTEMA DE LOGGING ESTRUCTURADO")
    print("=" * 60)
    
    tests = [
        ("Configuración del Logging", test_logging_configuration),
        ("Decoradores", test_decorators),
        ("Middleware de Requests", test_request_logging),
        ("Integración con Flask", test_flask_app_integration),
        ("Generación de Logs de Test", generate_test_logs),
        ("Formato JSON", test_json_format),
        ("Archivos de Log", verify_log_files),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error ejecutando test '{test_name}': {e}")
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results:
        status = "✅ PASÓ" if passed_test else "❌ FALLÓ"
        print(f"{status} {test_name}")
        if passed_test:
            passed += 1
    
    print(f"\n📈 Resultado: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("🎉 ¡TODOS LOS TESTS PASARON! El sistema de logging está funcionando correctamente.")
    else:
        print("⚠️  Algunos tests fallaron. Revisar la implementación.")
    
    print("\n💡 Para verificar los logs generados, revisar el directorio 'logs/'")
    print("💡 Los logs están en formato JSON estructurado para facilitar el análisis")

if __name__ == "__main__":
    run_complete_test()
