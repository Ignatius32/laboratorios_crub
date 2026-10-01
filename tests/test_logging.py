"""Verifica el sistema de logging estructurado.

Cubre el hueco que dejaron `test_logging.py` y `test_complete_logging_system.py`
al retirarse. Lo que se prueba aca no es decorativo: son los comportamientos que
cambiaron y que hasta ahora nada protegia.

1. Que `context.module/function/line` apunten a quien registro. Era el defecto
   visible: `StructuredLogger._log()` armaba el LogRecord con makeRecord
   pasandole ("", 0) como archivo y linea, de modo que esos tres campos salian
   vacios en todos los registros estructurados con contexto, que son casi todos.

2. Que el nivel del logger se respete. `logger.handle()` escribe sin consultar
   `isEnabledFor()`. Hoy no cambia lo que sale a disco, porque cada logger y su
   handler se configuran con el mismo nivel y el handler filtra igual; era una
   trampa latente: subirle el nivel a un logger —la forma habitual de callarlo—
   no tenia efecto. Por eso la comprobacion sube SOLO el nivel del logger y deja
   el handler como esta, que es lo unico que distingue un caso del otro.

3. Que el contexto siga llegando al JSON. El arreglo cambio la via de escritura,
   asi que hay que confirmar que los kwargs no se perdieron en el camino.

4. Que cada categoria escriba UN solo archivo. Antes eran dos por categoria
   —JSON y texto plano— y cada evento se serializaba y bajaba a disco dos veces.
"""
import json
import os
import shutil
import sys
import tempfile
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

DIR_LOGS = os.path.join(tempfile.gettempdir(), 'labcrub_test_logs')
shutil.rmtree(DIR_LOGS, ignore_errors=True)
os.environ['LOG_DIR'] = DIR_LOGS
os.environ['DATABASE_URI'] = 'sqlite:///' + os.path.join(
    tempfile.gettempdir(), 'labcrub_test_logging.db')
_bd = os.environ['DATABASE_URI'].replace('sqlite:///', '')
if os.path.exists(_bd):
    os.remove(_bd)

from app import create_app                                        # noqa: E402
from app.utils.logging_config import StructuredLogger             # noqa: E402

app = create_app()

fallos = []


def check(nombre, condicion, extra=''):
    print(('  OK   ' if condicion else '  FALLA') + ' ' + nombre
          + (('  -> ' + str(extra)) if not condicion and extra else ''))
    if not condicion:
        fallos.append(nombre)


def leer(nombre_archivo):
    """Devuelve los registros JSON de un archivo de log, uno por linea."""
    ruta = os.path.join(DIR_LOGS, nombre_archivo)
    if not os.path.exists(ruta):
        return []
    registros = []
    with open(ruta, encoding='utf-8') as f:
        for linea in f:
            linea = linea.strip()
            if linea:
                registros.append(json.loads(linea))
    return registros


def buscar(nombre_archivo, marca):
    return [r for r in leer(nombre_archivo) if marca in r.get('message', '')]


# --- 1. el nivel configurado se respeta ------------------------------------
# 'database' esta configurado en WARNING; 'business' y 'audit', en INFO.
print('--- el nivel configurado manda ---')
with app.app_context():
    base = StructuredLogger('database')
    base.info('MARCA_INFO_DESCARTADA', contexto=1)     # INFO < WARNING: se tira
    base.info('MARCA_INFO_SIN_KWARGS')                 # la rama sin kwargs
    base.warning('MARCA_WARNING_ESCRITA', contexto=2)  # WARNING: se escribe

check('un info() con contexto sobre un logger en WARNING no se escribe',
      not buscar('database_structured.log', 'MARCA_INFO_DESCARTADA'))
check('un info() sin contexto sobre un logger en WARNING tampoco se escribe',
      not buscar('database_structured.log', 'MARCA_INFO_SIN_KWARGS'))
check('un warning() sobre ese mismo logger si se escribe',
      len(buscar('database_structured.log', 'MARCA_WARNING_ESCRITA')) == 1)

# --- 2. el contexto llega al JSON ------------------------------------------
print('')
print('--- el contexto pasado por kwargs llega al JSON ---')
with app.app_context():
    StructuredLogger('business').info(
        'MARCA_CONTEXTO', operacion='crear_movimiento', cantidad=7, lab='LAB001')

