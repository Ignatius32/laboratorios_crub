"""Recorre todas las rutas GET como admin y como tecnico y reporta fallos.

CSRF queda ACTIVO: desactivarlo quita el campo csrf_token de los formularios y
las plantillas que lo renderizan explotan con un UndefinedError que no tiene
nada que ver con la aplicacion real.
"""
import os, sys, tempfile, json, base64, re, warnings
from pathlib import Path
warnings.filterwarnings('ignore')
os.environ['USUARIOS_AUTORIZADOS'] = '30111222,40555666'
os.environ['DATABASE_URI'] = 'sqlite:///' + os.path.join(tempfile.gettempdir(), 'labcrub_test_smoke.db')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.utils import keycloak_auth

_bd = os.environ['DATABASE_URI'].replace('sqlite:///', '')
if os.path.exists(_bd):
    os.remove(_bd)

app = create_app()

def b64(d): return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b'=').decode()

ESC = {}
class R:
    def __init__(s, c): s._c, s.status_code, s.ok, s.text = c, 200, True, ''
    def json(s): return s._c
    def raise_for_status(s): pass
keycloak_auth.requests.post = lambda u, data=None, **k: R(
    {'access_token': f"{b64({'alg':'none'})}.{b64({'realm_access':{'roles':ESC['roles']}})}.AAAA"})
keycloak_auth.requests.get = lambda u, **k: R(ESC['ui'])

# --- datos de prueba -------------------------------------------------------
with app.app_context():
    from app.models.models import db, Usuario, Laboratorio, Producto, Proveedor, Movimiento
    db.create_all()
    if not Laboratorio.query.first():
        db.session.add(Laboratorio(idLaboratorio='LAB001', nombre='Quimica',
                                   direccion='Quintral 1250', telefono='294',
                                   email='q@crub.edu.ar'))
        db.session.add(Proveedor(nombre='Drogueria Sur', cuit='30123456789'))
        db.session.add(Producto(idProducto='P001', nombre='Etanol', tipoProducto='droguero', unidadMedida='Lt', stockMinimo=5, marca='X'))
        db.session.commit()
        db.session.add(Movimiento(idMovimiento='M001', tipoMovimiento='ingreso', cantidad=10,
                                  unidadMedida='Lt', idProducto='P001', idLaboratorio='LAB001'))
        db.session.commit()

def entrar(cliente, dni, roles):
    ESC['roles'] = roles
    ESC['ui'] = {'preferred_username': dni, 'given_name': 'T', 'family_name': 'X',
                 'email': f'{dni}@crub.edu.ar', 'sub': 'kc-' + dni}
    html = cliente.get('/auth/login').get_data(as_text=True)
    tok = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html).group(1)
    r = cliente.post('/auth/login', data={'usuario': dni, 'contrasena': 'x', 'csrf_token': tok})
    assert r.status_code == 302, f'login fallo: {r.status_code}'

# Cada argumento de ruta con un valor del TIPO correcto.
VALORES = {'lab_id': 'LAB001', 'file_id': 'abc123', 'id': None}  # id depende de la ruta
def valor_id(regla):
    r = regla.rule
    if '/usuarios/' in r: return '40555666'
    if '/laboratorios/' in r: return 'LAB001'
    if '/proveedores/' in r: return '1'
    if '/movimientos/' in r: return 'M001'
    return 'P001'

def sustituir(regla):
    u = regla.rule
    for arg in regla.arguments:
        val = valor_id(regla) if arg == 'id' else VALORES.get(arg, '1')
        for patron in (f'<string:{arg}>', f'<int:{arg}>', f'<{arg}>'):
            u = u.replace(patron, val)
    return u

# auth.logout queda FUERA del barrido. Las rutas se recorren en orden
# alfabetico, asi que /auth/logout caia entre /admin/* y /tecnicos/*: cerraba la
# sesion a mitad de camino y todas las pantallas de tecnico posteriores
# respondian 302 hacia el login. Como 302 < 400, el test las contaba como OK y
# anunciaba "37 rutas OK" sin haber renderizado una sola pantalla de tecnico.
reglas = [r for r in app.url_map.iter_rules()
          if 'GET' in r.methods and r.endpoint not in ('static', 'auth.logout')
          and 'drive' not in r.rule and 'ficha_seguridad_directo' not in r.rule
          and 'vista_previa' not in r.rule and 'excel' not in r.rule]

problemas = 0
for etiqueta, dni, roles in (('ADMIN', '40555666', ['app_admin']),
                             ('TECNICO', '30111222', ['laboratorista'])):
    print(f'\n===== {etiqueta} =====')
    with app.test_client() as c:
        entrar(c, dni, roles)
        if etiqueta == 'TECNICO':
            with app.app_context():
                from app.models.models import db, Usuario, Laboratorio
                u = Usuario.query.filter_by(idUsuario=dni).first()
                u.laboratorios = [Laboratorio.query.first()]
                db.session.commit()
        ok = 0
        propias = 0
        prefijo = '/admin/' if etiqueta == 'ADMIN' else '/tecnicos/'
        for regla in sorted(reglas, key=lambda r: r.rule):
            url = sustituir(regla)
            try:
                respuesta = c.get(url)
            except Exception as e:
                print(f'  EXCEPCION {url}: {type(e).__name__}: {str(e)[:140]}')
                problemas += 1
                continue
            cod = respuesta.status_code
            if cod >= 400:
                print(f'  {cod} {url}')
                problemas += 1
                continue
            # Sobre las rutas del propio rol, una redireccion al login significa
            # que la pantalla no se renderizo. Sin esta comprobacion basta con
            # perder la sesion para que el recorrido entero pase en verde.
            if url.startswith(prefijo):
                destino = respuesta.headers.get('Location', '')
                if cod in (301, 302, 308) and 'auth/login' in destino:
                    print(f'  SIN SESION {url} -> {destino}')
                    problemas += 1
                    continue
                propias += 1
            ok += 1
        print(f'  {ok} rutas OK, de las cuales {propias} propias de {etiqueta} renderizadas')

# --- paginas de error ------------------------------------------------------
print('\n===== PAGINAS DE ERROR =====')
with app.test_client() as c:
    r = c.get('/no-existe-esta-ruta')
    txt = r.get_data(as_text=True)
    print(f'  404 anonimo: status={r.status_code} usa_plantilla={"Error 404" in txt}')
    if r.status_code != 404 or 'Error 404' not in txt: problemas += 1

    entrar(c, '40555666', ['app_admin'])
    r = c.get('/admin/productos/view/NOEXISTE')
    txt = r.get_data(as_text=True)
    print(f'  404 autenticado: status={r.status_code} usa_plantilla={"Error 404" in txt}')
    if r.status_code != 404 or 'Error 404' not in txt: problemas += 1

    r = c.get('/admin/api/get_products_by_lab/NOEXISTE')
    print(f'  404 en /api/ devuelve JSON: {r.is_json} -> {r.get_data(as_text=True)[:70]}')
    if not r.is_json: problemas += 1

print('\n' + ('=== TODO OK ===' if not problemas else f'=== {problemas} PROBLEMAS ==='))
sys.exit(1 if problemas else 0)
