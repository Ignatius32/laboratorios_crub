"""
La unidad de medida es del producto.

Antes se elegía en cada movimiento: un mismo producto podía quedar con
movimientos en Lt y en Kg, y el alta desde el panel de técnicos dejaba un
movimiento inicial en 'unidades'. El stock suma cantidades sin mirar la unidad,
así que esas mezclas daban totales sin sentido.

Acá se comprueba, entrando por los formularios, que:
  - el producto se guarda con su unidad y sin ella no se acepta;
  - un movimiento toma la unidad del producto aunque el pedido traiga otra;
  - una transferencia la respeta en las dos puntas;
  - corregir la unidad de un producto corrige la de sus movimientos;
  - el alta desde el panel de técnicos ya no deja 'unidades';
  - un producto sin unidad no admite movimientos.
"""
import base64
import json
import os
import re
import sys
import tempfile
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

os.environ['USUARIOS_AUTORIZADOS'] = '40555666'
os.environ['DATABASE_URI'] = 'sqlite:///' + os.path.join(
    tempfile.gettempdir(), 'labcrub_test_unidad.db')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_bd = os.environ['DATABASE_URI'].replace('sqlite:///', '')
if os.path.exists(_bd):
    os.remove(_bd)

from app import create_app                      # noqa: E402
from app.utils import keycloak_auth             # noqa: E402

app = create_app()

fallos = []


def check(nombre, condicion, extra=''):
    print(('  OK   ' if condicion else '  FALLA') + ' ' + nombre
          + (('  -> ' + str(extra)) if not condicion and extra else ''))
    if not condicion:
        fallos.append(nombre)


def b64(datos):
    return base64.urlsafe_b64encode(json.dumps(datos).encode()).rstrip(b'=').decode()


class _Resp:
    def __init__(self, cuerpo):
        self._cuerpo, self.status_code, self.ok, self.text = cuerpo, 200, True, ''

    def json(self):
        return self._cuerpo

    def raise_for_status(self):
        pass


keycloak_auth.requests.post = lambda u, data=None, **k: _Resp(
    {'access_token': b64({'alg': 'none'}) + '.'
     + b64({'realm_access': {'roles': ['app_admin']}}) + '.AAAA'})
keycloak_auth.requests.get = lambda u, **k: _Resp(
    {'preferred_username': '40555666', 'given_name': 'Bea', 'family_name': 'Jefa',
     'email': 'b@crub.edu.ar', 'sub': 'kc'})

from app.models.models import db, Laboratorio, Movimiento, Producto   # noqa: E402

with app.app_context():
    db.create_all()
    for lab in ('LAB001', 'LAB002'):
        db.session.add(Laboratorio(idLaboratorio=lab, nombre=f'Lab {lab}',
                                   direccion='Quintral 1250', telefono='294',
                                   email=f'{lab}@crub.edu.ar'))
    # Como queda un producto importado antes de este cambio, si algo falló.
    db.session.add(Producto(idProducto='SINU', nombre='Sin unidad',
                            tipoProducto='droguero'))
    db.session.commit()


def token(cliente, url):
    html = cliente.get(url).get_data(as_text=True)
    return re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html).group(1)


def movimientos(id_producto):
    with app.app_context():
        return [(m.idLaboratorio, m.tipoMovimiento, m.cantidad, m.unidadMedida)
                for m in Movimiento.query.filter_by(idProducto=id_producto)
                .order_by(Movimiento.timestamp).all()]


