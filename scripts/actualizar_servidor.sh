#!/bin/bash
# Actualiza la instalación de Laboratorios CRUB que ya está corriendo en Apache.
#
# deploy.sh es para instalar de cero: copia todo, arma el venv y crea una base
# vacía con db.create_all(). Sobre una instalación con datos eso no alcanza: no
# respalda nada, no corre las migraciones y no se fija si el .env del servidor
# tiene lo que esta versión necesita para dejar entrar a alguien.
#
# Se corre en el servidor, desde un clon del repositorio que NO sea el
# directorio que sirve Apache:
#
#     git clone -b feature/prod https://github.com/Ignatius32/laboratorios_crub.git
#     cd laboratorios_crub
#     sudo bash scripts/actualizar_servidor.sh --verificar   # no cambia nada
#     sudo bash scripts/actualizar_servidor.sh
#
# Primero comprueba todo lo que se puede comprobar sin tocar la instalación. Si
# algo falla después de empezar a cambiarla, repone el código, el venv y la base
# desde el respaldo que tomó al principio.
#
# No reinicia Apache: recarga sólo el proceso de esta aplicación (tocando
# wsgi.py), así que las demás aplicaciones del host no se enteran.

set -Eeuo pipefail

APP_DIR="${APP_DIR:-/var/www/laboratorios-crub}"
SERVICE_USER="${SERVICE_USER:-www-data}"
URL_APP="${URL_APP:-https://huayca.crub.uncoma.edu.ar/laboratorios-crub/}"
RESPALDOS="${RESPALDOS:-/var/backups/laboratorios-crub}"

ORIGEN="$(cd "$(dirname "$0")/.." && pwd)"
SELLO="$(date +%Y%m%d-%H%M%S)"
RESPALDO="${RESPALDOS}/${SELLO}"
SOLO_VERIFICAR=false
[ "${1:-}" = "--verificar" ] && SOLO_VERIFICAR=true

paso()  { echo; echo "==> $*"; }
falla() { echo "ERROR: $*" >&2; exit 1; }

# El valor de una variable del .env del servidor, sin comillas ni \r.
valor() {
    { grep -E "^[[:space:]]*$1=" "${APP_DIR}/.env" || true; } | tail -n 1 \
        | cut -d= -f2- | tr -d '\r' | sed -e "s/^[\"']//" -e "s/[\"'][[:space:]]*$//"
}


# --------------------------------------------------------------------------
# 1. Comprobaciones: nada de esto modifica la instalación
# --------------------------------------------------------------------------

paso "Comprobando la instalación en ${APP_DIR}"

[ "$EUID" -eq 0 ] || falla "hay que correrlo como root (sudo)."
[ -f "${APP_DIR}/wsgi.py" ] || falla "no hay una instalación en ${APP_DIR}. Para instalar de cero está deploy.sh."
[ -f "${APP_DIR}/.env" ] || falla "falta ${APP_DIR}/.env."
[ -x "${APP_DIR}/venv/bin/python" ] || falla "falta el venv en ${APP_DIR}/venv."
[ "$ORIGEN" != "$(cd "$APP_DIR" && pwd)" ] || falla "hay que correrlo desde un clon aparte, no desde ${APP_DIR}."
[ -f "${ORIGEN}/scripts/preparar_base.py" ] || falla "este clon está incompleto: falta scripts/preparar_base.py."
command -v rsync >/dev/null || falla "falta rsync (apt install rsync)."

if git -C "$ORIGEN" rev-parse --short HEAD >/dev/null 2>&1; then
    echo "Versión a instalar: $(git -C "$ORIGEN" log -1 --format='%h %s')"
fi

paso "Comprobando el .env del servidor"

problemas=0
aviso()    { echo "  AVISO: $*"; }
problema() { echo "  FALTA: $*"; problemas=$((problemas + 1)); }

