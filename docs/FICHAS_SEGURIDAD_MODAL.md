# Modal de Fichas de Seguridad - Documentación

## Descripción
Este sistema implementa un modal global para visualizar fichas de seguridad de productos químicos almacenadas en Google Drive. El modal está disponible en toda la aplicación y soporta múltiples tipos de archivo.

## Características

### 🔍 Tipos de archivo soportados
- **PDF**: Visualización completa con controles de navegación
- **DOC/DOCX**: Visualización mediante iframe
- **JPG/JPEG/PNG/GIF**: Visualización de imágenes optimizada
- **Otros**: Mensaje informativo con enlace de descarga

### 🛡️ Funcionalidades de seguridad
- Validación de URLs de Google Drive
- Manejo de errores robusto
- Contenido embebido sin redirecciones externas
- Indicadores visuales de estado

### 📱 Diseño responsivo
- Modal adaptativo a diferentes tamaños de pantalla
- Controles optimizados para dispositivos móviles
- Scrollbar personalizado
- Transiciones suaves

## Implementación

### HTML del Modal
El modal está incluido globalmente en `base.html`:

```html
<!-- Modal global para visualizar fichas de seguridad -->
<div class="modal fade" id="fichasSeguridadModal" tabindex="-1" aria-labelledby="fichasSeguridadModalLabel" aria-hidden="true">
    <!-- Estructura completa del modal -->
</div>
```

### CSS
Estilos específicos en `static/css/fichas-seguridad.css`:
- Diseño responsivo
- Animaciones y transiciones
- Personalización de componentes Bootstrap

### JavaScript
Funciones principales disponibles globalmente:

#### `showFichaSeguridad(driveId, nombreProducto, tipoArchivo)`
Función principal para mostrar una ficha de seguridad.

**Parámetros:**
- `driveId` (string): ID del archivo en Google Drive
- `nombreProducto` (string): Nombre del producto químico  
- `tipoArchivo` (string, opcional): Tipo de archivo ('pdf', 'doc', 'docx', 'jpg', etc.)

**Ejemplo:**
```javascript
showFichaSeguridad('1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms', 'Ácido Sulfúrico', 'pdf');
```

#### `mostrarFichaSeguridadDesdeUrl(url, nombreProducto, tipoArchivo)`
Función auxiliar que extrae el ID de Google Drive de una URL completa.

**Parámetros:**
- `url` (string): URL completa de Google Drive
- `nombreProducto` (string): Nombre del producto químico
- `tipoArchivo` (string, opcional): Tipo de archivo

**Ejemplo:**
```javascript
mostrarFichaSeguridadDesdeUrl(
    'https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view',
    'Ácido Sulfúrico'
);
```

## Integración en Templates

### En listas de productos
```html
{% if producto.urlFichaSeguridad %}
<button type="button" class="btn btn-sm btn-warning" title="Ver ficha de seguridad" 
        onclick="mostrarFichaSeguridadDesdeUrl('{{ producto.urlFichaSeguridad }}', '{{ producto.nombre }}')">
    <i class="fas fa-shield-alt"></i>
</button>
{% endif %}
```

### En vista detallada de producto
```html
{% if producto.urlFichaSeguridad %}
<button type="button" class="btn btn-warning" 
        onclick="mostrarFichaSeguridadDesdeUrl('{{ producto.urlFichaSeguridad }}', '{{ producto.nombre }}')">
    <i class="fas fa-shield-alt me-2"></i> Ver Ficha de Seguridad
</button>
{% endif %}
```

### Indicador de estado
```html
{% if producto.urlFichaSeguridad %}
    <span class="badge bg-success" title="Ficha de seguridad disponible">
        <i class="fas fa-shield-alt me-1"></i>Disponible
    </span>
{% else %}
    <span class="badge bg-warning text-dark" title="Ficha de seguridad no configurada">
        <i class="fas fa-exclamation-triangle me-1"></i>No disponible
    </span>
{% endif %}
```

## Configuración en la Base de Datos

El campo `urlFichaSeguridad` en la tabla `producto` debe contener:
- URL completa de Google Drive
- Solo el ID del archivo
- Debe ser accesible a través del endpoint `/descargar_archivo_drive/{driveId}`

### Ejemplos de URLs válidas:
```
https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view
https://drive.google.com/open?id=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
```

## Endpoint Backend Requerido

El sistema asume que existe un endpoint backend:

```
GET /descargar_archivo_drive/{driveId}
```

Este endpoint debe:
1. Validar permisos del usuario
2. Descargar el archivo desde Google Drive
3. Servir el archivo con los headers correctos
4. Manejar errores de archivos no encontrados

## Manejo de Errores

### Casos manejados:
- **URL no válida**: Muestra mensaje de error en el modal
- **Archivo no encontrado**: Error en la carga del iframe/imagen
- **Sin ficha configurada**: Badge indicativo y botón deshabilitado
- **Tipo de archivo no soportado**: Mensaje con enlace de descarga

### Mensajes de error:
- "No se ha configurado una ficha de seguridad para este producto"
- "URL de ficha de seguridad no válida. Contacte al administrador"
- "Error al cargar la imagen de la ficha de seguridad"
- "Error técnico al cargar la ficha de seguridad"

## Mejoras Futuras

### Funcionalidades adicionales sugeridas:
1. **Cache local**: Almacenar documentos descargados temporalmente
2. **Zoom y navegación**: Controles avanzados para PDFs
3. **Historial**: Registro de fichas consultadas
4. **Impresión**: Funcionalidad de impresión directa
5. **Anotaciones**: Permitir comentarios y marcas en las fichas
6. **Versiones**: Control de versiones de fichas de seguridad
7. **Notificaciones**: Alertas sobre fichas vencidas o actualizadas

### Optimizaciones técnicas:
- **Lazy loading**: Cargar contenido solo cuando sea necesario
- **Prefetch**: Pre-cargar fichas frecuentemente consultadas
- **Compresión**: Optimizar tamaño de archivos
- **PWA**: Soporte offline para fichas críticas

## Seguridad

### Consideraciones implementadas:
- Validación de URLs en frontend
- Sanitización de parámetros
- Control de acceso a través del backend
- Prevención de inyección de código

### Recomendaciones adicionales:
- Validar permisos por laboratorio
- Auditoría de acceso a fichas
- Encriptación de URLs sensibles
- Rate limiting en el endpoint de descarga

## Soporte y Mantenimiento

### Logs importantes:
- Errores de carga en consola del navegador
- Requests fallidos al endpoint de descarga
- URLs mal formadas

### Testing:
- Probar con diferentes tipos de archivo
- Verificar responsive design
- Validar manejo de errores
- Testear performance con archivos grandes

---

**Nota**: Esta implementación asume que el sistema de Google Drive y el endpoint de descarga están correctamente configurados y funcionando.
