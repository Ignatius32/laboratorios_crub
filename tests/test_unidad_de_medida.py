"""
La unidad de medida es del producto, y el ID se asigna solo.

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
  - un producto sin unidad no admite movimientos;
  - el ID no se escribe: se asigna correlativo (P0001, P0002, ...), en los
    formularios y en la importación por planilla.
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
    # Como queda un producto importado antes de este cambio, si algo falló. Su
    # ID deja la numeración en 7; el otro, cargado a mano en su momento con
    # otra forma, no tiene que contar.
    db.session.add(Producto(idProducto='P0007', nombre='Sin unidad',
                            tipoProducto='droguero'))
    db.session.add(Producto(idProducto='VIEJO1', nombre='ID de otra época',
                            tipoProducto='droguero', unidadMedida='Lt'))
    db.session.commit()


def token(cliente, url):
    html = cliente.get(url).get_data(as_text=True)
    return re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html).group(1)


def id_de(nombre):
    """El ID que se le asignó al producto con ese nombre, o None si no existe."""
    with app.app_context():
        p = Producto.query.filter_by(nombre=nombre).first()
        return p.idProducto if p else None


def unidad_de(nombre):
    with app.app_context():
        p = Producto.query.filter_by(nombre=nombre).first()
        return p.unidadMedida if p else None


def movimientos(id_producto):
    with app.app_context():
        return [(m.idLaboratorio, m.tipoMovimiento, m.cantidad, m.unidadMedida)
                for m in Movimiento.query.filter_by(idProducto=id_producto)
                .order_by(Movimiento.timestamp).all()]


with app.test_client() as c:
    c.post('/auth/login', data={'usuario': '40555666', 'contrasena': 'x',
                                'csrf_token': token(c, '/auth/login')})

    print('\n--- el producto lleva la unidad y el ID se asigna solo ---')
    html = c.get('/admin/productos/new').get_data(as_text=True)
    check('el formulario de producto ofrece la unidad', 'name="unidadMedida"' in html)
    check('y ya no pide el estado físico',
          'estadoFisico' not in html and 'Estado Físico' not in html)
    check('ni el ID', 'name="idProducto"' not in html)
    check('las opciones son Lt y Kg, sin Litros ni Kilogramos',
          'value="Lt"' in html and 'value="Kg"' in html
          and 'Litros' not in html and 'Kilogramos' not in html)
    check('el desplegable arranca sin nada elegido',
          re.search(r'<option value="">Seleccione', html) is not None)

    base = {'nombre': 'Hidróxido de sodio', 'descripcion': '', 'tipoProducto': 'droguero',
            'stockMinimo': '1', 'marca': ''}
    # Trae un ID a propósito: tiene que ignorarse.
    r = c.post('/admin/productos/new', follow_redirects=True, data=dict(
        base, idProducto='NAOH', unidadMedida='Kg',
        csrf_token=token(c, '/admin/productos/new')))
    naoh = id_de('Hidróxido de sodio')
    check('se guarda con su unidad', unidad_de('Hidróxido de sodio') == 'Kg')
    check('el ID sigue al más alto que había', naoh == 'P0008', naoh)
    check('y se le informa a quien lo cargó', 'P0008' in r.get_data(as_text=True))

    c.post('/admin/productos/new', data=dict(
        base, nombre='Unidad inválida', unidadMedida='Litros',
        csrf_token=token(c, '/admin/productos/new')))
    check('no acepta una unidad que no sea Lt o Kg', id_de('Unidad inválida') is None)

    r = c.post('/admin/productos/new', data=dict(
        base, nombre='Sin elegir', unidadMedida='',
        csrf_token=token(c, '/admin/productos/new')))
    check('sin elegir unidad no se da de alta', id_de('Sin elegir') is None)
    check('y el formulario lo dice', 'Elija la unidad de medida' in r.get_data(as_text=True))

    c.post('/admin/productos/new', data=dict(
        base, nombre='Otro producto', unidadMedida='Kg',
        csrf_token=token(c, '/admin/productos/new')))
    otro = id_de('Otro producto')
    check('los rechazados no gastan número: el siguiente es P0009', otro == 'P0009', otro)

    html = c.get(f'/admin/productos/edit/{otro}').get_data(as_text=True)
    check('al editar el ID se muestra pero no se puede cambiar',
          f'value="{otro}"' in html and 'name="idProducto"' not in html)
    c.post(f'/admin/productos/edit/{otro}', data=dict(
        base, nombre='Otro producto', idProducto='CAMBIADO', unidadMedida='Lt',
        csrf_token=token(c, f'/admin/productos/edit/{otro}')))
    check('la unidad se puede corregir al editar', unidad_de('Otro producto') == 'Lt')
    check('y el ID no cambia', id_de('Otro producto') == otro, id_de('Otro producto'))

    print('\n--- los movimientos toman la unidad del producto ---')
    html = c.get('/admin/movimientos/new').get_data(as_text=True)
    check('el formulario de movimiento ya no pide unidad', 'name="unidadMedida"' not in html)
    check('la unidad figura junto al producto', 'Hidróxido de sodio (Kg)' in html)

    mov = {'cantidad': '10', 'idProducto': naoh, 'idLaboratorio': 'LAB001',
           'idProveedor': '', 'laboratorioDestino': 'LAB002'}
    # El pedido trae 'Lt' a propósito: tiene que ignorarse.
    c.post('/admin/movimientos/new', data=dict(
        mov, tipoMovimiento='ingreso', unidadMedida='Lt',
        csrf_token=token(c, '/admin/movimientos/new')))
    check('el ingreso queda en la unidad del producto',
          movimientos(naoh) == [('LAB001', 'ingreso', 10.0, 'Kg')], movimientos(naoh))

    c.post('/admin/movimientos/new', data=dict(
        mov, tipoMovimiento='transferencia', cantidad='4',
        csrf_token=token(c, '/admin/movimientos/new')))
    unidades = {m[3] for m in movimientos(naoh)}
    check('la transferencia crea las dos puntas', len(movimientos(naoh)) == 3,
          movimientos(naoh))
    check('y las dos en la unidad del producto', unidades == {'Kg'}, unidades)

    c.post(f'/admin/productos/edit/{naoh}', data=dict(
        base, unidadMedida='Lt', csrf_token=token(c, f'/admin/productos/edit/{naoh}')))
    unidades = {m[3] for m in movimientos(naoh)}
    check('corregir la unidad del producto corrige sus movimientos',
          unidades == {'Lt'}, unidades)

    print('\n--- un producto sin unidad no admite movimientos ---')
    r = c.post('/admin/movimientos/new', data=dict(
        mov, tipoMovimiento='ingreso', idProducto='P0007',
        csrf_token=token(c, '/admin/movimientos/new')))
    check('no se registra', movimientos('P0007') == [], movimientos('P0007'))
    check('y avisa por qué', 'no tiene unidad de medida' in r.get_data(as_text=True))

    print('\n--- panel de técnicos ---')
    with app.app_context():
        rutas = {r.endpoint: str(r) for r in app.url_map.iter_rules()}
    en_lab = lambda endpoint: (rutas[endpoint].replace('<string:lab_id>', 'LAB001')
                               .replace('<lab_id>', 'LAB001'))
    ruta = en_lab('tecnicos.new_producto')
    html = c.get(ruta).get_data(as_text=True)
    check('el formulario de técnicos ofrece la unidad', 'name="unidadMedida"' in html)
    check('y tampoco pide el ID', 'name="idProducto"' not in html)
    c.post(ruta, data={
        'nombre': 'Carbonato de sodio', 'descripcion': '',
        'tipoProducto': 'botiquin', 'unidadMedida': 'Kg',
        'stockMinimo': '0', 'marca': '', 'csrf_token': token(c, ruta)})
    tec = id_de('Carbonato de sodio')
    check('el técnico crea el producto con unidad', unidad_de('Carbonato de sodio') == 'Kg')
    check('con el ID que sigue', tec == 'P0010', tec)
    check('el movimiento inicial ya no dice "unidades"',
          [m[3] for m in movimientos(tec)] == ['Kg'], movimientos(tec))

    ruta_mov = en_lab('tecnicos.new_movimiento')
    html = c.get(ruta_mov).get_data(as_text=True)
    check('el movimiento de técnicos tampoco pide unidad', 'name="unidadMedida"' not in html)
    c.post(ruta_mov, data={
        'tipoMovimiento': 'ingreso', 'cantidad': '2', 'idProducto': tec,
        'idProveedor': '0', 'unidadMedida': 'Lt', 'csrf_token': token(c, ruta_mov)})
    check('y lo registra en la unidad del producto',
          [m[3] for m in movimientos(tec)] == ['Kg', 'Kg'], movimientos(tec))

    print('\n--- importación por planilla ---')
    import pandas as pd                              # noqa: E402
    from io import BytesIO                           # noqa: E402

    def importar(filas):
        archivo = BytesIO()
        pd.DataFrame(filas).to_excel(archivo, index=False)
        archivo.seek(0)
        ruta_imp = rutas['admin.importar_productos']
        return c.post(ruta_imp, follow_redirects=True, content_type='multipart/form-data',
                      data={'csrf_token': token(c, ruta_imp),
                            'archivo': (archivo, 'productos.xlsx')})

    columnas = {'URL Ficha de Seguridad': '', 'Descripción': '', 'Control Sedronar': ''}
    importar([
        dict(columnas, **{'ID Producto': '', 'Nombre': 'Tolueno',
                          'Tipo de Producto': 'Droguero', 'Unidad de Medida': 'Lt'}),
        dict(columnas, **{'ID Producto': '', 'Nombre': 'Sulfato de sodio',
                          'Tipo de Producto': 'Droguero', 'Unidad de Medida': 'Kg'}),
        dict(columnas, **{'ID Producto': tec, 'Nombre': 'Carbonato de sodio anhidro',
                          'Tipo de Producto': 'Botiquín', 'Unidad de Medida': ''}),
        dict(columnas, **{'ID Producto': 'INVENTADO', 'Nombre': 'Con ID puesto a mano',
                          'Tipo de Producto': 'Droguero', 'Unidad de Medida': 'Lt'}),
    ])
    check('las filas sin ID se dan de alta con ID correlativos',
          (id_de('Tolueno'), id_de('Sulfato de sodio')) == ('P0011', 'P0012'),
          (id_de('Tolueno'), id_de('Sulfato de sodio')))
    check('la fila con un ID existente actualiza ese producto',
          id_de('Carbonato de sodio anhidro') == tec, id_de('Carbonato de sodio anhidro'))
    check('y conserva la unidad si la planilla no la trae',
          unidad_de('Carbonato de sodio anhidro') == 'Kg')
    check('un ID escrito a mano no da de alta nada', id_de('Con ID puesto a mano') is None)


print('\n=== ' + ('TODO OK' if not fallos else f'{len(fallos)} FALLO(S): {fallos}') + ' ===')
sys.exit(1 if fallos else 0)
