"""Prueba del flujo de ingreso con Keycloak simulado."""
import os, sys, tempfile, json, base64
from pathlib import Path
os.environ['USUARIOS_AUTORIZADOS'] = '30111222,40555666'
os.environ['DATABASE_URI'] = 'sqlite:///' + os.path.join(
    tempfile.gettempdir(), 'labcrub_test_auth.db')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.utils import keycloak_auth

_bd = os.environ['DATABASE_URI'].replace('sqlite:///', '')
if os.path.exists(_bd):
    os.remove(_bd)

app = create_app()
app.config['WTF_CSRF_ENABLED'] = False


def jwt_falso(roles_realm):
    def b64(d):
        return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b'=').decode()
    # la firma tiene que ser base64 valido o PyJWT lo rechaza antes de mirar
    # el payload, aunque no la verifique
    return f"{b64({'alg':'none'})}.{b64({'realm_access':{'roles':roles_realm}})}.AAAA"


class RespuestaFalsa:
    def __init__(self, cuerpo, status=200):
        self._cuerpo, self.status_code = cuerpo, status
        self.ok, self.text = 200 <= status < 300, json.dumps(cuerpo)
    def json(self): return self._cuerpo
    def raise_for_status(self):
        if not self.ok: raise Exception('http ' + str(self.status_code))


ESCENARIO = {}

def post_falso(url, data=None, **kw):
    if data['password'] != ESCENARIO['password_correcta']:
        return RespuestaFalsa({'error': 'invalid_grant'}, 400)
    return RespuestaFalsa({'access_token': jwt_falso(ESCENARIO['roles'])})

def get_falso(url, **kw):
    return RespuestaFalsa(ESCENARIO['userinfo'])

keycloak_auth.requests.post = post_falso
keycloak_auth.requests.get = get_falso

fallos = []
def check(nombre, cond, extra=''):
    print(('  OK   ' if cond else '  FALLA') + ' ' + nombre + ('  ' + extra if extra and not cond else ''))
    if not cond: fallos.append(nombre)


with app.app_context():
    from app.models.models import db, Usuario, Laboratorio
    db.create_all()

print('\n--- 1. Todo pide sesion (deny-by-default) ---')
with app.test_client() as c:
    for ruta in ('/admin/', '/admin/usuarios', '/tecnicos/', '/admin/productos'):
        r = c.get(ruta)
        check(f'{ruta} redirige al login', r.status_code == 302 and '/auth/login' in r.headers.get('Location', ''),
              f'{r.status_code} {r.headers.get("Location")}')
    r = c.get('/')
    check('/ es publica', r.status_code == 200, str(r.status_code))

print('\n--- 2. Contrasena mal ---')
ESCENARIO.update(password_correcta='buena', roles=['laboratorista'],
                 userinfo={'preferred_username': '30111222', 'given_name': 'Ana',
                           'family_name': 'Perez', 'email': 'ana@crub.edu.ar', 'sub': 'kc-1'})
with app.test_client() as c:
    r = c.post('/auth/login', data={'usuario': '30111222', 'contrasena': 'mala'}, follow_redirects=True)
    check('rechaza y muestra el mensaje', 'no son correctos' in r.get_data(as_text=True))

print('\n--- 3. Freno por fuerza bruta ---')
with app.test_client() as c:
    for i in range(app.config['INTENTOS_MAX']):
        c.post('/auth/login', data={'usuario': '30111222', 'contrasena': 'mala'})
    r = c.post('/auth/login', data={'usuario': '30111222', 'contrasena': 'buena'}, follow_redirects=True)
    texto = r.get_data(as_text=True)
    check('frena aun con la contrasena correcta', 'Demasiados intentos' in texto)
keycloak_auth._intentos.clear()

print('\n--- 4. Cuenta valida pero fuera de la lista ---')
ESCENARIO['userinfo'] = {'preferred_username': '99999999', 'given_name': 'Juan',
                         'family_name': 'Intruso', 'email': 'juan@crub.edu.ar', 'sub': 'kc-9'}
with app.test_client() as c:
    r = c.post('/auth/login', data={'usuario': '99999999', 'contrasena': 'buena'}, follow_redirects=True)
    texto = r.get_data(as_text=True)
    check('no entra', 'no esta habilitado' in texto or 'no está habilitado' in texto)
with app.app_context():
    check('no se creo fila local', Usuario.query.filter_by(idUsuario='99999999').first() is None)
