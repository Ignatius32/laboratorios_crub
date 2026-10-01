"""
Autenticación contra el Keycloak del CRUB, el mismo que usan Quintral y
Reportes DAE.

El mecanismo es el de reportes-dae: la aplicación pide usuario y contraseña en
su propio formulario y los cambia por un token en Keycloak
(grant_type=password), después consulta userinfo para saber quién entró. El
'username' de Keycloak es el DNI.

Dos filtros, en este orden:
  1. Keycloak dice si la persona es quien dice ser.
  2. USUARIOS_AUTORIZADOS dice si además puede entrar a esta aplicación.

Alguien con cuenta válida del CRUB pero sin DNI en la lista queda afuera, y se
le explica por qué en lugar de decirle que la contraseña está mal.

Esta aplicación no guarda ni valida contraseñas: no hay ningún camino de
ingreso que no pase por Keycloak. Restablecerlas lo resuelven las pantallas de
cuenta de Huayca, que ya sirven a todas las aplicaciones del CRUB.

La fila de `usuario` sigue existiendo, pero sólo para lo que Keycloak no sabe:
qué laboratorios tiene asignados cada técnico y quién cargó cada movimiento.
Se crea o actualiza sola en cada ingreso.
"""

import logging
import os
import time
import uuid

import jwt
import requests
from flask import current_app, request, session
from flask_login import current_user, login_user, logout_user

from app.models.models import Usuario, db
from app.utils.logging_config import get_audit_logger, get_security_logger

logger = logging.getLogger(__name__)

TIEMPO_LIMITE = 15  # segundos para que conteste Keycloak


# --------------------------------------------------------------------------
# configuración
# --------------------------------------------------------------------------

def usuarios_autorizados() -> set:
    """Los DNI que pueden entrar, del .env.

    Se lee en cada ingreso a propósito: agregar o sacar a alguien es editar el
    .env, sin reiniciar el servicio.
    """
    crudo = os.getenv("USUARIOS_AUTORIZADOS") or os.getenv("DNI_AUTORIZADOS") or ""
    return {d.strip() for d in crudo.replace(";", ",").split(",") if d.strip()}


def configurado() -> bool:
    return bool(current_app.config.get("KEYCLOAK_SERVER_URL")
                and current_app.config.get("KEYCLOAK_CLIENT_ID"))


def url_reset_password() -> str:
    return current_app.config["URL_RESET_PASSWORD"]


# --------------------------------------------------------------------------
# errores
# --------------------------------------------------------------------------

class ErrorDeIngreso(Exception):
    """Algo impidió entrar. El texto es el que ve la persona."""


class CredencialesInvalidas(ErrorDeIngreso):
    pass


class NoAutorizado(ErrorDeIngreso):
    """La cuenta existe y es válida, pero no está habilitada para esta app."""


class ServicioNoDisponible(ErrorDeIngreso):
    pass


# --------------------------------------------------------------------------
# freno a los intentos por fuerza bruta
# --------------------------------------------------------------------------

# En memoria del proceso: alcanza para frenar a quien prueba contraseñas y no
# agrega una dependencia. Con varios workers cada uno lleva su cuenta, así que
# el tope efectivo se multiplica por la cantidad de procesos.
_intentos = {}


def _clave_intentos():
    return request.remote_addr or "desconocido"


def espera_pendiente() -> int:
    """Segundos que faltan para poder volver a intentar. 0 si se puede ya."""
    _fallos, hasta = _intentos.get(_clave_intentos(), (0, 0))
    return max(0, int(hasta - time.time()))


def _anotar_fallo():
    clave = _clave_intentos()
    fallos, _ = _intentos.get(clave, (0, 0))
    fallos += 1
    espera = current_app.config["ESPERA_SEGUNDOS"]
    tope = current_app.config["INTENTOS_MAX"]
    hasta = time.time() + espera if fallos >= tope else 0
    _intentos[clave] = (fallos, hasta)


def _limpiar_fallos():
    _intentos.pop(_clave_intentos(), None)


# --------------------------------------------------------------------------
# Keycloak
# --------------------------------------------------------------------------

def _url(camino):
    base = current_app.config["KEYCLOAK_SERVER_URL"].rstrip("/")
    realm = current_app.config["KEYCLOAK_REALM"]
    return f"{base}/realms/{realm}/protocol/openid-connect/{camino}"


