# Implementación de Auditoría de Usuarios

## Resumen
Se ha implementado un sistema de auditoría que registra qué usuario creó cada producto y cada movimiento en el sistema.

## Cambios Realizados

### 1. Modelo de Datos (`models.py`)

#### Tabla `Producto`
- ✅ Agregado campo `created_by` (FK a Usuario)
- ✅ Agregado campo `created_at` (DateTime)
- ✅ Agregada relación `creador` con la tabla Usuario

#### Tabla `Movimiento`
- ✅ Agregado campo `created_by` (FK a Usuario)
- ✅ Agregada relación `creador` con la tabla Usuario

### 2. Rutas Actualizadas

#### `admin.py`
- ✅ `new_producto()`: Captura `current_user.idUsuario` al crear productos
- ✅ `new_movimiento()`: Captura `current_user.idUsuario` al crear movimientos
- ✅ Movimientos de transferencia: Ambos movimientos (origen y destino) registran el creador

#### `tecnicos.py`
- ✅ `new_producto_en_lab()`: Captura usuario en producto y movimiento inicial
- ✅ `new_movimiento()`: Captura usuario al crear movimientos
- ✅ Movimientos de transferencia: Ambos movimientos registran el creador

### 3. Vistas Actualizadas

#### Lista de Movimientos (`admin/movimientos/list.html`)
- ✅ Nueva columna "Creado por" en la tabla
- ✅ Muestra nombre completo del usuario
- ✅ Tooltip con email del usuario
- ✅ Mensaje "No registrado" para movimientos antiguos

#### Vista de Producto (`admin/productos/view.html`)
- ✅ Sección "Creado por" con nombre y email del usuario
- ✅ Fecha de creación del producto
- ✅ Mensaje "No registrado" para productos existentes

### 4. Migración de Base de Datos

Se creó el script `migrations/add_audit_fields.py` que:
- ✅ Agrega columna `created_by` a la tabla `producto`
- ✅ Agrega columna `created_at` a la tabla `producto`
- ✅ Agrega columna `created_by` a la tabla `movimiento`
- ✅ Maneja registros existentes (tendrán `created_by = NULL`)
- ✅ Compatible con SQLite

## Funcionalidad

### Para Productos
- Al crear un nuevo producto, se guarda automáticamente quién lo creó
- En la vista de detalles del producto, el admin puede ver:
  - Nombre completo del creador
  - Email del creador
  - Fecha de creación

### Para Movimientos
- Al crear cualquier movimiento (ingreso, compra, uso, transferencia), se guarda quién lo creó
- En la lista de movimientos, cada registro muestra:
  - Nombre completo del usuario que lo creó
  - Email en tooltip al pasar el mouse
- Para transferencias, ambos movimientos (origen y destino) registran el mismo usuario

### Registros Existentes
- Los productos y movimientos creados antes de esta implementación mostrarán "No registrado"
- Todos los nuevos registros tendrán la información del usuario

## Cómo Usar

### Ejecutar Migración
```bash
python migrations/add_audit_fields.py
```

### Ver Información de Auditoría

**En productos:**
1. Ir a Admin → Productos
2. Click en "Ver detalles" de cualquier producto
3. Ver sección "Creado por" al final de los detalles

**En movimientos:**
1. Ir a Admin → Movimientos
2. La columna "Creado por" muestra el usuario para cada registro

## Notas Técnicas

- Los campos `created_by` son nullable para mantener compatibilidad con registros existentes
- Se usa `current_user.idUsuario` de Flask-Login para obtener el usuario autenticado
- Las relaciones ORM permiten acceso fácil: `producto.creador.nombre`
- La fecha `created_at` se establece automáticamente con `default=datetime.utcnow`

## Beneficios

1. **Trazabilidad**: Se puede saber quién creó cada registro
2. **Auditoría**: Facilita investigaciones sobre cambios en el sistema
3. **Responsabilidad**: Los usuarios saben que sus acciones quedan registradas
4. **Reportes**: Permite generar estadísticas por usuario (ej: movimientos por técnico)

## Próximas Mejoras Sugeridas

- [ ] Agregar `updated_by` y `updated_at` para rastrear modificaciones
- [ ] Agregar filtros por usuario en las listas
- [ ] Crear reportes de actividad por usuario
- [ ] Mostrar información de auditoría en más vistas (lista de productos)
- [ ] Log de cambios completo (quién cambió qué campo)

---

**Fecha de implementación:** Octubre 2025
**Estado:** ✅ Completado y funcionando
