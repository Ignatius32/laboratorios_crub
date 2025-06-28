"""
Sistema de logging estructurado para CRUB Laboratory Management System.
Implementa logging en formato JSON con contexto completo y categorización por tipos.
"""

import os
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Any, Optional
from flask import request, g, current_app
from flask_login import current_user
import threading
import traceback

class StructuredJSONFormatter(logging.Formatter):
    """
    Formateador personalizado que genera logs en formato JSON estructurado.
    Incluye contexto de usuario, request, y sistema.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        # Estructura base del log
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S'),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "user": self._get_user_context(),
            "request": self._get_request_context(),
            "context": {
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "process_id": os.getpid(),
                "thread_id": threading.get_ident()
            }
        }
        
        # Agregar contexto adicional si existe
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
            
        # Agregar información de excepción si existe
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
            
        return json.dumps(log_data, ensure_ascii=False, default=str)
    
    def _get_user_context(self) -> Dict[str, Any]:
        """Obtiene contexto del usuario actual."""
        try:
            if current_user.is_authenticated:
                return {
                    "id": current_user.idUsuario,
                    "role": current_user.rol,
                    "email": current_user.email
                }
            else:
                return {"id": "Anonymous", "role": "None", "email": "N/A"}
        except:
            return {"id": "System", "role": "System", "email": "System"}
    
    def _get_request_context(self) -> Dict[str, Any]:
        """Obtiene contexto de la request HTTP actual."""
        try:
            if request:
                return {
                    "ip": request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
                    "method": request.method,
                    "endpoint": request.endpoint,
                    "url": request.url,
                    "user_agent": request.headers.get('User-Agent', 'Unknown')
                }
        except:
            pass
        
        return {
            "ip": "N/A",
            "method": "N/A", 
            "endpoint": "N/A",
            "url": "N/A",
            "user_agent": "N/A"
        }

class LoggerManager:
    """Gestiona la configuración y acceso a diferentes tipos de loggers."""
    
    def __init__(self):
        self.loggers = {}
        self.log_dir = None
        
    def setup_logging(self, app):
        """Configura el sistema de logging para la aplicación."""
        
        # Configuración básica
        self.log_dir = app.config.get('LOG_DIR', 'logs')
        log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper())
        
        # Crear directorio de logs
        try:
            os.makedirs(self.log_dir, exist_ok=True)
        except PermissionError:
            # Fallback to /tmp if can't create logs directory
            self.log_dir = '/tmp/laboratorios-crub-logs'
            os.makedirs(self.log_dir, exist_ok=True)
        
        # Configurar logger principal de la aplicación
        self._setup_app_logger(app, log_level)
        
        # Configurar loggers especializados
        self._setup_specialized_loggers(log_level)
        
        # Configurar loggers de terceros
        self._setup_third_party_loggers()
        
        # Log inicial
        app.logger.info("Sistema de logging inicializado - Nivel: %s", app.config.get('LOG_LEVEL', 'INFO'))
        
    def _setup_app_logger(self, app, log_level):
        """Configura el logger principal de la aplicación."""
        
        # Remover handlers existentes
        app.logger.handlers.clear()
        
        # Handler para logs estructurados
        structured_handler = logging.handlers.RotatingFileHandler(
            os.path.join(self.log_dir, 'app_structured.log'),
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        structured_handler.setLevel(log_level)
        structured_handler.setFormatter(StructuredJSONFormatter())
        
        # Handler para logs tradicionales (backup)
        traditional_handler = logging.handlers.RotatingFileHandler(
            os.path.join(self.log_dir, 'app.log'),
            maxBytes=10485760,
            backupCount=5
        )
        traditional_handler.setLevel(log_level)
        traditional_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        traditional_handler.setFormatter(traditional_formatter)
        
        # Handler para consola en desarrollo
        if app.debug:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            app.logger.addHandler(console_handler)
        
        # Agregar handlers
        app.logger.addHandler(structured_handler)
        app.logger.addHandler(traditional_handler)
        app.logger.setLevel(log_level)
        
    def _setup_specialized_loggers(self, log_level):
        """Configura loggers especializados por categoría."""
        
        specialized_loggers = {
            'security': {
                'filename': 'security.log',
                'structured_filename': 'security_structured.log',
                'level': logging.WARNING
            },
            'audit': {
                'filename': 'audit.log', 
                'structured_filename': 'audit_structured.log',
                'level': logging.INFO
            },
            'business': {
                'filename': 'business.log',
                'structured_filename': 'business_structured.log', 
                'level': logging.INFO
            },
            'database': {
                'filename': 'database.log',
                'structured_filename': 'database_structured.log',
                'level': logging.WARNING
            },
            'performance': {
                'filename': 'performance.log',
                'structured_filename': 'performance_structured.log',
                'level': logging.INFO
            }
        }
        
        for logger_name, config in specialized_loggers.items():
            logger = logging.getLogger(f'crub.{logger_name}')
            logger.handlers.clear()
            logger.setLevel(config['level'])
            
            # Handler estructurado
            structured_handler = logging.handlers.RotatingFileHandler(
                os.path.join(self.log_dir, config['structured_filename']),
                maxBytes=10485760,
                backupCount=20 if logger_name == 'audit' else 10
            )
            structured_handler.setLevel(config['level'])
            structured_handler.setFormatter(StructuredJSONFormatter())
            
            # Handler tradicional
            traditional_handler = logging.handlers.RotatingFileHandler(
                os.path.join(self.log_dir, config['filename']),
                maxBytes=10485760,
                backupCount=10 if logger_name == 'audit' else 5
            )
            traditional_handler.setLevel(config['level'])
            traditional_formatter = logging.Formatter(
                f'%(asctime)s - {logger_name.upper()} - %(levelname)s - %(message)s'
            )
            traditional_handler.setFormatter(traditional_formatter)
            
            logger.addHandler(structured_handler)
            logger.addHandler(traditional_handler)
            
            self.loggers[logger_name] = logger
            
    def _setup_third_party_loggers(self):
        """Configura loggers de librerías de terceros."""
        
        # Reducir verbosidad de loggers de terceros
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        
    def get_logger(self, name: str) -> logging.Logger:
        """Obtiene un logger especializado."""
        return self.loggers.get(name, logging.getLogger(f'crub.{name}'))

# Instancia global del manager
logger_manager = LoggerManager()

class StructuredLogger:
    """
    Interfaz simplificada para logging estructurado con contexto.
    """
    
    def __init__(self, logger_name: str = 'app'):
        if logger_name == 'app':
            self.logger = logging.getLogger('app')
        else:
            self.logger = logger_manager.get_logger(logger_name)
    
    def info(self, message: str, **kwargs):
        """Log de información con contexto adicional."""
        self._log(logging.INFO, message, **kwargs)
        
    def warning(self, message: str, **kwargs):
        """Log de advertencia con contexto adicional."""
        self._log(logging.WARNING, message, **kwargs)
        
    def error(self, message: str, **kwargs):
        """Log de error con contexto adicional."""
        self._log(logging.ERROR, message, **kwargs)
        
    def debug(self, message: str, **kwargs):
        """Log de debug con contexto adicional."""
        self._log(logging.DEBUG, message, **kwargs)
        
    def critical(self, message: str, **kwargs):
        """Log crítico con contexto adicional."""
        self._log(logging.CRITICAL, message, **kwargs)
        
    def _log(self, level: int, message: str, **kwargs):
        """Método interno para logging con contexto adicional."""
        if kwargs:
            # Crear un LogRecord personalizado con datos extra
            record = self.logger.makeRecord(
                self.logger.name, level, "", 0, message, (), None
            )
            record.extra_data = kwargs
            self.logger.handle(record)
        else:
            self.logger.log(level, message)

# Loggers especializados listos para usar
def get_app_logger() -> StructuredLogger:
    """Logger principal de la aplicación."""
    return StructuredLogger('app')

def get_security_logger() -> StructuredLogger:
    """Logger para eventos de seguridad."""
    return StructuredLogger('security')

def get_audit_logger() -> StructuredLogger:
    """Logger para auditoría de acciones de usuario."""
    return StructuredLogger('audit')

def get_business_logger() -> StructuredLogger:
    """Logger para lógica de negocio."""
    return StructuredLogger('business')

def get_database_logger() -> StructuredLogger:
    """Logger para operaciones de base de datos."""
    return StructuredLogger('database')

def get_performance_logger() -> StructuredLogger:
    """Logger para métricas de rendimiento."""
    return StructuredLogger('performance')

def setup_logging(app):
    """Función principal para inicializar el sistema de logging."""
    logger_manager.setup_logging(app)
    return logger_manager