with app.test_client() as c:
    c.post('/auth/login', data={'usuario': '40555666', 'contrasena': 'x',
                                'csrf_token': token(c, '/auth/login')})

    print('\n--- el producto lleva la unidad ---')
    html = c.get('/admin/productos/new').get_data(as_text=True)
    check('el formulario de producto ofrece la unidad', 'name="unidadMedida"' in html)
    check('y ya no pide el estado físico',
          'estadoFisico' not in html and 'Estado Físico' not in html)
    check('las opciones son Lt y Kg, sin Litros ni Kilogramos',
          'value="Lt"' in html and 'value="Kg"' in html
          and 'Litros' not in html and 'Kilogramos' not in html)

    base = {'nombre': 'Hidróxido de sodio', 'descripcion': '', 'tipoProducto': 'droguero',
            'stockMinimo': '1', 'marca': ''}
    c.post('/admin/productos/new', data=dict(
        base, idProducto='NAOH', unidadMedida='Kg',
        csrf_token=token(c, '/admin/productos/new')))
    with app.app_context():
        p = Producto.query.get('NAOH')
        check('se guarda con su unidad', p is not None and p.unidadMedida == 'Kg',
              p and p.unidadMedida)

    c.post('/admin/productos/new', data=dict(
        base, idProducto='MALO', unidadMedida='Litros',
        csrf_token=token(c, '/admin/productos/new')))
    with app.app_context():
        check('no acepta una unidad que no sea Lt o Kg', Producto.query.get('MALO') is None)

    check('el desplegable arranca sin nada elegido',
          re.search(r'<option[^>]*selected[^>]*value=""|<option[^>]*value=""[^>]*selected', html) is not None
          or re.search(r'<option value="">Seleccione', html) is not None)
    r = c.post('/admin/productos/new', data=dict(
        base, idProducto='SINE', unidadMedida='',
        csrf_token=token(c, '/admin/productos/new')))
    with app.app_context():
        check('sin elegir unidad no se da de alta', Producto.query.get('SINE') is None)
    check('y el formulario lo dice', 'Elija la unidad de medida' in r.get_data(as_text=True))

    c.post('/admin/productos/new', data=dict(
        base, idProducto='LIQK', nombre='Otro producto',
        unidadMedida='Kg', csrf_token=token(c, '/admin/productos/new')))
    with app.app_context():
        p = Producto.query.get('LIQK')
        check('se da de alta sin estado físico', p is not None and p.unidadMedida == 'Kg')

    c.post('/admin/productos/edit/LIQK', data=dict(
        base, idProducto='LIQK', nombre='Otro producto',
        unidadMedida='Lt', csrf_token=token(c, '/admin/productos/edit/LIQK')))
    with app.app_context():
        check('la unidad se puede corregir al editar',
              Producto.query.get('LIQK').unidadMedida == 'Lt')

    print('\n--- los movimientos toman la unidad del producto ---')
    html = c.get('/admin/movimientos/new').get_data(as_text=True)
    check('el formulario de movimiento ya no pide unidad', 'name="unidadMedida"' not in html)
    check('la unidad figura junto al producto', 'Hidróxido de sodio (Kg)' in html)

    mov = {'cantidad': '10', 'idProducto': 'NAOH', 'idLaboratorio': 'LAB001',
           'idProveedor': '', 'laboratorioDestino': 'LAB002'}
    # El pedido trae 'Lt' a propósito: tiene que ignorarse.
    c.post('/admin/movimientos/new', data=dict(
        mov, tipoMovimiento='ingreso', unidadMedida='Lt',
        csrf_token=token(c, '/admin/movimientos/new')))
    check('el ingreso queda en la unidad del producto',
          movimientos('NAOH') == [('LAB001', 'ingreso', 10.0, 'Kg')], movimientos('NAOH'))

    c.post('/admin/movimientos/new', data=dict(
        mov, tipoMovimiento='transferencia', cantidad='4',
        csrf_token=token(c, '/admin/movimientos/new')))
    unidades = {m[3] for m in movimientos('NAOH')}
    check('la transferencia crea las dos puntas', len(movimientos('NAOH')) == 3,
          movimientos('NAOH'))
    check('y las dos en la unidad del producto', unidades == {'Kg'}, unidades)

    c.post('/admin/productos/edit/NAOH', data=dict(
        base, idProducto='NAOH', unidadMedida='Lt',
        csrf_token=token(c, '/admin/productos/edit/NAOH')))
    unidades = {m[3] for m in movimientos('NAOH')}
    check('corregir la unidad del producto corrige sus movimientos',
          unidades == {'Lt'}, unidades)

    print('\n--- un producto sin unidad no admite movimientos ---')
    r = c.post('/admin/movimientos/new', data=dict(
        mov, tipoMovimiento='ingreso', idProducto='SINU',
        csrf_token=token(c, '/admin/movimientos/new')))
    check('no se registra', movimientos('SINU') == [], movimientos('SINU'))
    check('y avisa por qué', 'no tiene unidad de medida' in r.get_data(as_text=True))

    print('\n--- panel de técnicos ---')
    html = c.get('/tecnicos/laboratorio/LAB001/productos/new')
    ruta = '/tecnicos/laboratorio/LAB001/productos/new'
    if html.status_code == 404:
        # La ruta exacta la define el blueprint; se busca en vez de suponerla.
        with app.app_context():
            ruta = next(str(r) for r in app.url_map.iter_rules()
                        if r.endpoint == 'tecnicos.new_producto').replace('<string:lab_id>', 'LAB001').replace('<lab_id>', 'LAB001')
    html = c.get(ruta).get_data(as_text=True)
    check('el formulario de técnicos ofrece la unidad', 'name="unidadMedida"' in html)
    c.post(ruta, data={
        'idProducto': 'TEC1', 'nombre': 'Carbonato de sodio', 'descripcion': '',
        'tipoProducto': 'botiquin', 'unidadMedida': 'Kg',
        'stockMinimo': '0', 'marca': '', 'csrf_token': token(c, ruta)})
    with app.app_context():
        p = Producto.query.get('TEC1')
        check('el técnico crea el producto con unidad', p is not None and p.unidadMedida == 'Kg')
    check('el movimiento inicial ya no dice "unidades"',
          [m[3] for m in movimientos('TEC1')] == ['Kg'], movimientos('TEC1'))

    with app.app_context():
        ruta_mov = next(str(r) for r in app.url_map.iter_rules()
                        if r.endpoint == 'tecnicos.new_movimiento')
    ruta_mov = ruta_mov.replace('<string:lab_id>', 'LAB001').replace('<lab_id>', 'LAB001')
    html = c.get(ruta_mov).get_data(as_text=True)
    check('el movimiento de técnicos tampoco pide unidad', 'name="unidadMedida"' not in html)
    c.post(ruta_mov, data={
        'tipoMovimiento': 'ingreso', 'cantidad': '2', 'idProducto': 'TEC1',
        'idProveedor': '0', 'unidadMedida': 'Lt', 'csrf_token': token(c, ruta_mov)})
    check('y lo registra en la unidad del producto',
          [m[3] for m in movimientos('TEC1')] == ['Kg', 'Kg'], movimientos('TEC1'))


print('\n=== ' + ('TODO OK' if not fallos else f'{len(fallos)} FALLO(S): {fallos}') + ' ===')
sys.exit(1 if fallos else 0)