keycloak_auth._intentos.clear()

print('\n--- 5. Tecnico entra ---')
ESCENARIO.update(roles=['laboratorista'],
                 userinfo={'preferred_username': '30111222', 'given_name': 'Ana',
                           'family_name': 'Perez', 'email': 'ana@crub.edu.ar', 'sub': 'kc-1'})
with app.test_client() as c:
    r = c.post('/auth/login', data={'usuario': '30111222', 'contrasena': 'buena'})
    check('redirige al panel de tecnico', r.status_code == 302 and '/tecnicos/' in r.headers.get('Location',''),
          str(r.headers.get('Location')))
    r = c.get('/tecnicos/', follow_redirects=True)
    check('el panel de tecnico ya abre', r.status_code == 200, str(r.status_code))
    r = c.get('/admin/usuarios')
    check('no puede entrar al panel de admin', r.status_code == 302, str(r.status_code))
with app.app_context():
    u = Usuario.query.filter_by(idUsuario='30111222').first()
    check('fila local creada', u is not None)
    check('rol tecnico', u and u.rol == 'tecnico', u.rol if u else '')
    check('sin columna de contrasena', not hasattr(u, 'password_hash'))

print('\n--- 6. Admin entra y el rol se actualiza ---')
ESCENARIO.update(roles=['app_admin'],
                 userinfo={'preferred_username': '40555666', 'given_name': 'Bea',
                           'family_name': 'Jefa', 'email': 'bea@crub.edu.ar', 'sub': 'kc-2'})
with app.test_client() as c:
    r = c.post('/auth/login', data={'usuario': '40555666', 'contrasena': 'buena'})
    check('redirige al panel de admin', '/admin/' in r.headers.get('Location',''), str(r.headers.get('Location')))
    r = c.get('/admin/usuarios')
    check('el panel de admin abre', r.status_code == 200, str(r.status_code))
    r = c.get('/auth/logout', follow_redirects=True)
    check('logout vuelve al login', '/auth/login' in r.request.path or 'Ingresar' in r.get_data(as_text=True))
    r = c.get('/admin/usuarios')
    check('despues del logout ya no entra', r.status_code == 302)

print('\n--- 6b. Keycloak manda sobre el rol y los datos ---')
with app.app_context():
    b = Usuario.query.filter_by(idUsuario='40555666').first()
    check('rol admin tomado del realm', b and b.rol == 'admin', b.rol if b else '')
# a Ana la ascienden a admin en el realm
ESCENARIO.update(roles=['app_admin'],
                 userinfo={'preferred_username': '30111222', 'given_name': 'Ana Maria',
                           'family_name': 'Perez', 'email': 'ana@crub.edu.ar', 'sub': 'kc-1'})
with app.test_client() as c:
    c.post('/auth/login', data={'usuario': '30111222', 'contrasena': 'buena'})
with app.app_context():
    a = Usuario.query.filter_by(idUsuario='30111222').first()
    check('el ascenso en el realm se refleja', a.rol == 'admin', a.rol)
    check('el nombre se actualiza', a.nombre == 'Ana Maria', a.nombre)
# y el rol vuelve a tecnico si se lo sacan
ESCENARIO['roles'] = ['laboratorista']
with app.test_client() as c:
    c.post('/auth/login', data={'usuario': '30111222', 'contrasena': 'buena'})
with app.app_context():
    a = Usuario.query.filter_by(idUsuario='30111222').first()
    check('quitar el rol en el realm baja a tecnico', a.rol == 'tecnico', a.rol)

print('\n--- 6c. Sin ninguno de los dos roles entra como tecnico ---')
ESCENARIO.update(roles=['offline_access'],
                 userinfo={'preferred_username': '40555666', 'given_name': 'Bea',
                           'family_name': 'Jefa', 'email': 'bea@crub.edu.ar', 'sub': 'kc-2'})
with app.test_client() as c:
    r = c.post('/auth/login', data={'usuario': '40555666', 'contrasena': 'buena'})
    check('no lo manda al panel de admin', '/tecnicos/' in r.headers.get('Location',''),
          r.headers.get('Location',''))

print('\n--- 7. Redirect abierto en next ---')
ESCENARIO.update(roles=['app_admin'],
                 userinfo={'preferred_username': '40555666', 'given_name': 'Bea',
                           'family_name': 'Jefa', 'email': 'bea@crub.edu.ar', 'sub': 'kc-2'})