def _roles_del_token(access_token) -> list:
    """Los roles del realm y del cliente que vienen en el access token.

    Se decodifica sin verificar la firma a propósito: este token lo acabamos de
    pedir nosotros al endpoint de Keycloak por HTTPS en esta misma petición, no
    llegó del navegador, así que no hay nadie en el medio que pueda haberlo
    fabricado. Verificar la firma exigiría traer y cachear las claves públicas
    del realm sin ganar nada acá.
    """
    try:
        datos = jwt.decode(access_token,
                           options={"verify_signature": False, "verify_aud": False})
    except jwt.PyJWTError as e:
        logger.warning("No se pudo leer los roles del token: %s", e)
        return []

    roles = list(datos.get("realm_access", {}).get("roles", []))
    cliente = current_app.config["KEYCLOAK_CLIENT_ID"]
    roles += datos.get("resource_access", {}).get(cliente, {}).get("roles", [])
    return roles


def rol_de_la_app(roles_keycloak) -> str:
    """Traduce los roles del realm al rol de esta aplicación.

    A diferencia del código anterior, alguien sin ninguno de los dos roles no
    cae en 'tecnico' por descarte: devuelve cadena vacía y el ingreso se
    resuelve con la lista de autorizados.
    """
    if current_app.config["KEYCLOAK_ADMIN_ROLE"] in roles_keycloak:
        return "admin"
    if current_app.config["KEYCLOAK_TECNICO_ROLE"] in roles_keycloak:
        return "tecnico"
    return ""


def autenticar(usuario: str, contrasena: str) -> dict:
    """Valida contra Keycloak y devuelve los datos de la persona.

    Levanta CredencialesInvalidas, NoAutorizado o ServicioNoDisponible.
    """
    if not configurado():
        raise ServicioNoDisponible(
            "Falta configurar el acceso a Keycloak. Revise el archivo .env.")

    verificar_ssl = current_app.config["KEYCLOAK_VERIFY_SSL"]

    datos = {
        "grant_type": "password",
        "client_id": current_app.config["KEYCLOAK_CLIENT_ID"],
        "username": usuario.strip(),
        "password": contrasena,
        "scope": "openid profile email",
    }
    secreto = current_app.config.get("KEYCLOAK_CLIENT_SECRET")
    if secreto:
        datos["client_secret"] = secreto

    try:
        r = requests.post(_url("token"), data=datos,
                          timeout=TIEMPO_LIMITE, verify=verificar_ssl)
    except requests.RequestException as e:
        logger.error("No se pudo contactar Keycloak: %s", e)
        raise ServicioNoDisponible(
            "No se pudo contactar el servidor de cuentas. Pruebe de nuevo en un rato.")

    if r.status_code == 401 or (r.status_code == 400 and
                                r.json().get("error") == "invalid_grant"):
        # Mismo mensaje para usuario inexistente y contraseña equivocada: si se
        # distinguieran, el formulario diría quién tiene cuenta en el CRUB.
        logger.info("Ingreso rechazado para %r", usuario)
        raise CredencialesInvalidas("El usuario o la contraseña no son correctos.")

    if not r.ok:
        logger.error("Keycloak respondió %s: %s", r.status_code, r.text[:300])
        raise ServicioNoDisponible(
            "El servidor de cuentas rechazó el pedido. Avise a Sistemas.")

    token = r.json().get("access_token")
    if not token:
        raise ServicioNoDisponible("El servidor de cuentas no devolvió un token.")

    try:
        u = requests.get(_url("userinfo"),
                         headers={"Authorization": f"Bearer {token}"},
                         timeout=TIEMPO_LIMITE, verify=verificar_ssl)
        u.raise_for_status()
        info = u.json()
    except requests.RequestException as e:
        logger.error("No se pudo leer userinfo: %s", e)
        raise ServicioNoDisponible(
            "No se pudieron leer sus datos del servidor de cuentas.")

    dni = str(info.get("preferred_username") or usuario).strip()

    permitidos = usuarios_autorizados()
    if not permitidos:
        raise NoAutorizado(
            "Todavía no hay ningún usuario habilitado para esta aplicación. "
            "Hay que cargarlos en USUARIOS_AUTORIZADOS del archivo .env.")
    if dni not in permitidos:
        logger.info("Usuario %s autenticado pero no habilitado", dni)
        raise NoAutorizado(
            f"Su cuenta del CRUB es válida, pero el usuario {dni} no está "
            "habilitado para esta aplicación. Pídale al administrador que lo agregue.")

    nombre = (info.get("given_name") or "").strip()
    apellido = (info.get("family_name") or "").strip()
    return {
        "dni": dni,
        "nombre": nombre,
        "apellido": apellido,
        "mail": info.get("email") or "",
        "visible": " ".join(p for p in (nombre, apellido) if p) or dni,
        "keycloak_id": info.get("sub") or "",
        "rol": rol_de_la_app(_roles_del_token(token)),
    }


