#!/bin/bash
# Ayudas de diagnostico para Laboratorios CRUB.
#
# La version anterior no llegaba a correr: su guarda inicial exigia
# debug_keycloak_production.py en la raiz, archivo que se movio a
# scripts/legacy/, asi que abortaba con "must be run from the
# laboratorios-crub directory" sin importar desde donde se la invocara. Sus
# opciones ejecutaban ese script y debug_keycloak_callback.py, ambos escritos
# para el flujo OIDC de redireccion que se reemplazo por el ingreso directo
# contra el endpoint de token; y probaba la conectividad contra /auth/, la ruta
# anterior a Keycloak v26 (ahora /keycloak/).
#
# Queda solo lo que sigue existiendo.

set -u

RAIZ="$(cd "$(dirname "$0")" && pwd)"
cd "$RAIZ" || exit 1

# El venv del servidor es venv/bin (Linux); en una maquina de desarrollo
# Windows es venv/Scripts. Se prueba el que exista.
if   [ -x "venv/bin/python" ];        then PY="venv/bin/python"
elif [ -x "venv/Scripts/python.exe" ]; then PY="venv/Scripts/python.exe"
elif command -v python3 >/dev/null 2>&1; then PY="python3"
else PY="python"
fi

KEYCLOAK_URL="$(grep -E '^KEYCLOAK_SERVER_URL=' .env 2>/dev/null | cut -d= -f2-)"
KEYCLOAK_URL="${KEYCLOAK_URL:-https://huayca.crub.uncoma.edu.ar/keycloak/}"
REALM="$(grep -E '^KEYCLOAK_REALM=' .env 2>/dev/null | cut -d= -f2-)"
REALM="${REALM:-CRUB}"

echo "================================"
echo "DIAGNOSTICO - Laboratorios CRUB"
echo "================================"
echo "Directorio: $RAIZ"
echo "Interprete: $PY"
echo
echo "1. Variables de entorno (scripts/check_env_vars.py)"
echo "2. Dependencias instaladas contra requirements.txt"
echo "3. Ultimas lineas del log de aplicacion"
echo "4. Ultimas lineas del log de seguridad"
echo "5. Seguir el log de seguridad en vivo"
echo "6. Log de errores de Apache"
echo "7. Conectividad con Keycloak"
echo "8. Todo lo anterior salvo el seguimiento en vivo"
echo
read -r -p "Opcion: " opcion

log_app()  { tail -n "${1:-20}" logs/app_structured.log      2>/dev/null || echo "  (sin logs/app_structured.log)"; }
log_seg()  { tail -n "${1:-20}" logs/security_structured.log 2>/dev/null || echo "  (sin logs/security_structured.log)"; }
conectividad() {
    echo "=== Documento de descubrimiento OIDC del realm $REALM ==="
    curl -s -o /dev/null -w "  HTTP %{http_code} en %{time_total}s\n" --max-time 10 \
        "${KEYCLOAK_URL%/}/realms/${REALM}/.well-known/openid-configuration" \
        || echo "  no se pudo conectar"
}

case "$opcion" in
    1) $PY scripts/check_env_vars.py ;;
    2) $PY scripts/check_dependencies.py ;;
    3) echo "=== logs/app_structured.log ===";      log_app 40 ;;
    4) echo "=== logs/security_structured.log ==="; log_seg 40 ;;
    5) echo "=== siguiendo logs/security_structured.log (Ctrl+C para salir) ==="
       tail -f logs/security_structured.log 2>/dev/null || echo "  (sin archivo)" ;;
    6) tail -n 40 /var/log/apache2/error.log 2>/dev/null || echo "  (sin acceso al log de Apache)" ;;
    7) conectividad ;;
    8) echo "=== Variables de entorno ==="; $PY scripts/check_env_vars.py; echo
       echo "=== Dependencias ===";         $PY scripts/check_dependencies.py; echo
       echo "=== Log de aplicacion ===";    log_app 20; echo
       echo "=== Log de seguridad ===";     log_seg 20; echo
       conectividad ;;
    *) echo "Opcion invalida." ; exit 1 ;;
esac
