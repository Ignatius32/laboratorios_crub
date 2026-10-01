"""Verifica los cambios concretos de la fase B."""
import os, sys, tempfile, json, base64, re, warnings
from pathlib import Path
warnings.filterwarnings('ignore')
os.environ['USUARIOS_AUTORIZADOS'] = '30111222,40555666'
os.environ['DATABASE_URI'] = 'sqlite:///' + os.path.join(tempfile.gettempdir(), 'labcrub_test_faseb.db')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import create_app
from app.utils import keycloak_auth

_bd = os.environ['DATABASE_URI'].replace('sqlite:///', '')
if os.path.exists(_bd):
    os.remove(_bd)

app = create_app()

def b64(d):
    return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b'=').decode()

ESC = {}
class R:
    def __init__(s, c): s._c, s.status_code, s.ok, s.text = c, 200, True, ''
    def json(s): return s._c
    def raise_for_status(s): pass

keycloak_auth.requests.post = lambda u, data=None, **k: R(
    {'access_token': b64({'alg': 'none'}) + '.' + b64({'realm_access': {'roles': ESC['roles']}}) + '.AAAA'})
keycloak_auth.requests.get = lambda u, **k: R(ESC['ui'])

fallos = []
def check(n, c, extra=''):
    print(('  OK   ' if c else '  FALLA') + ' ' + n + (('  -> ' + str(extra)) if not c and extra else ''))
    if not c:
        fallos.append(n)

from app.models.models import db, Usuario, Laboratorio, Producto, Movimiento
from app.utils.stock_service import (get_stock_for_product_in_lab, get_stock_map_for_lab,
                                     get_global_stock_map, get_stock_by_lab_map)

with app.app_context():
    db.create_all()
    for l, n in (('LAB001', 'Quimica'), ('LAB002', 'Biologia')):
        if not Laboratorio.query.get(l):
            db.session.add(Laboratorio(idLaboratorio=l, nombre=n, direccion='x',
                                       telefono='1', email=l + '@c.ar'))
    if not Producto.query.get('P001'):
        db.session.add(Producto(idProducto='P001', nombre='Etanol',
                                tipoProducto='droguero', estadoFisico='liquido'))
    db.session.commit()
    Movimiento.query.delete()
    db.session.commit()
    for i, t, c, l in (('M1', 'ingreso', 10, 'LAB001'), ('M2', 'compra', 5, 'LAB001'),
                       ('M3', 'uso', 3, 'LAB001'), ('M4', 'transferencia', 2, 'LAB001'),
                       ('M5', 'ingreso', 7, 'LAB002')):
        db.session.add(Movimiento(idMovimiento=i, tipoMovimiento=t, cantidad=c,
                                  unidadMedida='Lt', idProducto='P001', idLaboratorio=l))
    db.session.commit()

    print('\n--- stock_service tras el refactor (10+5-3-2=10 en LAB001, 7 en LAB002) ---')
    check('stock producto en lab', get_stock_for_product_in_lab('P001', 'LAB001') == 10.0,
          get_stock_for_product_in_lab('P001', 'LAB001'))
    check('mapa por lab', get_stock_map_for_lab('LAB001') == {'P001': 10.0}, get_stock_map_for_lab('LAB001'))
    check('mapa global (10+7=17)', get_global_stock_map() == {'P001': 17.0}, get_global_stock_map())
    check('mapa por laboratorio',
          get_stock_by_lab_map() == {'P001': {'LAB001': 10.0, 'LAB002': 7.0}}, get_stock_by_lab_map())
    check('filtro por product_ids', get_global_stock_map(['NOEXISTE']) == {}, get_global_stock_map(['NOEXISTE']))
    check('lab sin movimientos da mapa vacio', get_stock_map_for_lab('NOEXISTE') == {})

    print('--- propiedades del modelo que delegan en el servicio ---')
    check('Producto.stock_total', Producto.query.get('P001').stock_total == 17.0)
    check('Producto.stock_en_laboratorio', Producto.query.get('P001').stock_en_laboratorio('LAB002') == 7.0)
    check('Laboratorio.get_stock_producto', Laboratorio.query.get('LAB001').get_stock_producto('P001') == 10.0)

    print('--- modelo Stock eliminado ---')
    import app.models.models as m
    check('no existe la clase Stock', not hasattr(m, 'Stock'))
    check('no existe la tabla stock', 'stock' not in db.metadata.tables)


