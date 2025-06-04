"""
Middleware para logging automático de requests HTTP.
Captura automáticamente todas las requests y las registra en el sistema de logging estructurado.
"""

import time
from flask import request, g, current_app
from flask_login import current_user
from app.utils.logging_config import StructuredLogger

class RequestLoggingMiddleware:
    """Middleware que registra automáticamente todas las requests HTTP."""
    
    def __init__(self, app=None):
        self.app = app
        self.logger = StructuredLogger('security')
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa el middleware con la aplicación Flask."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_appcontext(self.teardown_request)
    
    def before_request(self):
        """Se ejecuta antes de cada request."""
        g.start_time = time.time()
        
        # Obtener información básica de la request
        request_info = {
            "method": request.method,
            "endpoint": request.endpoint,
            "url": request.url,
            "path": request.path,
            "remote_addr": request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
            "user_agent": request.headers.get('User-Agent'),
            "referrer": request.headers.get('Referer'),
        }
        
        # Información del usuario si está autenticado
        user_info = {
            "user_id": "anonymous",
            "user_role": "none"
        }
        
        try:
            if current_user.is_authenticated:
                user_info = {
                    "user_id": current_user.idUsuario,
                    "user_role": current_user.rol
                }
        except:
            pass
        
        # Solo loggear ciertos tipos de requests o requests sensibles
        if self._should_log_request():
            self.logger.info("Request iniciada", 
                           request_info=request_info,
                           user_info=user_info,
                           request_id=id(request))
    
    def after_request(self, response):
        """Se ejecuta después de cada request."""
        try:
            if hasattr(g, 'start_time'):
                duration = time.time() - g.start_time
                
                # Información de la respuesta
                response_info = {
                    "status_code": response.status_code,
                    "content_length": response.content_length,
                    "content_type": response.headers.get('Content-Type'),
                    "duration_ms": round(duration * 1000, 2)
                }
                
                # Solo loggear responses relevantes
                if self._should_log_response(response):
                    log_level = self._get_log_level_for_status(response.status_code)
                    
                    getattr(self.logger, log_level)(
                        f"Request completada - {response.status_code}",
                        response_info=response_info,
                        request_id=id(request)
                    )
        except Exception as e:
            # No dejar que errores de logging rompan la aplicación
            current_app.logger.error(f"Error en request logging: {e}")
        
        return response
    
    def teardown_request(self, exception):
        """Se ejecuta al finalizar el contexto de la request."""
        if exception:
            # Loggear excepciones no manejadas
            self.logger.error("Excepción no manejada en request",
                            exception_type=type(exception).__name__,
                            exception_message=str(exception),
                            request_id=id(request))
    
    def _should_log_request(self):
        """Determina si una request debe ser loggeada."""
        # No loggear requests a archivos estáticos
        if request.endpoint and request.endpoint.startswith('static'):
            return False
        
        # No loggear requests de health check o similar
        if request.path in ['/health', '/ping', '/favicon.ico']:
            return False
        
        # Loggear requests POST, PUT, DELETE (modificaciones)
        if request.method in ['POST', 'PUT', 'DELETE']:
            return True
        
        # Loggear requests a endpoints administrativos
        if request.endpoint and ('admin' in request.endpoint or 'auth' in request.endpoint):
            return True
        
        # Para otras requests GET, solo loggear ocasionalmente o en debug
        return current_app.debug
    
    def _should_log_response(self, response):
        """Determina si una response debe ser loggeada."""
        # Siempre loggear errores
        if response.status_code >= 400:
            return True
        
        # Loggear respuestas a requests que fueron loggeadas
        return self._should_log_request()
    
    def _get_log_level_for_status(self, status_code):
        """Obtiene el nivel de log apropiado según el status code."""
        if status_code < 400:
            return 'info'
        elif status_code < 500:
            return 'warning'
        else:
            return 'error'

def setup_request_logging(app):
    """Configura el middleware de logging de requests."""
    middleware = RequestLoggingMiddleware(app)
    return middleware
