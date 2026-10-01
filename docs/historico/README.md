# Notas históricas

Apuntes que se fueron escribiendo a medida que se implementaba cada cosa, y que
estaban sueltos en la raíz del repositorio. Se guardan como registro de por qué
se hicieron algunas decisiones, **no como documentación vigente**.

Varios describen comportamiento que ya no existe:

- `IMPLEMENTACION_LOGIN_DIRECTO_KEYCLOAK_V26.md`,
  `KEYCLOAK_V26_MIGRATION_SUMMARY.md` y `MIGRACION_COMPLETA_RESUMEN.md`
  documentan el flujo OIDC de redirección, reemplazado por autenticación directa
  contra el endpoint de token.
- `ADMIN_USUARIOS_BOTON_EDITAR_AGREGADO.md` y
  `GESTOR_USUARIOS_ACCIONES_REMOVIDAS.md` describen estados intermedios de la
  pantalla de usuarios que ya cambiaron.
- `KEYCLOAK_USER_SYNC_GUIDE.md` sigue siendo mayormente válido para la
  sincronización, pero menciona contraseñas locales que ya no existen.

Estos tres llegaron después, desde `docs/`, donde figuraban como documentación
vigente y describían código que ya no existe:

- `FILTROS_RESPONSIVOS_IMPLEMENTADOS.md` documenta entero `filters-responsive.js`
  y `filters-responsive.css`, unificados en `ui.js` y `app.css`.
- `MINIMALIST-DESIGN-README.md` describe las ocho hojas de estilo que había
  antes de `tokens.css` + `app.css`, y el uso de DataTables, que se quitó junto
  con jQuery, JSZip y pdfmake al no quedar ninguna tabla que los inicializara.
- `FICHAS_SEGURIDAD_MODAL.md` describe bien el modal, que sigue existiendo, pero
  apunta a `fichas-seguridad.css`, que ya no está.
- `LOGGING_SISTEMA_COMPLETO_FINAL.md` se superponía casi entero con
  `LOGGING_ESTRUCTURADO_IMPLEMENTADO.md`, que quedó como la referencia vigente, y
  además listaba como activos `security.log` y `performance.log` —las copias en
  texto plano que se eliminaron cuando cada categoría pasó a escribir sólo el
  JSON— con instrucciones de PowerShell para leerlos.

La documentación que se mantiene al día es:

- `README.md` (raíz) — qué es el proyecto y cómo levantarlo.
- `DEPLOYMENT.md` (raíz) — despliegue y variables de entorno.
- `docs/` — notas técnicas por tema.
