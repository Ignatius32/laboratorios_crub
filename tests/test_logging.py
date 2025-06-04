"""
Script de ejemplo para demostrar el uso del sistema de logging estructurado.
Este archivo puede ejecutarse para verificar que el logging funciona correctamente.
"""

from app.utils.logging_config import (
    StructuredLogger,
    get_audit_logger,
    get_business_logger,
    get_security_logger,
    get_performance_logger,
    get_database_logger
)
from app.utils.logging_decorators import (
    log_action,
    audit_user_action,
    monitor_performance,
    log_security_event,
    log_admin_action,
    log_data_modification
)
import time

def test_basic_logging():
    """Prueba el logging básico estructurado."""
    print("=== Probando logging básico ===")
    
    # Logger básico
    logger = StructuredLogger()
    logger.info("Mensaje de información básico", 
                operation="test",
                component="logging_test")
    
    logger.warning("Mensaje de advertencia",
                   warning_type="test_warning",
                   details="Esta es una prueba")
    
    logger.error("Mensaje de error de prueba",
                 error_code="TEST_001",
                 component="test_module")

def test_specialized_loggers():
    """Prueba los loggers especializados."""
    print("=== Probando loggers especializados ===")
    
    # Logger de auditoría
    audit_logger = get_audit_logger()
    audit_logger.info("Acción de auditoría de prueba",
                     action="test_audit",
                     entity_type="usuario",
                     entity_id="TEST_USER")
    
    # Logger de seguridad
    security_logger = get_security_logger()
    security_logger.warning("Evento de seguridad de prueba",
                           event_type="test_security_event",
                           risk_level="medium",
                           source_ip="127.0.0.1")
    
    # Logger de negocio
    business_logger = get_business_logger()
    business_logger.info("Operación de negocio completada",
                        operation="stock_calculation",
                        laboratory_id="LAB001",
                        products_processed=50)
    
    # Logger de rendimiento
    perf_logger = get_performance_logger()
    perf_logger.info("Métrica de rendimiento",
                    operation="database_query",
                    duration_ms=1250,
                    rows_affected=100)
    
    # Logger de base de datos
    db_logger = get_database_logger()
    db_logger.warning("Consulta lenta detectada",
                     query_type="SELECT",
                     table="movimientos",
                     duration_ms=2500)

@log_action("operación de prueba", logger_type="business", include_args=True)
def test_decorated_function(product_id, quantity):
    """Función de prueba con decorador de logging."""
    print(f"Procesando producto {product_id} con cantidad {quantity}")
    time.sleep(0.1)  # Simular trabajo
    return {"status": "success", "processed": quantity}

@audit_user_action("creación de producto de prueba", sensitive=True)
def test_audit_decorated_function(product_name):
    """Función de prueba con decorador de auditoría."""
    print(f"Creando producto: {product_name}")
    return {"product_id": "PROD_TEST_001", "name": product_name}

@monitor_performance(threshold_ms=50)
def test_performance_decorated_function():
    """Función de prueba con decorador de rendimiento."""
    time.sleep(0.1)  # Simular trabajo que excede el umbral
    return "Operación completada"

@log_security_event("evento de prueba", risk_level="low")
def test_security_decorated_function():
    """Función de prueba con decorador de seguridad."""
    print("Ejecutando operación de seguridad de prueba")
    return {"security_check": "passed"}

def test_exception_logging():
    """Prueba el logging de excepciones."""
    print("=== Probando logging de excepciones ===")
    
    logger = StructuredLogger()
    
    try:
        # Provocar una excepción
        result = 1 / 0
    except Exception as e:
        logger.error("Error capturado en prueba",
                    error_type="division_by_zero",
                    operation="test_exception",
                    recovery_action="none")

@log_action("operación con error", logger_type="business")
def test_decorated_function_with_error():
    """Función decorada que genera un error para probar el logging de errores."""
    raise ValueError("Error de prueba intencional")

def test_context_logging():
    """Prueba el logging con contexto adicional."""
    print("=== Probando logging con contexto ===")
    
    logger = StructuredLogger('business')
    
    # Simular contexto de una operación compleja
    operation_context = {
        "operation_id": "OP_20250529_001",
        "user_id": "ADMIN001",
        "laboratory_id": "LAB_QUIMICA",
        "timestamp": time.time(),
        "batch_size": 100
    }
    
    logger.info("Iniciando procesamiento por lotes", **operation_context)
    
    # Simular procesamiento
    for i in range(3):
        item_context = {
            **operation_context,
            "item_number": i + 1,
            "item_status": "processing"
        }
        logger.debug(f"Procesando item {i + 1}", **item_context)
        time.sleep(0.01)
    
    final_context = {
        **operation_context,
        "status": "completed",
        "items_processed": 3,
        "duration_ms": 30
    }
    logger.info("Procesamiento por lotes completado", **final_context)

def run_all_tests():
    """Ejecuta todas las pruebas de logging."""
    print("🚀 Iniciando pruebas del sistema de logging estructurado\n")
    
    try:
        test_basic_logging()
        print("✅ Logging básico - OK\n")
        
        test_specialized_loggers()
        print("✅ Loggers especializados - OK\n")
        
        # Probar decoradores
        result = test_decorated_function("PROD001", 25)
        print(f"✅ Decorador de acción - OK (resultado: {result})\n")
        
        audit_result = test_audit_decorated_function("Producto de Prueba")
        print(f"✅ Decorador de auditoría - OK (resultado: {audit_result})\n")
        
        perf_result = test_performance_decorated_function()
        print(f"✅ Decorador de rendimiento - OK (resultado: {perf_result})\n")
        
        security_result = test_security_decorated_function()
        print(f"✅ Decorador de seguridad - OK (resultado: {security_result})\n")
        
        test_exception_logging()
        print("✅ Logging de excepciones - OK\n")
        
        # Probar decorador con error
        try:
            test_decorated_function_with_error()
        except ValueError:
            print("✅ Decorador con error - OK (error capturado correctamente)\n")
        
        test_context_logging()
        print("✅ Logging con contexto - OK\n")
        
        print("🎉 Todas las pruebas completadas exitosamente!")
        print("📁 Revisa los archivos en la carpeta 'logs' para ver los resultados:")
        print("   - app_structured.log")
        print("   - audit_structured.log")
        print("   - business_structured.log")
        print("   - security_structured.log")
        print("   - performance_structured.log")
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")

if __name__ == "__main__":
    # Este script puede ejecutarse directamente para pruebas
    print("Este script debe ejecutarse en el contexto de la aplicación Flask.")
    print("Para probarlo, ejecuta:")
    print("python -c \"from app import create_app; app = create_app(); from test_logging import run_all_tests; app.app_context().push(); run_all_tests()\"")