case "$(valor SECRET_KEY)" in
    ''|fallback-secret-key|your_secure_secret_key_change_this|your_secure_secret_key_change_this_in_production|generar-una-clave-nueva-y-unica)
        problema "SECRET_KEY está vacía o es un valor de relleno; la aplicación no arranca así. Generar una con:
           python3 -c \"import secrets; print(secrets.token_urlsafe(64))\"" ;;
esac

autorizados="$(valor USUARIOS_AUTORIZADOS)"
[ -n "$autorizados" ] || autorizados="$(valor DNI_AUTORIZADOS)"
case "$autorizados" in
    '')
        problema "USUARIOS_AUTORIZADOS no está. Sin esa lista no entra nadie, tampoco los administradores.
           Agregar una línea con los DNI habilitados: USUARIOS_AUTORIZADOS=11111111,22222222" ;;
    12345678,23456789)
        problema "USUARIOS_AUTORIZADOS tiene los DNI de ejemplo del template." ;;
    *)
        echo "  USUARIOS_AUTORIZADOS: $(echo "$autorizados" | tr ',;' '\n\n' | grep -c .) usuario(s)" ;;
esac

[ -n "$(valor KEYCLOAK_CLIENT_ID)" ] \
    || problema "KEYCLOAK_CLIENT_ID no está; sin él se usaría el cliente de desarrollo."
case "$(valor KEYCLOAK_CLIENT_SECRET)" in
    ''|your-keycloak-client-secret)
        aviso "KEYCLOAK_CLIENT_SECRET está vacío o es el de relleno. Sólo sirve si el cliente es público." ;;
esac
case "$(valor KEYCLOAK_SERVER_URL)" in
    '') ;;  # vale el valor por defecto de config.py
    */keycloak|*/keycloak/) ;;
    *) aviso "KEYCLOAK_SERVER_URL es '$(valor KEYCLOAK_SERVER_URL)'. El Keycloak del CRUB está en https://huayca.crub.uncoma.edu.ar/keycloak/" ;;
esac
case "$(valor FLASK_ENV)" in
    ''|production) ;;
    *) problema "FLASK_ENV es '$(valor FLASK_ENV)'; en el servidor tiene que ser production." ;;
esac

[ "$problemas" -eq 0 ] || falla "corregir ${APP_DIR}/.env y volver a correr. No se modificó nada."

paso "Bajando las dependencias (todavía sin instalar)"

# Con el pip del venv que está en uso, que corre sobre el mismo Python que
# mod_wsgi. Si alguna versión de requirements.txt no existe para ese Python,
# falla acá y no con la aplicación a medio actualizar.
PYTHON_BASE="$(readlink -f "${APP_DIR}/venv/bin/python")"
echo "Python: ${PYTHON_BASE} ($("$PYTHON_BASE" --version 2>&1))"
"$PYTHON_BASE" -c 'import venv, ensurepip' 2>/dev/null \
    || falla "a ${PYTHON_BASE} le falta el módulo venv (apt install python3-venv)."

RUEDAS="$(mktemp -d /tmp/laboratorios-crub-ruedas.XXXXXX)"
trap 'rm -rf "$RUEDAS"' EXIT
"${APP_DIR}/venv/bin/python" -m pip download --quiet --disable-pip-version-check \
    -r "${ORIGEN}/requirements.txt" -d "$RUEDAS" \
    || falla "no se pudieron bajar las dependencias para este Python. No se modificó nada."
echo "Dependencias bajadas: $(find "$RUEDAS" -type f | wc -l) paquetes"

if $SOLO_VERIFICAR; then
    paso "Todo en orden. Para actualizar, correr de nuevo sin --verificar."
    exit 0
fi


# --------------------------------------------------------------------------
# 2. Respaldo
# --------------------------------------------------------------------------

paso "Respaldando en ${RESPALDO}"

mkdir -p "$RESPALDO"
chmod 700 "$RESPALDOS" "$RESPALDO"   # adentro va el .env

tar -czf "${RESPALDO}/aplicacion.tar.gz" -C "$APP_DIR" \
    --exclude=./venv --exclude=./venv.anterior --exclude=./logs \
    --exclude=__pycache__ .

