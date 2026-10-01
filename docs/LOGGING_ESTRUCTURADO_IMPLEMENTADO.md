# Sistema de Logging Estructurado - CRUB Laboratory Management

## 🎯 Resumen

Se ha implementado un sistema de logging estructurado completo en formato JSON que resuelve la **falta de logging estructurado** identificada en el análisis del proyecto. Este sistema proporciona trazabilidad completa, auditoría detallada y monitoreo de rendimiento.

## ✨ Características Implementadas

### 1. **Logging Estructurado en JSON**
- Formato JSON consistente para todos los logs
- Contexto automático de usuario, request y sistema
- Metadatos enriquecidos para análisis posterior
- Compatibilidad con herramientas de análisis como ELK Stack

### 2. **Loggers Especializados**
- **Aplicación** (`app_structured.log`): Logs generales de la aplicación
- **Seguridad** (`security_structured.log`): Eventos de autenticación, acceso, tokens
- **Auditoría** (`audit_structured.log`): Acciones de usuario, modificaciones de datos
- **Negocio** (`business_structured.log`): Operaciones de negocio, cálculos de stock
- **Base de datos** (`database_structured.log`): Consultas lentas, errores de BD
- **Rendimiento** (`performance_structured.log`): Métricas de tiempo, memoria

### 3. **Decoradores de Logging**
Facilitan el uso del sistema sin modificar lógica de negocio:
```python
@log_admin_action("crear usuario")
@audit_user_action("modificación de producto", sensitive=True)
@monitor_performance(threshold_ms=1000)
@log_business_operation("crear movimiento en laboratorio")
```

> `log_security_event` y `log_authentication_event` ya no existen: no los usaba
> ninguna ruta y se eliminaron. Los eventos de seguridad se registran
> directamente con `get_security_logger()`, como hacen `app/routes/auth.py` y
> `app/utils/keycloak_auth.py`.

### 4. **Middleware de Request Logging**
- Captura automática de todas las requests HTTP
- Logging de duración, status codes, IPs
- Contexto de usuario automático
- Filtrado inteligente para evitar ruido

## 🏗️ Arquitectura

```
app/utils/
├── logging_config.py          # Configuración principal y formateadores
├── logging_decorators.py      # Decoradores para uso fácil
└── request_logging.py         # Middleware para requests HTTP

logs/
├── app_structured.log         # Logs generales (JSON)
├── security_structured.log    # Eventos de seguridad (JSON)
├── audit_structured.log       # Auditoría de acciones (JSON)
├── business_structured.log    # Operaciones de negocio (JSON)
├── database_structured.log    # Eventos de base de datos (JSON)
├── performance_structured.log # Métricas de rendimiento (JSON)
├── app.log                    # Backup en formato tradicional
├── security.log              # Backup seguridad
├── audit.log                 # Backup auditoría
└── [otros].log               # Otros backups
```

## 📊 Formato de Log Estructurado

Cada entrada de log incluye:

```json
{
  "timestamp": "2025-05-29 15:30:45",
  "level": "INFO",
  "logger": "crub.business",
  "message": "Producto creado exitosamente",
  "user": {
    "id": "ADMIN001",
    "role": "admin",
    "email": "admin@crub.edu.ar"
  },
  "request": {
    "ip": "192.168.1.100",
    "method": "POST",
    "endpoint": "admin.new_producto",
    "url": "https://lab.crub.edu.ar/admin/productos/new",
    "user_agent": "Mozilla/5.0..."
  },
  "context": {
    "module": "admin",
    "function": "new_producto",
    "line": 245,
    "process_id": 1234,
    "thread_id": 5678
  },
  "action_type": "BUSINESS: crear_producto",
  "entity_type": "producto",
  "entity_id": "PROD_2025_001"
}
```

## 🚀 Uso del Sistema

### Uso Básico
```python
from app.utils.logging_config import StructuredLogger

logger = StructuredLogger('business')
logger.info("Operación completada", 
           product_id="PROD001",
           quantity=25,
           laboratory_id="LAB_QUIMICA")
```