def entrar(c, dni, roles):
    ESC['roles'] = roles
    ESC['ui'] = {'preferred_username': dni, 'given_name': 'N', 'family_name': 'A',
                 'email': dni + '@crub.edu.ar', 'sub': 'k' + dni}
    html = c.get('/auth/login').get_data(as_text=True)
    tok = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html).group(1)
    c.post('/auth/login', data={'usuario': dni, 'contrasena': 'x', 'csrf_token': tok})
    return tok


print('\n--- admin ahora entra al panel de laboratorio ---')
with app.test_client() as c:
    entrar(c, '40555666', ['app_admin'])
    r = c.get('/tecnicos/')
    check('dashboard de tecnico abre para admin', r.status_code == 200, r.status_code)
    check('y lista todos los laboratorios', b'Quimica' in r.data and b'Biologia' in r.data)
    check('panel de un lab abre', c.get('/tecnicos/panel/LAB001').status_code == 200)
    check('un lab inexistente da 404', c.get('/tecnicos/panel/NOEXISTE').status_code == 404)

print('\n--- pantalla de usuarios ---')
with app.test_client() as c:
    entrar(c, '40555666', ['app_admin'])
    # hace falta OTRO usuario: el propio no muestra boton de borrar, a proposito
    with app.app_context():
        if not Usuario.query.get('99998888'):
            db.session.add(Usuario(idUsuario='99998888', nombre='Otro', apellido='Tecnico',
                                   email='otro@crub.edu.ar', rol='tecnico'))
            db.session.commit()
    r = c.get('/admin/usuarios')
    html = r.get_data(as_text=True)
    check('renderiza', r.status_code == 200, r.status_code)
    check('sin console.log de debug', '[DEBUG]' not in html)
    # el string "keycloak-debug" tambien aparece en el meta y en un comentario:
    # lo que importa es que no se cargue el <script>
    check('no carga el script de debug', 'js/keycloak-debug.js' not in html)
    check('tiene boton de eliminar para otro usuario', '/usuarios/delete/99998888' in html)
    check('el propio usuario no se puede borrar',
          '/usuarios/delete/40555666' not in html and 'disabled' in html)
    check('usa el modal de confirmacion', 'confirm-action' in html)
    check('avisa de tecnicos sin laboratorios', 'Sin asignar' in html)

print('\n--- eliminar usuario funciona ---')
with app.test_client() as c:
    entrar(c, '40555666', ['app_admin'])
    with app.app_context():
        if not Usuario.query.get('11112222'):
            db.session.add(Usuario(idUsuario='11112222', nombre='Temp', apellido='Borrar',
                                   email='temp@crub.edu.ar', rol='tecnico'))
            db.session.commit()
    html = c.get('/admin/usuarios').get_data(as_text=True)
    tok = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html).group(1)
    r = c.post('/admin/usuarios/delete/11112222', data={'csrf_token': tok})
    check('POST de borrado redirige', r.status_code == 302, r.status_code)
    with app.app_context():
        check('el usuario ya no esta', Usuario.query.get('11112222') is None)

print('\n--- archivos eliminados ya no se referencian ---')
with app.test_client() as c:
    entrar(c, '40555666', ['app_admin'])
    html = c.get('/admin/usuarios').get_data(as_text=True)
    for muerto in ('admin-panel.js', 'tecnicos.js', 'fichas-seguridad-ejemplos.js'):
        check('no se pide ' + muerto, muerto not in html)
    check('se pide fichas-seguridad.js', 'fichas-seguridad.js' in html)
    check('APP_URLS definido', 'APP_URLS' in html)
    # "alpha1" tambien aparece en un comentario que explica el cambio: lo que
    # importa es que el <link>/<script> apunten a la version estable
    check('carga bootstrap 5.3.3', 'bootstrap@5.3.3/dist/css' in html
          and 'bootstrap@5.3.3/dist/js' in html)
    check('no carga bootstrap alpha', 'bootstrap@5.3.0-alpha1' not in html)
    check('metas de debug en false', 'name="keycloak-debug" content="false"' in html)

print('\n' + ('=== TODO OK ===' if not fallos else '=== ' + str(len(fallos)) + ' FALLAS: ' + str(fallos) + ' ==='))
sys.exit(1 if fallos else 0)
