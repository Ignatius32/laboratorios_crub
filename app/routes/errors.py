"""
Páginas de error propias.

Sin esto cualquier fallo muestra la página cruda de Werkzeug: fondo blanco,
tipografía del navegador y, con DEBUG activo, el traceback completo. Acá se
registran manejadores que devuelven las plantillas de errors/ con el mismo
diseño que el resto de la aplicación.

Se registran sobre la app y no sobre un blueprint a propósito: un errorhandler
de blueprint sólo atiende los errores que nacen dentro de ese blueprint, y un
404 por una URL inexistente no pertenece a ninguno.
"""

from flask import render_template, request
from werkzeug.exceptions import HTTPException

from app.models.models import db


def _quiere_json() -> bool:
    """Si el pedido vino de fetch/XHR, contestar JSON y no una página.

    Los endpoints /api/ y los modales de la aplicación esperan JSON; devolverles
    HTML hace que el .json() del cliente falle con un error de parseo que no
    dice nada sobre lo que pasó de verdad.
    """
    if request.path.startswith('/api/') or '/api/' in request.path:
        return True
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return True
    # Acepta JSON explícitamente y no HTML.
    return (request.accept_mimetypes.best == 'application/json'
            and not request.accept_mimetypes.accept_html)


# Un ícono por familia de error, para que la página diga de un vistazo si es
# "te equivocaste de dirección" o "se rompió algo acá".
_ICONOS = {
    400: 'fa-circle-exclamation',
    403: 'fa-lock',
    404: 'fa-compass',
    413: 'fa-file-arrow-up',
    500: 'fa-triangle-exclamation',
}


def _responder(codigo, titulo, mensaje):
    if _quiere_json():
        return {'error': titulo, 'mensaje': mensaje, 'codigo': codigo}, codigo
    return render_template('errors/error.html',
                           title=titulo, codigo=codigo, mensaje=mensaje,
                           icono=_ICONOS.get(codigo, 'fa-circle-exclamation')), codigo


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return _responder(400, 'Pedido inválido',
                          getattr(e, 'description', None)
                          or 'El pedido no se pudo interpretar.')

    @app.errorhandler(403)
    def forbidden(e):
        return _responder(403, 'Sin permiso',
                          'Tu cuenta no tiene permiso para ver esta página.')

    @app.errorhandler(404)
    def not_found(e):
        return _responder(404, 'Página no encontrada',
                          'La dirección que buscás no existe o cambió de lugar.')

    @app.errorhandler(413)
    def too_large(e):
        return _responder(413, 'Archivo demasiado grande',
                          'El archivo supera el tamaño máximo permitido.')

    @app.errorhandler(500)
    def server_error(e):
        # Una excepción a mitad de una escritura deja la sesión de SQLAlchemy
        # inutilizable: sin este rollback, el siguiente pedido que toque la base
        # falla también, y el error real queda enterrado bajo otro.
        db.session.rollback()
        app.logger.error("Error interno en %s", request.path, exc_info=True)
        return _responder(500, 'Error del sistema',
                          'Algo falló de nuestro lado. Ya quedó registrado.')

    @app.errorhandler(Exception)
    def unhandled(e):
        # Las HTTPException (abort(404), abort(403), …) ya tienen su manejador:
        # devolverlas tal cual para no convertir un 404 en un 500.
        if isinstance(e, HTTPException):
            return e
        db.session.rollback()
        app.logger.error("Excepción no controlada en %s", request.path, exc_info=True)
        return _responder(500, 'Error del sistema',
                          'Algo falló de nuestro lado. Ya quedó registrado.')
