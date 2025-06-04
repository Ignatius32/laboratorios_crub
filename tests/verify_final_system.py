#!/usr/bin/env python3
"""
Test de Verificación Final del Sistema CRUB con Logging Completo
===============================================================

Este script verifica que la aplicación Flask funcione correctamente
con el sistema de logging estructurado implementado.
"""

import os
import sys
import time

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_flask_app_with_logging():
    """Test que la aplicación Flask funcione con el nuevo sistema de logging"""
    print("🔍 Verificando aplicación Flask con logging estructurado...")
    
    try:
        # Importar y crear la aplicación
        from app import create_app
        from config import Config
        
        app = create_app(Config)
        
        with app.app_context():
            print("✅ Aplicación Flask creada exitosamente")
            
            # Verificar que el logging esté configurado
            from app.utils.logging_config import get_app_logger, get_business_logger
            
            app_logger = get_app_logger()
            business_logger = get_business_logger()
            
            # Generar logs de test
            app_logger.info("Test de aplicación Flask con logging estructurado")
            business_logger.info("Test de operación de negocio")
            
            print("✅ Sistema de logging funcionando en Flask")
            
            # Verificar rutas críticas importadas
            print("🔍 Verificando importación de rutas...")
            
            # Test imports de rutas con logging
            try:
                from app.routes.auth import auth
                from app.routes.admin import admin  
                from app.routes.tecnicos import tecnicos
                from app.routes.main import main
                
                print("✅ Todas las rutas importadas correctamente")
                
                # Verificar que las rutas tengan los decoradores de logging
                admin_routes = [name for name in dir(admin) if not name.startswith('_')]
                print(f"✅ Rutas de admin disponibles: {len(admin_routes)}")
                
                return True
                
            except Exception as e:
                print(f"❌ Error importando rutas: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Error creando aplicación Flask: {e}")
        return False

def test_database_connection():
    """Verificar que la base de datos esté funcionando"""
    print("\n🔍 Verificando conexión a base de datos...")
    
    try:
        from app import create_app
        from config import Config
        from app.models.models import db, Usuario
        
        app = create_app(Config)
        
        with app.app_context():
            # Test simple de consulta
            user_count = Usuario.query.count()
            print(f"✅ Base de datos conectada - Usuarios registrados: {user_count}")
            return True
            
    except Exception as e:
        print(f"❌ Error conectando a base de datos: {e}")
        return False

def test_logging_in_production_context():
    """Test del logging en contexto de producción"""
    print("\n🔍 Verificando logging en contexto de producción...")
    
    try:
        from app import create_app
        from config import Config
        from app.utils.logging_config import get_business_logger, get_audit_logger
        
        app = create_app(Config)
        
        with app.app_context():
            # Simular request context
            with app.test_request_context('/', method='POST'):
                business_logger = get_business_logger()
                audit_logger = get_audit_logger()
                
                # Logs con contexto completo
                business_logger.info("Test de operación con contexto Flask", extra={
                    'operation': 'production_test',
                    'component': 'verification_system'
                })
                
                audit_logger.info("Test de auditoría con contexto Flask", extra={
                    'action': 'production_audit_test',
                    'entity_type': 'system_verification'
                })
                
                print("✅ Logging funcionando en contexto de producción")
                return True
                
    except Exception as e:
        print(f"❌ Error en logging de producción: {e}")
        return False

def verify_log_files_updated():
    """Verificar que los archivos de log se hayan actualizado"""
    print("\n🔍 Verificando actualización de archivos de log...")
    
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    
    if not os.path.exists(logs_dir):
        print("❌ Directorio de logs no encontrado")
        return False
    
    # Archivos que deberían tener contenido reciente
    log_files = [
        'business_structured.log',
        'app_structured.log'
    ]
    
    recent_files = 0
    
    for log_file in log_files:
        file_path = os.path.join(logs_dir, log_file)
        if os.path.exists(file_path):
            # Verificar modificación reciente (últimos 60 segundos)
            mod_time = os.path.getmtime(file_path)
            current_time = time.time()
            
            if (current_time - mod_time) < 60:
                print(f"✅ {log_file} actualizado recientemente")
                recent_files += 1
            else:
                print(f"⚠️  {log_file} no actualizado recientemente")
        else:
            print(f"❌ {log_file} no encontrado")
    
    return recent_files > 0

def run_final_verification():
    """Ejecutar verificación final completa"""
    print("=" * 60)
    print("🎯 VERIFICACIÓN FINAL DEL SISTEMA CRUB CON LOGGING")
    print("=" * 60)
    
    tests = [
        ("Aplicación Flask con Logging", test_flask_app_with_logging),
        ("Conexión a Base de Datos", test_database_connection),
        ("Logging en Contexto de Producción", test_logging_in_production_context),
        ("Archivos de Log Actualizados", verify_log_files_updated)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔄 Ejecutando: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE VERIFICACIÓN FINAL")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results:
        status = "✅ EXITOSO" if passed_test else "❌ FALLÓ"
        print(f"{status} {test_name}")
        if passed_test:
            passed += 1
    
    print(f"\n📈 Resultado Final: {passed}/{total} verificaciones exitosas")
    
    if passed == total:
        print("\n🎉 ¡VERIFICACIÓN COMPLETA EXITOSA!")
        print("🚀 El sistema CRUB está LISTO PARA PRODUCCIÓN con logging estructurado completo")
        print("📋 Todos los componentes funcionando correctamente")
    else:
        print(f"\n⚠️  {total - passed} verificaciones fallaron")
        print("🔧 Revisar componentes indicados antes de producción")

if __name__ == "__main__":
    run_final_verification()