ESCENARIO.update(roles=['app_admin'])
for malicioso in ('//evil.com', '/\\evil.com', 'https://evil.com'):
    with app.test_client() as c:
        r = c.post('/auth/login?next=' + malicioso, data={'usuario': '40555666', 'contrasena': 'buena'})
        destino = r.headers.get('Location', '')
        check(f'ignora next={malicioso}', 'evil.com' not in destino, destino)
with app.test_client() as c:
    r = c.post('/auth/login?next=/admin/productos', data={'usuario': '40555666', 'contrasena': 'buena'})
    check('respeta un next interno', r.headers.get('Location','').endswith('/admin/productos'), r.headers.get('Location',''))

print('\n--- 8. Tope duro de sesion ---')
import time
with app.test_client() as c:
    c.post('/auth/login', data={'usuario': '40555666', 'contrasena': 'buena'})
    with c.session_transaction() as s:
        s['desde'] = int(time.time()) - (app.config['SESION_HORAS'] * 3600 + 60)
    r = c.get('/admin/usuarios', follow_redirects=True)
    check('sesion vencida obliga a reingresar', 'expir' in r.get_data(as_text=True))

print('\n--- 9. Rutas de contrasena eliminadas ---')
with app.test_client() as c:
    for ruta in ('/auth/forgot-password', '/auth/callback', '/auth/keycloak-login',
                 '/auth/set-password/1/abc', '/auth/keycloak-logout'):
        r = c.get(ruta)
        check(f'{ruta} ya no existe', r.status_code == 404, str(r.status_code))

print('\n--- 10. La lista fijada en el entorno manda ---')
with app.app_context():
    os.environ['USUARIOS_AUTORIZADOS'] = '40555666'
    check('30111222 ya no esta autorizado', '30111222' not in keycloak_auth.usuarios_autorizados())
    os.environ['USUARIOS_AUTORIZADOS'] = '30111222,40555666'
    check('vuelve a estarlo al reponerlo', '30111222' in keycloak_auth.usuarios_autorizados())

print('\n--- 11. La lista del .env se relee sin reiniciar ---')
# Como en el servidor: el entorno del proceso salió del .env al arrancar, y
# después alguien edita el archivo. Antes esto no tenía efecto hasta recargar
# la aplicación, aunque la documentación decía lo contrario.
archivo = Path(tempfile.gettempdir()) / 'labcrub_test_auth.env'
archivo.write_text('SECRET_KEY=x\nUSUARIOS_AUTORIZADOS=30111222,40555666\n', encoding='utf-8')
keycloak_auth.ARCHIVO_ENV = archivo
keycloak_auth._ARCHIVO_AL_ARRANCAR = '30111222,40555666'
os.environ['USUARIOS_AUTORIZADOS'] = '30111222,40555666'
with app.app_context():
    check('arranca con la lista del archivo',
          keycloak_auth.usuarios_autorizados() == {'30111222', '40555666'})

    archivo.write_text('SECRET_KEY=x\nUSUARIOS_AUTORIZADOS=40555666, 28999888\n', encoding='utf-8')
    check('sacar un DNI del archivo le quita el acceso',
          '30111222' not in keycloak_auth.usuarios_autorizados())
    check('agregar uno se lo da', '28999888' in keycloak_auth.usuarios_autorizados())

    keycloak_auth._intentos.clear()
    ESCENARIO.update(password_correcta='buena', roles=['laboratorista'],
                     userinfo={'preferred_username': '30111222', 'given_name': 'Ana',
                               'family_name': 'Perez', 'email': 'ana@crub.edu.ar', 'sub': 'kc-1'})
    with app.test_client() as c:
        r = c.post('/auth/login', data={'usuario': '30111222', 'contrasena': 'buena'},
                   follow_redirects=True)
        check('y el ingreso de quien se sacó se rechaza',
              'no está habilitado' in r.get_data(as_text=True))

    archivo.unlink()
    check('si el archivo desaparece vale la lista con que arrancó',
          keycloak_auth.usuarios_autorizados() == {'30111222', '40555666'})

    os.environ['USUARIOS_AUTORIZADOS'] = '11222333'
    archivo.write_text('USUARIOS_AUTORIZADOS=40555666\n', encoding='utf-8')
    check('una lista fijada por fuera del archivo se respeta',
          keycloak_auth.usuarios_autorizados() == {'11222333'})
    archivo.unlink()