### Loggers Especializados
```python
from app.utils.logging_config import (
    get_audit_logger,
    get_security_logger,
    get_business_logger,
    get_performance_logger
)

# Auditoría
audit_logger = get_audit_logger()
audit_logger.info("Usuario creado", user_id="USR001", created_by="ADMIN001")

# Seguridad
security_logger = get_security_logger()
security_logger.warning("Intento de login fallido", email="user@test.com", attempts=3)

# Negocio
business_logger = get_business_logger()
business_logger.info("Stock calculado", laboratory_id="LAB001", products=150)
```

### Decoradores
```python
from app.utils.logging_decorators import *

@log_admin_action("crear laboratorio")
def create_laboratory(name, code):
    # Tu lógica aquí
    pass

@audit_user_action("eliminar producto", sensitive=True)
def delete_product(product_id):
    # Tu lógica aquí
    pass

@monitor_performance(threshold_ms=500)
def complex_calculation():
    # Tu lógica aquí
    pass
```

## 🔧 Configuración

### Variables de Entorno
```env
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR=logs           # Directorio de logs
```

### En config.py
```python
class Config:
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = os.environ.get('LOG_DIR', 'logs')
```

## 📈 Beneficios Implementados

### 1. **Trazabilidad Completa**
- Cada acción tiene contexto completo de usuario, request y sistema
- IDs de correlación para seguir operaciones complejas
- Timestamps precisos para análisis temporal

### 2. **Auditoría Detallada**
- Registro automático de acciones administrativas
- Seguimiento de modificaciones de datos sensibles
- Contexto de seguridad para investigaciones

### 3. **Monitoreo de Rendimiento**
- Detección automática de operaciones lentas
- Métricas de tiempo de ejecución
- Alertas configurables por umbral

### 4. **Análisis y Alertas**
- Formato JSON para herramientas de análisis
- Separación por categorías para procesamiento específico
- Base para implementar alertas automáticas

## 🔍 Mejoras vs Sistema Anterior

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| Formato | Texto plano inconsistente | JSON estructurado |
| Contexto | Información limitada | Contexto completo automático |
| Categorización | Un solo archivo | 6 categorías especializadas |
| Facilidad de uso | Manual y verboso | Decoradores automáticos |
| Análisis | Difícil de procesar | Fácil análisis automático |
| Auditoría | Limitada | Completa y detallada |
| Rendimiento | Sin métricas | Monitoreo automático |
| Integración | Ninguna | Lista para ELK/Grafana |

## 🧪 Verificación

Para probar el sistema:

```bash
# Verificar logs generados
ls -la logs/
tail -f logs/app_structured.log
```

## 📋 Implementación en Rutas Existentes

### Ya Implementado:
- ✅ Rutas de autenticación (`auth.py`)
- ✅ Importación de productos (`admin.py`)
- ✅ Middleware de requests automático

### Próximos Pasos Recomendados:
1. Agregar decoradores a rutas críticas de admin
2. Implementar logging en operaciones de stock
3. Agregar métricas de rendimiento a consultas complejas
4. Configurar alertas para eventos de seguridad

## 🔗 Integración con Herramientas Externas

El formato JSON estructurado facilita la integración con:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Grafana** para dashboards
- **Prometheus** para métricas
- **Splunk** para análisis avanzado
- **Alertmanager** para notificaciones

## 📚 Documentación Adicional

- `app/utils/logging_config.py` - Configuración principal
- `app/utils/logging_decorators.py` - Decoradores disponibles
- `app/utils/request_logging.py` - Middleware que registra las requests

> No hay pruebas automatizadas del logging. Las que había
> (`test_logging.py`, `test_complete_logging_system.py`) no funcionaban y se
> retiraron; ver `tests/README.md`, que describe qué haría falta cubrir.

---

## ✅ Resolución del Problema

**PROBLEMA RESUELTO**: ✅ **Falta de logging estructurado**

El sistema anterior tenía logging básico y genérico. Ahora se cuenta con:
- 📊 Logging estructurado en JSON
- 🔍 6 categorías especializadas de logs
- 🎯 Decoradores para facilitar el uso
- 🚦 Middleware automático de requests
- 📈 Monitoreo de rendimiento integrado
- 🔒 Auditoría completa de seguridad
- 🔗 Base para herramientas de análisis

El sistema proporciona la visibilidad y trazabilidad necesarias para un entorno de producción profesional.
