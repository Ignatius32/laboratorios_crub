#!/usr/bin/env python3
"""Verifica el .env contra las variables que el código realmente lee.

La lista NO se escribe acá: se descubre recorriendo los os.environ.get(...) del
proyecto. La versión anterior llevaba nueve nombres a mano y exigía
KEYCLOAK_REDIRECT_URI y KEYCLOAK_POST_LOGOUT_REDIRECT_URI, que dejaron de
existir cuando se reemplazó el flujo OIDC de redirección por el ingreso directo
contra el endpoint de token. Resultado: dos ❌ falsos en un .env correcto, y la
comprobación de config reventaba con AttributeError sobre esos mismos nombres.

No intenta adivinar cuáles son obligatorias. Inferirlo del AST no se puede
hacer bien: `os.environ.get('SERVER_NAME', None)` es opcional a propósito, y
`os.getenv('USUARIOS_AUTORIZADOS') or os.getenv('DNI_AUTORIZADOS') or ''` lleva
el respaldo fuera de la llamada. Marcarlas como faltantes sería repetir el mismo
defecto que este script tenía. Así que lista lo que el código lee y su estado, y
señala como problema sólo lo que se puede afirmar con certeza: que config.py no
cargue, o que SECRET_KEY sea un valor de relleno conocido.
"""

import ast
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
# Por segmento y no por subcadena: 'KEYCLOAK_REALM' contiene 'KEY' pero no
# es un secreto, y ocultarlo sólo estorba al diagnosticar.
SEGMENTOS_SENSIBLES = {'SECRET', 'TOKEN', 'PASSWORD', 'PASS', 'KEY'}


def descubrir_variables():
    """Devuelve {NOMBRE: tiene_valor_por_defecto} leyendo el código fuente."""
    encontradas = {}
    archivos = [RAIZ / 'config.py'] + sorted((RAIZ / 'app').rglob('*.py'))
    for ruta in archivos:
        if '__pycache__' in str(ruta):
            continue
        try:
            arbol = ast.parse(ruta.read_text(encoding='utf-8'))
        except (OSError, SyntaxError):
            continue
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.Call) or not nodo.args:
                continue
            f = nodo.func
            # os.environ.get('X'[, defecto])  /  os.getenv('X'[, defecto])
            # Sólo os.environ: request.environ.get('HTTP_X_FORWARDED_FOR')
            # también encaja en "algo.environ.get" y no es una variable de
            # entorno del proceso.
            es_environ_get = (isinstance(f, ast.Attribute) and f.attr == 'get'
                              and isinstance(f.value, ast.Attribute)
                              and f.value.attr == 'environ'
                              and isinstance(f.value.value, ast.Name)
                              and f.value.value.id == 'os')
            es_getenv = (isinstance(f, ast.Attribute) and f.attr == 'getenv'
                         and isinstance(f.value, ast.Name) and f.value.id == 'os')
            if not (es_environ_get or es_getenv):
                continue
            primero = nodo.args[0]
            if isinstance(primero, ast.Constant) and isinstance(primero.value, str):
                nombre = primero.value
                tiene_defecto = len(nodo.args) > 1 and not (
                    isinstance(nodo.args[1], ast.Constant) and nodo.args[1].value is None)
                # Si en algún sitio se lee sin defecto, es obligatoria.
                encontradas[nombre] = encontradas.get(nombre, True) and tiene_defecto
    return encontradas


def mostrar(nombre, valor):
    if valor is None:
        return 'sin definir'
    if SEGMENTOS_SENSIBLES & set(nombre.upper().split('_')):
        return f'***{valor[-4:]}' if len(valor) > 4 else '***'
    return valor if len(valor) <= 58 else valor[:55] + '...'


def check_environment_loading():
    print('=' * 60)
    print('VARIABLES DE ENTORNO  (contra los os.environ.get del código)')
    print('=' * 60)

    from dotenv import load_dotenv
    env = RAIZ / '.env'
    print(f'{"ok   " if env.exists() else "FALTA"}  {env}')
    load_dotenv(env)

    variables = sorted(descubrir_variables())
    definidas = [n for n in variables if os.environ.get(n)]
    ausentes = [n for n in variables if not os.environ.get(n)]

    problemas = 0

    print(f'\n--- Definidas en el entorno ({len(definidas)} de {len(variables)})')
    for nombre in definidas:
        print(f'  {nombre:34} {mostrar(nombre, os.environ.get(nombre))}')

    print(f'\n--- Sin definir ({len(ausentes)}): el codigo usa su valor de respaldo')
    for nombre in ausentes:
        print(f'  {nombre}')

    print('\n--- Carga de la configuración de Flask')
    try:
        sys.path.insert(0, str(RAIZ))
        from config import Config, INSECURE_SECRET_KEYS

        for atributo in ('KEYCLOAK_SERVER_URL', 'KEYCLOAK_REALM', 'KEYCLOAK_CLIENT_ID',
                         'APPLICATION_ROOT', 'IS_PRODUCTION', 'SESION_HORAS'):
            print(f'  {atributo:34} {getattr(Config, atributo)}')

        if Config.SECRET_KEY in INSECURE_SECRET_KEYS:
            print('  AVISO  SECRET_KEY es un valor de relleno conocido; en producción')
            print('         create_app() se niega a arrancar con él.')
            problemas += 1
        elif Config.IS_PRODUCTION and len(Config.SECRET_KEY) < 32:
            print(f'  AVISO  SECRET_KEY tiene {len(Config.SECRET_KEY)} caracteres, corta para producción.')
            problemas += 1
    except Exception as e:
        print(f'  ERROR al cargar config.py: {type(e).__name__}: {e}')
        problemas += 1

    print('\n' + '=' * 60)
    print('Sin problemas.' if not problemas else f'{problemas} problema(s) a revisar.')
    return problemas == 0


if __name__ == '__main__':
    sys.exit(0 if check_environment_loading() else 1)
