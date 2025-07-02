# Sincronización de Usuarios desde Keycloak

## Resumen

Se ha implementado una funcionalidad que permite a los administradores sincronizar automáticamente los usuarios con rol "laboratorista" desde Keycloak-CRUB a la base de datos local del sistema.

## Configuración

### Variables de Entorno
El sistema está configurado correctamente con las siguientes variables en `.env`:

```properties
# Keycloak Configuration
KEYCLOAK_SERVER_URL=https://huayca.crub.uncoma.edu.ar/auth/
KEYCLOAK_REALM=CRUB
KEYCLOAK_CLIENT_ID=laboratorios-crub-dev
KEYCLOAK_CLIENT_SECRET=lCXmdzWhJkfLNdacmNjx4EIPPg4WMFeD

# Role Mapping
KEYCLOAK_ADMIN_ROLE=app_admin
KEYCLOAK_TECNICO_ROLE=laboratorista  # ✅ CORRECTO
```

### Mapeo de Roles
- **Keycloak**: `laboratorista` → **App**: `tecnico`
- **Keycloak**: `app_admin` → **App**: `admin`

## Funcionalidades Implementadas

### 1. Métodos en KeycloakAdminClient

- `get_all_users()`: Obtiene todos los usuarios de Keycloak
- `get_users_by_role(role_name)`: Obtiene usuarios por rol específico
- `get_laboratorista_users()`: Obtiene usuarios con rol "laboratorista"
- `sync_users_to_local_db()`: Sincroniza usuarios laboratoristas a BD local

### 2. Ruta de Administración

**URL**: `POST /admin/usuarios/sync-keycloak`

**Funcionalidad**:
- Obtiene todos los usuarios con rol "laboratorista" desde Keycloak
- Crea nuevos usuarios en la BD local si no existen
- Actualiza usuarios existentes con información de Keycloak
- Mantiene logs de auditoría y seguridad

### 3. Interfaz de Usuario

#### Panel de Administración
- **Tarjeta "Integración Keycloak"** en el dashboard principal
- Botón "Sincronizar Ahora" con confirmación

#### Gestión de Usuarios
- **Botón dropdown** junto a "Nuevo Usuario"
- Opción "Sincronizar desde Keycloak" con confirmación

## Cómo Usar

### Desde el Dashboard de Administración
1. Acceder al panel de administración
2. Localizar la tarjeta "Integración Keycloak" (borde verde)
3. Hacer clic en "Sincronizar Ahora"
4. Confirmar la acción

### Desde Gestión de Usuarios
1. Ir a "Usuarios" en el menú de administración
2. Hacer clic en el dropdown junto a "Nuevo Usuario"
3. Seleccionar "Sincronizar desde Keycloak"
4. Confirmar la acción

## Comportamiento de la Sincronización

### Usuarios Nuevos
- Se crean automáticamente en la BD local
- Rol asignado: `tecnico`
- Contraseña inicial: `keycloak_managed` (no se usa, autenticación vía Keycloak)
- Sin laboratorios asignados inicialmente

### Usuarios Existentes
- Se actualizan nombre, apellido y email
- Se mantienen las asignaciones de laboratorios existentes
- Se actualiza el rol si cambió en Keycloak

### Estadísticas de Sincronización
El sistema reporta:
- **Creados**: Nuevos usuarios agregados
- **Actualizados**: Usuarios existentes modificados  
- **Omitidos**: Usuarios sin datos suficientes
- **Errores**: Problemas durante el procesamiento

## Logs y Auditoría

### Logs de Seguridad
```
component: keycloak_admin
operation: sync_users
```

### Logs de Auditoría
```
operation: user_sync_keycloak
user_id: admin_que_ejecuta
action: created/updated
```

## Consideraciones de Seguridad

1. **Solo administradores** pueden ejecutar la sincronización
2. **Logs completos** de todas las operaciones
3. **Validación** de datos antes de crear/actualizar usuarios
4. **Rollback** automático en caso de errores

## Verificación

Para verificar que la integración funciona correctamente:

```bash
python test_keycloak_sync.py
```

Este script verifica:
- ✅ Conexión a Keycloak
- ✅ Obtención de usuarios laboratoristas
- ✅ Lógica de sincronización (sin cambios reales)

## Troubleshooting

### Error de Conexión
- Verificar URLs de Keycloak en `.env`
- Comprobar credenciales del cliente
- Verificar conectividad de red

### Usuarios No Sincronizados
- Verificar que los usuarios tengan rol "laboratorista" en Keycloak
- Comprobar que tengan email y username válidos
- Revisar logs de aplicación para errores específicos

### Permisos Insuficientes
- El cliente Keycloak debe tener permisos para:
  - Listar usuarios
  - Obtener roles de usuarios
  - Acceder a información de perfil

## Próximos Pasos

Una vez que los usuarios estén sincronizados:

1. **Asignar laboratorios** a usuarios técnicos desde la interfaz de administración
2. **Configurar permisos específicos** según necesidades
3. **Programar sincronizaciones periódicas** si es necesario