def ingresar(usuario: str, contrasena: str) -> dict:
    """autenticar() más el freno a los reintentos."""
    faltan = espera_pendiente()
    if faltan:
        raise CredencialesInvalidas(
            f"Demasiados intentos fallidos. Espere {faltan // 60 + 1} minutos.")
    try:
        persona = autenticar(usuario, contrasena)
    except CredencialesInvalidas:
        _anotar_fallo()
        raise
    _limpiar_fallos()
    return persona


# --------------------------------------------------------------------------
# la fila local
# --------------------------------------------------------------------------

def _id_libre(dni: str) -> str:
    """El DNI como identificador, salvo que no entre en la columna.

    idUsuario tiene 10 caracteres y es clave primaria; un DNI argentino entra
    de sobra. El caso raro —un legajo largo, una cuenta de servicio— cae en un
    identificador generado para no romper el ingreso.
    """
    if len(dni) <= 10:
        return dni
    return uuid.uuid4().hex[:10]


def sincronizar_usuario(persona: dict) -> Usuario:
    """Crea o actualiza la fila local de esta persona y la devuelve.

    Keycloak manda sobre el nombre, el mail y el rol. Lo que es sólo de esta
    aplicación —los laboratorios asignados— no se toca acá: lo administra un
    administrador desde el panel y sobrevive a cada ingreso.
    """
    audit_logger = get_audit_logger()

    usuario = Usuario.query.filter_by(idUsuario=persona["dni"]).first()
    if usuario is None and persona["mail"]:
        usuario = Usuario.query.filter_by(email=persona["mail"]).first()

    # El rol vacío significa que el realm no le dio ninguno de los dos roles de
    # la aplicación. Está en la lista de autorizados, así que entra, pero como
    # técnico.
    #
    # A propósito no se hereda el rol que ya tenía la fila: si se hiciera,
    # sacarle app_admin a alguien en Keycloak no le sacaría nada acá, y seguiría
    # entrando al panel de administración para siempre. El realm manda, y cuando
    # no dice nada se aplica el menor privilegio.
    rol = persona["rol"] or "tecnico"

    if usuario is None:
        usuario = Usuario(
            idUsuario=_id_libre(persona["dni"]),
            nombre=persona["nombre"] or persona["dni"],
            apellido=persona["apellido"],
            email=persona["mail"] or f"{persona['dni']}@sin-mail.local",
            telefono="",
            rol=rol,
        )
        db.session.add(usuario)
        audit_logger.info("Usuario creado desde Keycloak",
                          operation="sync_user", component="keycloak_auth",
                          user_id=usuario.idUsuario, email=usuario.email, role=rol)
    else:
        usuario.nombre = persona["nombre"] or usuario.nombre
        usuario.apellido = persona["apellido"] or usuario.apellido
        if persona["mail"]:
            usuario.email = persona["mail"]
        usuario.rol = rol
        audit_logger.info("Usuario actualizado desde Keycloak",
                          operation="sync_user", component="keycloak_auth",
                          user_id=usuario.idUsuario, email=usuario.email, role=rol)

    db.session.commit()
    return usuario


# --------------------------------------------------------------------------
# sesión
# --------------------------------------------------------------------------

def abrir_sesion(usuario: Usuario, persona: dict):
    """Deja la sesión lista para una persona que ya pasó los dos filtros."""
    session.clear()
    session.permanent = True
    login_user(usuario)
    session["desde"] = int(time.time())
    session["keycloak_id"] = persona.get("keycloak_id", "")

    get_security_logger().info("Ingreso exitoso",
                               operation="login", component="keycloak_auth",
                               user_id=usuario.idUsuario, role=usuario.rol)


def cerrar_sesion():
    logout_user()
    session.clear()


def sesion_vencida() -> bool:
    """Tope duro a la sesión, se siga usando o no.

    La cookie de Flask se renueva sola con cada visita, así que sin esto una
    pestaña abierta quedaría autenticada para siempre.
    """
    if not current_user.is_authenticated:
        return False
    desde = session.get("desde")
    # Sin marca de inicio no se puede saber la antigüedad: es una sesión vieja,
    # anterior a este cambio. Se la trata como vencida y se vuelve a entrar.
    if not desde:
        return True
    return time.time() - desde > current_app.config["SESION_HORAS"] * 3600
