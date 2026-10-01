# Scripts obsoletos

Nada de acá se ejecuta como parte de la aplicación. Son scripts sueltos que
quedaron de distintos momentos del proyecto y que vivían en la raíz del
repositorio, mezclados con `run.py` y `config.py`.

**La mayoría ya no funciona.** Apuntan a código que se eliminó:

- Los `debug_keycloak_*.py` y varios `test_keycloak_*.py` prueban el flujo OIDC
  de redirección (`/auth/callback`, `keycloak_oidc`), que se quitó al pasar a
  autenticación directa contra el endpoint de token.
- `test_auth_endpoints.py`, `test_auth_flow.py`, `test_login_form_v26.py` y
  `test_direct_login.py` esperan el formulario de login local con contraseña,
  que ya no existe.
- `secure_bootstrap_admin.py` neutralizaba la contraseña de la cuenta semilla;
  la columna `password_hash` se eliminó, así que el script falla al arrancar.
- `test_forgot_password.py` y `FORGOT_PASSWORD_IMPLEMENTATION.md` estaban vacíos
  y se borraron.

Se conservan por si hacen falta como referencia de cómo funcionaba algo antes.
Si dentro de unos meses nadie los abrió, se pueden borrar: el historial de git
los tiene.

Los scripts **vigentes** quedaron en `scripts/`:

- `add_indexes.py` — crea los índices de rendimiento.
- `migrate_db.py` — utilidades de migración.
- `check_dependencies.py` — verifica que estén instaladas las dependencias.
- `check_env_vars.py` — verifica que el `.env` tenga lo que hace falta.
- `test_deployment.py` — valida la configuración de producción.

Las pruebas reales de la aplicación están en `tests/`.
