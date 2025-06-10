# Implementación de Ficha de Seguridad con Google Drive

## Resumen de Cambios Implementados

Se ha implementado la funcionalidad para subir y visualizar fichas de seguridad de productos utilizando Google Drive como almacenamiento.

### 🔧 Archivos Modificados

#### 1. `app/routes/tecnicos.py`
- **Nuevos imports**: Agregado `base64`, `flask_wtf.file.FileAllowed`, `werkzeug.utils.secure_filename`
- **Formulario `ProductoTecnicoForm`**: 
  - Cambiado `urlFichaSeguridad` (StringField) por `fichaSeguridad` (FileField)
  - Agregados campos `stockMinimo` y `marca`
  - Agregado validador para tipos de archivo (PDF, JPG, PNG)
- **Función `new_producto`**:
  - Agregada lógica para procesar archivos subidos
  - Conversión a base64 para envío a Google Drive
  - Manejo de errores de subida
  - Almacenamiento del ID del archivo en la base de datos

#### 2. `app/integrations/google_drive.py`
- **Método `upload_ficha_seguridad`**: Nueva función para subir archivos a la carpeta específica de fichas de seguridad
- Configuración para carpeta destino: `1ZsUxrJp9-rKkLs5gklVSKo_fjIoHVpRQ`
- Formato de nombre: `ficha_seg_{idProducto}.{extension}`

#### 3. `app.gs` (Google Apps Script)
- **Función `handleUploadFichaSeguridad`**: Maneja la subida de archivos al Google Drive
- **Función `getMimeType`**: Determina el tipo MIME basado en la extensión
- Configuración de permisos para visualización pública
- Retorna ID del archivo y URL de visualización

#### 4. `app/templates/tecnicos/productos/form.html`
- Agregado `enctype="multipart/form-data"` al formulario
- Cambiado campo de URL por campo de archivo
- Agregados campos de Stock Mínimo y Marca
- Agregado texto de ayuda para tipos de archivo permitidos

#### 5. `app/templates/tecnicos/productos/view.html`
- **Modal de visualización**: Nuevo modal para mostrar la ficha de seguridad
- **iframe embebido**: Para visualizar PDFs directamente
- **Compatibilidad**: Soporte para URLs existentes y nuevos IDs de Google Drive
- **JavaScript**: Gestión del modal, carga de archivos, y enlaces de descarga

### 📋 Funcionalidades Implementadas

#### ✅ Subida de Archivos
- Campo de archivo en el formulario de creación de productos
- Validación de tipos: PDF, JPG, JPEG, PNG
- Conversión automática a base64 para transmisión
- Nomenclatura estandarizada: `ficha_seg_{idProducto}.{extension}`

#### ✅ Almacenamiento en Google Drive
- Carpeta específica para fichas de seguridad
- Configuración de permisos de visualización
- Retorno de ID único para referencia en base de datos

#### ✅ Visualización
- Modal responsive con iframe embebido
- Spinner de carga mientras se carga el documento
- Botón de descarga directa
- Compatibilidad con productos existentes (URLs completas)

#### ✅ Compatibilidad hacia atrás
- Productos con URLs existentes siguen funcionando
- Detección automática entre URLs completas e IDs de Drive
- Sin necesidad de migración de datos existentes

### 🛠️ Configuración Requerida

#### Variables de Entorno
```bash
GOOGLE_SCRIPT_URL=https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec
GOOGLE_DRIVE_SECURE_TOKEN=your_secure_token
```

#### Google Apps Script
1. Copiar el código de `app.gs` a Google Apps Script
2. Configurar el token de seguridad en Properties Service
3. Desplegar como aplicación web con permisos apropiados
4. Configurar acceso a Google Drive API

### 🧪 Pruebas

Ejecutar el script de prueba:
```bash
python test_ficha_seguridad.py
```

Este script verificará:
- Configuración de la integración
- Capacidad de subida de archivos
- Conexión con Google Apps Script

### 📝 Uso

#### Para Técnicos
1. **Crear Producto**: Usar el campo "Ficha de Seguridad" para subir archivo PDF o imagen
2. **Ver Producto**: Hacer clic en "Ver Ficha de Seguridad" para abrir modal con visualización
3. **Descargar**: Usar el botón "Descargar" en el modal

#### Para Administradores
- La funcionalidad está disponible tanto para técnicos como administradores
- Los archivos se almacenan centralizadamente en Google Drive
- Los IDs se guardan en el campo `urlFichaSeguridad` del modelo `Producto`

### 🔐 Seguridad

- Validación de tipos de archivo en frontend y backend
- Token de seguridad para comunicación con Google Apps Script
- Archivos almacenados con permisos de solo lectura
- Nomenclatura estandarizada previene conflictos

### 📊 Estructura de Archivos en Google Drive

```
Fichas de Seguridad (ID: 1ZsUxrJp9-rKkLs5gklVSKo_fjIoHVpRQ)
├── ficha_seg_PROD001.pdf
├── ficha_seg_PROD002.jpg
├── ficha_seg_PROD003.png
└── ...
```

### 🚀 Próximos Pasos

1. **Validación adicional**: Implementar validación de tamaño máximo de archivo
2. **Compresión**: Agregar compresión automática para imágenes grandes
3. **Versionado**: Permitir múltiples versiones de fichas de seguridad
4. **Búsqueda**: Indexación de contenido de PDFs para búsqueda
5. **Notificaciones**: Alertas cuando se actualicen fichas de seguridad

### ⚠️ Consideraciones

- Los archivos grandes pueden tomar tiempo en subir
- La visualización de PDFs depende del navegador del usuario
- Requiere conexión a internet para visualizar archivos
- El almacenamiento está limitado por la cuenta de Google Drive configurada