reg = buscar('business_structured.log', 'MARCA_CONTEXTO')
check('el registro se escribio', len(reg) == 1, len(reg))
if reg:
    r = reg[0]
    check('los kwargs aparecen como campos del JSON',
          r.get('operacion') == 'crear_movimiento' and r.get('cantidad') == 7
          and r.get('lab') == 'LAB001',
          dict((k, r.get(k)) for k in ('operacion', 'cantidad', 'lab')))
    check('el nivel queda registrado', r.get('level') == 'INFO', r.get('level'))
    check('el mensaje se conserva', r.get('message') == 'MARCA_CONTEXTO')

# --- 3. context apunta a quien registro ------------------------------------
print('')
print('--- context identifica al llamador, no al modulo de logging ---')


def funcion_que_registra():
    """El nombre y la linea de ESTA funcion son los que deben quedar."""
    linea = sys._getframe().f_lineno + 1
    StructuredLogger('business').info('MARCA_LLAMADOR', dato='x')
    return linea


with app.app_context():
    linea_esperada = funcion_que_registra()

reg = buscar('business_structured.log', 'MARCA_LLAMADOR')
check('el registro se escribio', len(reg) == 1, len(reg))
if reg:
    ctx = reg[0].get('context', {})
    check('context.function es la funcion que llamo',
          ctx.get('function') == 'funcion_que_registra', ctx.get('function'))
    check('context.module es este archivo de prueba',
          ctx.get('module') == 'test_logging', ctx.get('module'))
    check('context.line apunta a la llamada y no es 0',
          ctx.get('line') == linea_esperada,
          str(ctx.get('line')) + ' en vez de ' + str(linea_esperada))

# --- 4. una sola escritura por categoria -----------------------------------
print('')
print('--- cada categoria escribe un solo archivo ---')
archivos = sorted(os.listdir(DIR_LOGS))
check('todos los archivos de log son *_structured.log',
      all(a.endswith('_structured.log') for a in archivos), archivos)
for texto_plano in ('app.log', 'security.log', 'audit.log', 'business.log',
                    'database.log', 'performance.log'):
    check('no se escribe la copia en texto plano ' + texto_plano,
          texto_plano not in archivos)

# --- 5. cada categoria en su propio archivo --------------------------------
print('')
print('--- cada categoria va a su propio archivo ---')
with app.app_context():
    StructuredLogger('audit').info('MARCA_AUDITORIA', accion='alta')
check('el registro de auditoria esta en audit_structured.log',
      len(buscar('audit_structured.log', 'MARCA_AUDITORIA')) == 1)
check('y no se filtro al de negocio',
      not buscar('business_structured.log', 'MARCA_AUDITORIA'))

# --- 6. el nivel del LOGGER se respeta, no solo el del handler -------------
# Esta es la comprobacion que aisla el arreglo de _log(). Subir solo el nivel
# del logger, dejando su handler mas permisivo, es el unico escenario en que
# handle() y log() difieren: handle() no consulta isEnabledFor() y escribe
# igual. Verificado contra el codigo anterior: ahi este registro SI se escribia.
print('')
print('--- el nivel del logger manda, no solo el del handler ---')
import logging  # noqa: E402

with app.app_context():
    lg = logging.getLogger('crub.business')
    nivel_previo = lg.level
    niveles_handler = [logging.getLevelName(h.level) for h in lg.handlers]
    lg.setLevel(logging.ERROR)
    try:
        StructuredLogger('business').info('MARCA_LOGGER_SILENCIADO', k=1)
    finally:
        lg.setLevel(nivel_previo)
    StructuredLogger('business').info('MARCA_TRAS_RESTAURAR', k=2)

check('con el logger en ERROR y su handler en ' + '/'.join(niveles_handler)
      + ', el info() se descarta',
      not buscar('business_structured.log', 'MARCA_LOGGER_SILENCIADO'))
check('y al restaurarle el nivel vuelve a registrar',
      len(buscar('business_structured.log', 'MARCA_TRAS_RESTAURAR')) == 1)

# --- 7. el JSON es valido linea por linea ----------------------------------
print('')
print('--- el formato es una linea JSON por evento ---')
total = 0
for archivo in archivos:
    try:
        total += len(leer(archivo))
    except json.JSONDecodeError as e:
        check('JSON valido en ' + archivo, False, e)
check('las ' + str(total) + ' lineas escritas son JSON valido', total > 0)
for r in leer('business_structured.log'):
    check('cada registro trae timestamp, level, logger y message',
          all(c in r for c in ('timestamp', 'level', 'logger', 'message')),
          list(r.keys()))
    break

shutil.rmtree(DIR_LOGS, ignore_errors=True)
print('')
print('=== TODO OK ===' if not fallos
      else '=== ' + str(len(fallos)) + ' FALLAS: ' + str(fallos) + ' ===')
sys.exit(1 if fallos else 0)
