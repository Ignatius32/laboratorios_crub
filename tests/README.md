# Pruebas

Se corren sueltas, con el intérprete del proyecto y desde la raíz del
repositorio. Cada una arma su propia base SQLite en el directorio temporal del
sistema y la borra al empezar, así que no tocan `instance/laboratorios.db`.

```bash
python tests/test_autenticacion.py
python tests/test_todas_las_pantallas.py
python tests/test_stock_y_limpieza.py
python tests/test_unidad_de_medida.py
```

Devuelven código de salida 0 si todo pasa, 1 si algo falla, y listan qué.

## Qué cubre cada una

**`test_autenticacion.py`** — el ingreso de punta a punta contra un Keycloak
simulado: contraseña incorrecta, freno por fuerza bruta, cuenta válida pero
fuera de `USUARIOS_AUTORIZADOS`, roles del realm mapeados a admin/técnico,
expiración de sesión, `next` apuntando a un sitio externo, y que las rutas de
contraseña eliminadas devuelvan 404.

**`test_todas_las_pantallas.py`** — recorre todas las rutas GET como
administrador y como técnico y falla si alguna devuelve 4xx o 5xx. Es la red que
atrapa las plantillas rotas y las consultas mal escritas. También verifica que
los errores rendericen la página propia, y que bajo `/api/` contesten JSON.

**`test_stock_y_limpieza.py`** — que el cálculo de stock siga dando lo mismo
después del refactor de `stock_service` (con números conocidos: 10+5-3-2), que
las propiedades del modelo deleguen bien, y que lo que se eliminó realmente no
esté (modelo `Stock`, JavaScript muerto, Bootstrap alpha, metas de depuración
fijadas en `true`).

**`test_unidad_de_medida.py`** — que el ID de producto se asigne solo (P0001,
P0002, …), en los formularios y al importar una planilla, y que la unidad (Lt o
Kg) sea del producto: los
formularios de producto la piden, los de movimiento ya no, y cada movimiento
toma la del producto aunque el pedido traiga otra. También que el alta desde el
panel de técnicos no deje un movimiento en `unidades`.

## Cómo funciona el Keycloak simulado

No hay red: se reemplazan `keycloak_auth.requests.post` y `.get` por funciones
que devuelven un token armado a mano. Un detalle que cuesta descubrir: la firma
del JWT falso tiene que ser base64 válido (`AAAA` sirve, `x` no), porque PyJWT
la decodifica antes de mirar el payload aunque no verifique la firma. Con una
firma inválida los roles llegan vacíos y la persona entra como técnico, que es
justo el comportamiento seguro por defecto — y hace que la prueba falle por el
motivo equivocado.

**`test_stock_realtime.py`** y **`test_exportar_excel.py`** son anteriores pero
funcionan: la primera ejercita las cuatro operaciones de `stock_service` contra
la base de desarrollo; la segunda, la exportación del reporte a Excel.

## Lo que se retiró, y qué falta

Se quitaron `test_logging.py`, `test_complete_logging_system.py` y
`verify_final_system.py`. Ninguna funcionaba: la primera no arrancaba suelta
—le faltaba agregar la raíz del repositorio a `sys.path`—, la segunda daba 0 de
7 porque todos sus imports fallaban dentro de sus propios `try/except` y lo
reportaban como fallo de la aplicación, y la tercera fallaba 4 de sus
verificaciones. Las tres daban sensación de cobertura sin ejercer nada.

También se quitaron `test_file_validation_system.py` y
`verify_file_validation_complete.py`, que eran archivos de 0 bytes, junto con
`app/utils/file_validator.py`, el módulo vacío que decían probar.

El hueco que dejaban lo cubre ahora **`test_logging.py`**, reescrita. Verifica
los tres cambios de comportamiento del subsistema, y está comprobado que falla
si se revierte cualquiera de ellos:

- `context.module/function/line` apuntan a quien registró. Era el defecto
  visible: `_log()` armaba el LogRecord con `makeRecord(..., "", 0, ...)`, así
  que esos tres campos salían vacíos en todos los registros con contexto.
- El nivel del *logger* se respeta, no sólo el de su handler. `logger.handle()`
  escribe sin consultar `isEnabledFor()`. Esto no cambiaba lo que salía a disco
  —cada logger y su handler se configuran con el mismo nivel, y el handler
  filtraba igual—, pero dejaba una trampa: subirle el nivel a un logger no tenía
  efecto. Por eso la prueba sube sólo el nivel del logger y deja el handler como
  está, que es el único escenario donde ambas vías difieren.
- Cada categoría escribe un solo archivo. Antes eran dos por categoría, JSON y
  texto plano, y cada evento bajaba a disco dos veces.

Nota sobre el logger `security`: está en `WARNING`, así que los `info()` que
emite el middleware de requests para POST/PUT/DELETE y para los accesos a
`/admin` y `/auth` **no se registran**. Es el comportamiento que viene de antes.
Subirlo a `INFO` enciende ese rastro de auditoría a cambio de bastante más
volumen en disco: es una decisión operativa, no una corrección pendiente.
