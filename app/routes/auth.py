"""
Ingreso y salida.

Un solo camino: el formulario de esta aplicación contra Keycloak. No hay login
local, no hay contraseñas guardadas acá y no hay pantallas de recuperación: eso
lo resuelven las pantallas de cuenta de Huayca, que ya sirven a todas las
aplicaciones del CRUB.

La lógica de verdad está en app/utils/keycloak_auth.py; acá sólo se traduce a
formulario, mensajes y redirecciones.
"""

from flask import (Blueprint, flash, redirect, render_template, request,
                   url_for)
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired

from app.utils import keycloak_auth
from app.utils.logging_config import get_audit_logger, get_security_logger

auth = Blueprint('auth', __name__, url_prefix='/auth')


class LoginForm(FlaskForm):
    usuario = StringField('Usuario (DNI)', validators=[DataRequired()])
    contrasena = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Ingresar')


def destino_despues_de_entrar(user):
    """A dónde mandar a alguien que acaba de entrar.

    Sólo se acepta un `next` que sea una ruta de este host; cualquier otra cosa
    sería un redirect abierto y cae al panel que le corresponde a la persona.

    Exigir que empiece con '/' ya descarta las URL con esquema
    ('https://otro-sitio', 'javascript:...'), y las dos excepciones son las
    formas relativas al protocolo: '//otro-sitio' y '/\\otro-sitio', que los
    navegadores normalizan a una URL externa.
    """
    next_page = request.args.get('next') or ''

    if (next_page.startswith('/')
            and not next_page.startswith('//')
            and not next_page.startswith('/\\')):
        return next_page

    if user.rol == 'admin':
        return url_for('admin.dashboard')
    return url_for('tecnicos.dashboard')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and not keycloak_auth.sesion_vencida():
        return redirect(destino_despues_de_entrar(current_user))

    form = LoginForm()

    if form.validate_on_submit():
        try:
            persona = keycloak_auth.ingresar(form.usuario.data,
                                             form.contrasena.data)
        except keycloak_auth.ErrorDeIngreso as e:
            get_security_logger().warning(
                "Ingreso rechazado",
                operation="login", component="auth",
                usuario=form.usuario.data, motivo=type(e).__name__)
            flash(str(e), 'danger')
            return redirect(url_for('auth.login', next=request.args.get('next')))

        usuario = keycloak_auth.sincronizar_usuario(persona)
        keycloak_auth.abrir_sesion(usuario, persona)
        flash(f'Bienvenido/a, {persona["visible"]}', 'success')
        return redirect(destino_despues_de_entrar(usuario))

    return render_template('auth/login.html',
                           title='Iniciar sesión',
                           form=form,
                           configurado=keycloak_auth.configurado(),
                           url_reset=keycloak_auth.url_reset_password())


@auth.route('/logout')
@login_required
def logout():
    usuario_id = current_user.idUsuario
    keycloak_auth.cerrar_sesion()
    get_audit_logger().info("Usuario cerró sesión",
                            operation="logout", component="auth",
                            user_id=usuario_id)
    flash('Cerró la sesión correctamente.', 'success')
    return redirect(url_for('auth.login'))