# Además, cada base copiada con la API de respaldo de SQLite: la aplicación
# sigue atendiendo mientras tanto, y un cp a secas puede agarrar una escritura
# por la mitad.
find "$APP_DIR" -name '*.db' -not -path "${APP_DIR}/venv*" | while read -r base; do
    destino="${RESPALDO}/$(echo "${base#"$APP_DIR"/}" | tr '/' '_')"
    "$PYTHON_BASE" - "$base" "$destino" <<'PY'
import sqlite3, sys
origen, destino = sqlite3.connect(sys.argv[1]), sqlite3.connect(sys.argv[2])
with destino:
    origen.backup(destino)
filas = destino.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
print(f"  {sys.argv[1]} -> {sys.argv[2]} ({filas} tablas)")
PY
done
ls -lh "$RESPALDO"


# --------------------------------------------------------------------------
# 3. Actualización. De acá en más, cualquier falla repone el respaldo.
# --------------------------------------------------------------------------

recargar() { touch "${APP_DIR}/wsgi.py"; }

revertir() {
    trap - ERR
    echo
    echo "ERROR: falló la actualización. Reponiendo la versión anterior..." >&2
    if [ -d "${APP_DIR}/venv.anterior" ]; then
        rm -rf "${APP_DIR}/venv"
        mv "${APP_DIR}/venv.anterior" "${APP_DIR}/venv"
    fi
    tar -xzf "${RESPALDO}/aplicacion.tar.gz" -C "$APP_DIR"
    chown -R "${SERVICE_USER}:${SERVICE_USER}" "$APP_DIR"
    recargar
    echo "Quedó la versión anterior, con la base como estaba. Respaldo: ${RESPALDO}" >&2
    exit 1
}
trap revertir ERR

paso "Copiando el código"

# Sin --delete: en el servidor puede haber archivos propios que no están en el
# repositorio. Los módulos viejos que queden no molestan: nadie los importa.
rsync -a \
    --include='.env.production.template' \
    --exclude='.git' --exclude='.env' --exclude='.env.*' \
    --exclude='venv' --exclude='venv.anterior' --exclude='venv-viejo' \
    --exclude='instance' --exclude='logs' --exclude='*.db' \
    --exclude='__pycache__' --exclude='*.pyc' \
    "${ORIGEN}/" "${APP_DIR}/"

paso "Armando el venv nuevo"

rm -rf "${APP_DIR}/venv.anterior"
mv "${APP_DIR}/venv" "${APP_DIR}/venv.anterior"
"$PYTHON_BASE" -m venv "${APP_DIR}/venv"
"${APP_DIR}/venv/bin/python" -m pip install --quiet --disable-pip-version-check \
    --find-links "$RUEDAS" -r "${APP_DIR}/requirements.txt"

paso "Permisos"

mkdir -p "${APP_DIR}/logs" "${APP_DIR}/instance"
chown -R "${SERVICE_USER}:${SERVICE_USER}" "$APP_DIR"
chmod 600 "${APP_DIR}/.env"

paso "Migrando la base"

# Como el usuario de Apache: así los archivos que cree (la base rehecha por
# alembic, los logs) quedan con el dueño que después los tiene que escribir.
(cd "$APP_DIR" && runuser -u "$SERVICE_USER" -- venv/bin/python scripts/preparar_base.py)

paso "Recargando la aplicación"

recargar
sleep 3
codigo="$(curl -s -o /dev/null -w '%{http_code}' --max-time 60 "${URL_APP}auth/login" || true)"
echo "${URL_APP}auth/login -> ${codigo}"
case "$codigo" in
    200) ;;
    000) echo "AVISO: no se pudo consultar la URL desde el servidor. Probarla desde un navegador." ;;
    *)   echo "La aplicación no contesta bien. Ver /var/log/apache2/error.log" >&2; false ;;
esac

trap - ERR

paso "Listo"
echo "Respaldo de la versión anterior: ${RESPALDO}"
echo "El venv anterior quedó en ${APP_DIR}/venv.anterior; se puede borrar cuando"
echo "esté confirmado que todo anda."