print('\n--- 12. Alta anticipada: laboratorios asignados antes del primer ingreso ---')
os.environ['USUARIOS_AUTORIZADOS'] = '40555666,27333444'
keycloak_auth._intentos.clear()
with app.app_context():
    for lab in ('LABA', 'LABB'):
        db.session.add(Laboratorio(idLaboratorio=lab, nombre=f'Laboratorio {lab}',
                                   direccion='Quintral 1250'))
    db.session.commit()

ESCENARIO.update(password_correcta='buena', roles=['app_admin'],
                 userinfo={'preferred_username': '40555666', 'given_name': 'Bea',
                           'family_name': 'Jefa', 'email': 'bea@crub.edu.ar', 'sub': 'kc-2'})
with app.test_client() as c:
    c.post('/auth/login', data={'usuario': '40555666', 'contrasena': 'buena'})
    html = c.get('/admin/usuarios').get_data(as_text=True)
    check('el listado ofrece dar de alta un usuario', '/admin/usuarios/new' in html)
    r = c.get('/admin/usuarios/new')
    check('el formulario de alta abre', r.status_code == 200, str(r.status_code))

    nuevo = {'nombre': 'Carla', 'apellido': 'Provisoria', 'email': 'carla@provisorio.com',
             'telefono': '', 'rol': 'tecnico', 'labs_asignados': ['LABA', 'LABB']}
    r = c.post('/admin/usuarios/new', data=dict(nuevo, idUsuario='27.333.444'))
    with app.app_context():
        check('un DNI con puntos no se acepta', Usuario.query.count() == Usuario.query.filter(
            Usuario.idUsuario != '27.333.444').count() and r.status_code == 200)

    r = c.post('/admin/usuarios/new', data=dict(nuevo, idUsuario='27333444'), follow_redirects=True)
    texto = r.get_data(as_text=True)
    with app.app_context():
        u = Usuario.query.get('27333444')
        check('se crea el perfil con el DNI como ID', u is not None)
        check('con los laboratorios asignados',
              u is not None and sorted(l.idLaboratorio for l in u.laboratorios) == ['LABA', 'LABB'])
    check('no avisa de la lista si el DNI ya está habilitado', 'falta agregar el DNI' not in texto)

    r = c.post('/admin/usuarios/new', data=dict(nuevo, idUsuario='27333444', email='otra@x.com'))
    check('no deja dar de alta dos veces el mismo DNI',
          'Ya hay un usuario con ese DNI' in r.get_data(as_text=True))

    r = c.post('/admin/usuarios/new', follow_redirects=True, data=dict(
        nuevo, idUsuario='25000111', email='fuera@x.com', labs_asignados=['LABA']))
    check('avisa si el DNI todavía no está en la lista de habilitados',
          'falta agregar el DNI 25000111' in r.get_data(as_text=True))

# Ahora esa persona ingresa por primera vez. Keycloak trae sus datos reales.
ESCENARIO.update(roles=['laboratorista'],
                 userinfo={'preferred_username': '27333444', 'given_name': 'Carla',
                           'family_name': 'Gomez', 'email': 'carla@crub.edu.ar', 'sub': 'kc-7'})
with app.test_client() as c:
    r = c.post('/auth/login', data={'usuario': '27333444', 'contrasena': 'buena'})
    check('en su primer ingreso entra al panel de técnico',
          r.status_code == 302 and '/tecnicos/' in r.headers.get('Location', ''),
          str(r.headers.get('Location')))
with app.app_context():
    filas = Usuario.query.filter(Usuario.idUsuario == '27333444').all()
    u = filas[0] if filas else None
    check('no se crea un segundo perfil',
          len(filas) == 1 and Usuario.query.filter_by(email='carla@provisorio.com').first() is None)
    check('los datos se actualizan con los de Keycloak',
          u is not None and (u.apellido, u.email) == ('Gomez', 'carla@crub.edu.ar'),
          str((u.apellido, u.email)) if u else '')
    check('y conserva los laboratorios que se le habían asignado',
          u is not None and sorted(l.idLaboratorio for l in u.laboratorios) == ['LABA', 'LABB'])

print('\n' + ('=== TODO OK ===' if not fallos else f'=== {len(fallos)} FALLAS: {fallos} ==='))
sys.exit(1 if fallos else 0)
