"""
Decoradores para logging estructurado en el sistema CRUB.
Proporciona decoradores para logging automático de funciones, 
auditoría de acciones y monitoreo de rendimiento.
"""

import time
import functools
from typing import Callable, Any, Optional
from flask import request
from flask_login import current_user
from .logging_config import (
    StructuredLogger, 
    get_audit_logger, 
    get_performance_logger,
    get_business_logger,
    get_security_logger
)

def log_action(action_type: str = "general", logger_type: str = "business", 
               include_args: bool = False, include_result: bool = False):
    """
    Decorador para logging automático de acciones de negocio.
    
    Args:
        action_type: Tipo de acción para categorización
        logger_type: Tipo de logger a usar (business, audit, security)
        include_args: Si incluir argumentos de la función en el log
        include_result: Si incluir el resultado en el log
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Obtener logger apropiado
            if logger_type == "audit":
                logger = get_audit_logger()
            elif logger_type == "security":
                logger = get_security_logger()
            elif logger_type == "performance":
                logger = get_performance_logger()
            else:
                logger = get_business_logger()
            
            # Preparar contexto base
            context = {
                "action_type": action_type,
                "function": func.__name__,
                "module": func.__module__
            }
            
            # Incluir argumentos si se solicita (sin passwords)
            if include_args:
                safe_args = _sanitize_args(args, kwargs)
                context["arguments"] = safe_args
            
            # Log inicio de acción
            logger.info(f"Iniciando acción: {action_type} - {func.__name__}", **context)
            
            try:
                # Ejecutar función
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Contexto de éxito
                success_context = {
                    **context,
                    "status": "success",
                    "execution_time_ms": round(execution_time * 1000, 2)
                }
                
                # Incluir resultado si se solicita
                if include_result and result is not None:
                    success_context["result"] = _sanitize_result(result)
                
                logger.info(f"Acción completada exitosamente: {action_type} - {func.__name__}", 
                           **success_context)
                
                return result
                
            except Exception as e:
                # Log de error
                error_context = {
                    **context,
                    "status": "error",
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
                
                logger.error(f"Error en acción: {action_type} - {func.__name__}", **error_context)
                raise
                
        return wrapper
    return decorator

def audit_user_action(action_description: str, sensitive: bool = False):
    """
    Decorador específico para auditoría de acciones de usuario.
    
    Args:
        action_description: Descripción de la acción para auditoría
        sensitive: Si es una acción sensible que requiere mayor detalle
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            audit_logger = get_audit_logger()
            
            # Contexto de auditoría
            audit_context = {
                "action": action_description,
                "function": func.__name__,
                "sensitive": sensitive,
                "timestamp": time.time()
            }
            
            # Obtener información de usuario si está disponible
            try:
                if current_user.is_authenticated:
                    audit_context.update({
                        "user_id": current_user.idUsuario,
                        "user_role": current_user.rol,
                        "user_email": current_user.email
                    })
            except:
                pass
            
            # Información de request si está disponible
            try:
                if request:
                    audit_context.update({
                        "ip_address": request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
                        "user_agent": request.headers.get('User-Agent'),
                        "endpoint": request.endpoint
                    })
            except:
                pass
            
            # Log antes de la acción
            audit_logger.info(f"AUDIT: {action_description}", **audit_context)
            
            try:
                result = func(*args, **kwargs)
                
                # Log éxito de auditoría
                audit_context["result_status"] = "success"
                audit_logger.info(f"AUDIT SUCCESS: {action_description}", **audit_context)
                
                return result
                
            except Exception as e:
                # Log fallo de auditoría
                audit_context.update({
                    "result_status": "failed",
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                audit_logger.warning(f"AUDIT FAILED: {action_description}", **audit_context)
                raise
                
        return wrapper
    return decorator

def monitor_performance(threshold_ms: float = 1000, alert_on_slow: bool = True):
    """
    Decorador para monitoreo de rendimiento de funciones.
    
    Args:
        threshold_ms: Umbral en milisegundos para considerar lenta la función
        alert_on_slow: Si alertar cuando la función excede el umbral
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            perf_logger = get_performance_logger()
            
            start_time = time.time()
            start_memory = _get_memory_usage()
            
            try:
                result = func(*args, **kwargs)
                
                # Calcular métricas
                execution_time = time.time() - start_time
                execution_time_ms = execution_time * 1000
                end_memory = _get_memory_usage()
                memory_delta = end_memory - start_memory if start_memory and end_memory else None
                
                # Contexto de rendimiento
                perf_context = {
                    "function": func.__name__,
                    "module": func.__module__,
                    "execution_time_ms": round(execution_time_ms, 2),
                    "execution_time_s": round(execution_time, 3),
                    "memory_usage_mb": end_memory,
                    "memory_delta_mb": memory_delta,
                    "threshold_ms": threshold_ms,
                    "is_slow": execution_time_ms > threshold_ms
                }
                
                # Log rendimiento
                if execution_time_ms > threshold_ms and alert_on_slow:
                    perf_logger.warning(f"Función lenta detectada: {func.__name__} - {execution_time_ms:.2f}ms", 
                                      **perf_context)
                else:
                    perf_logger.info(f"Rendimiento: {func.__name__} - {execution_time_ms:.2f}ms", 
                                   **perf_context)
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                execution_time_ms = execution_time * 1000
                
                error_context = {
                    "function": func.__name__,
                    "module": func.__module__,
                    "execution_time_ms": round(execution_time_ms, 2),
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "failed": True
                }
                
                perf_logger.error(f"Error en función monitoreada: {func.__name__}", **error_context)
                raise
                
        return wrapper
    return decorator

def log_security_event(event_type: str, risk_level: str = "medium"):
    """
    Decorador para eventos de seguridad.
    
    Args:
        event_type: Tipo de evento de seguridad
        risk_level: Nivel de riesgo (low, medium, high, critical)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            security_logger = get_security_logger()
            
            security_context = {
                "event_type": event_type,
                "risk_level": risk_level,
                "function": func.__name__,
                "module": func.__module__,
                "timestamp": time.time()
            }
            
            # Contexto de usuario y request
            try:
                if current_user.is_authenticated:
                    security_context.update({
                        "user_id": current_user.idUsuario,
                        "user_role": current_user.rol
                    })
                
                if request:
                    security_context.update({
                        "ip_address": request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
                        "user_agent": request.headers.get('User-Agent'),
                        "endpoint": request.endpoint,
                        "method": request.method
                    })
            except:
                pass
            
            # Log evento de seguridad
            log_level = "warning" if risk_level in ["medium", "high"] else "critical" if risk_level == "critical" else "info"
            
            getattr(security_logger, log_level)(f"SECURITY EVENT: {event_type}", **security_context)
            
            try:
                result = func(*args, **kwargs)
                
                # Log éxito del evento de seguridad
                security_context["result"] = "success"
                security_logger.info(f"SECURITY EVENT SUCCESS: {event_type}", **security_context)
                
                return result
                
            except Exception as e:
                # Log fallo del evento de seguridad
                security_context.update({
                    "result": "failed",
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                security_logger.error(f"SECURITY EVENT FAILED: {event_type}", **security_context)
                raise
                
        return wrapper
    return decorator

# Funciones de utilidad

def _sanitize_args(args: tuple, kwargs: dict) -> dict:
    """Sanitiza argumentos removiendo información sensible."""
    safe_kwargs = {}
    sensitive_keys = ['password', 'passwd', 'token', 'secret', 'key', 'auth', 'credential']
    
    for key, value in kwargs.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            safe_kwargs[key] = "[REDACTED]"
        elif isinstance(value, (str, int, float, bool)):
            safe_kwargs[key] = value
        else:
            safe_kwargs[key] = str(type(value))
    
    return {
        "args_count": len(args),
        "kwargs": safe_kwargs
    }

def _sanitize_result(result: Any) -> Any:
    """Sanitiza resultado para logging seguro."""
    if isinstance(result, (str, int, float, bool)):
        return result
    elif isinstance(result, dict):
        return {k: v for k, v in result.items() if not any(sensitive in str(k).lower() 
                for sensitive in ['password', 'token', 'secret'])}
    else:
        return str(type(result))

def _get_memory_usage() -> Optional[float]:
    """Obtiene uso de memoria actual en MB."""
    try:
        import psutil
        process = psutil.Process()
        return round(process.memory_info().rss / 1024 / 1024, 2)
    except ImportError:
        return None

# Decoradores específicos comunes

def log_admin_action(action_description: str):
    """Decorador específico para acciones de administrador."""
    return audit_user_action(f"ADMIN: {action_description}", sensitive=True)

def log_data_modification(entity_type: str):
    """Decorador para modificaciones de datos."""
    return audit_user_action(f"DATA_MODIFICATION: {entity_type}", sensitive=True)

def log_authentication_event(event_type: str):
    """Decorador para eventos de autenticación."""
    return log_security_event(f"AUTH: {event_type}", risk_level="high")

def log_business_operation(operation_name: str):
    """Decorador para operaciones de negocio importantes."""
    return log_action(f"BUSINESS: {operation_name}", logger_type="business", include_args=True)
