from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from app.models.models import Usuario, db
from app.utils.email_service import EmailService
from app.utils.logging_decorators import (
    log_authentication_event, 
    log_security_event,
    audit_user_action
)
from app.utils.logging_config import get_security_logger, get_audit_logger
from app.utils.keycloak_auth import keycloak_auth
from app.integrations.keycloak_oidc import keycloak_oidc
from werkzeug.security import generate_password_hash
import json
import sys
import json

auth = Blueprint('auth', __name__, url_prefix='/auth')

# Import or define forms at the top
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError, EqualTo, Length

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Iniciar sesión')

class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Solicitar restablecimiento')

class SetPasswordForm(FlaskForm):
    password = PasswordField('Nueva Contraseña', validators=[
        DataRequired(),
        Length(min=6, message='La contraseña debe tener al menos 6 caracteres')
    ])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(),
        EqualTo('password', message='Las contraseñas deben coincidir')
    ])
    submit = SubmitField('Guardar contraseña')

@auth.route('/login', methods=['GET', 'POST'])
@log_security_event("login_attempt", risk_level="medium")
def login():
    security_logger = get_security_logger()
    
    if current_user.is_authenticated:
        security_logger.info("Authenticated user attempted to access login", 
                           user_id=current_user.idUsuario)
        if current_user.rol == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            # Redirigir técnicos siempre al Panel de Técnico
            return redirect(url_for('tecnicos.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Check if it's the admin login from environment variables
        from flask import current_app
        admin_username = current_app.config.get('ADMIN_USERNAME')
        admin_password = current_app.config.get('ADMIN_PASSWORD')
        
        if form.email.data == admin_username and form.password.data == admin_password:
            # Find admin user or create if not exists
            admin_user = Usuario.query.filter_by(rol='admin').first()
            if admin_user:
                login_user(admin_user, remember=form.remember_me.data)
                security_logger.info("Login exitoso de administrador", 
                                   user_id=admin_user.idUsuario,
                                   email=form.email.data,
                                   login_type="admin_env_credentials")
            else:
                security_logger.error("Intento de login admin sin usuario en BD", 
                                    email=form.email.data)
                flash('Error: No se encontró un usuario administrador en la base de datos', 'danger')
                return redirect(url_for('auth.login'))
                
            return redirect(url_for('admin.dashboard'))
        else:            
            # Try to authenticate as regular user
            user = Usuario.query.filter_by(email=form.email.data).first()
            if user is None or not user.check_password(form.password.data):
                security_logger.warning("Intento de login fallido", 
                                       email=form.email.data,
                                       reason="invalid_credentials",
                                       user_exists=user is not None)
                flash('Email o contraseña incorrectos', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=form.remember_me.data)
            security_logger.info("Login exitoso de usuario regular", 
                               user_id=user.idUsuario,
                               email=user.email,
                               role=user.rol,
                               login_type="regular_user")
            
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                if user.rol == 'admin':
                    next_page = url_for('admin.dashboard')
                else:
                    # Redirigir técnicos siempre al Panel de Técnico
                    next_page = url_for('tecnicos.dashboard')
            return redirect(next_page)
    
    return render_template('auth/login.html', title='Iniciar sesión', form=form)

@auth.route('/logout')
@login_required
@audit_user_action("logout")
def logout():
    """Unified logout function that handles both regular and Keycloak logout"""
    audit_logger = get_audit_logger()
    security_logger = get_security_logger()
    user_id = current_user.idUsuario if current_user.is_authenticated else "unknown"
    
    # Check if user was authenticated via Keycloak
    keycloak_authenticated = session.get('keycloak_authenticated', False)
    
    if keycloak_authenticated:
        try:
            # Get Keycloak logout URL before clearing session
            logout_url = keycloak_auth.logout_user_from_keycloak()
            
            audit_logger.info("Usuario cerró sesión via Keycloak", 
                             user_id=user_id,
                             logout_type="keycloak")
            
            security_logger.info("Usuario desconectado de Keycloak",
                               operation="keycloak_logout",
                               component="auth",
                               user_id=user_id)
            
            flash('Has cerrado sesión exitosamente.', 'success')
            return redirect(logout_url)
            
        except Exception as e:
            security_logger.error("Error al cerrar sesión de Keycloak",
                                operation="keycloak_logout",
                                component="auth",
                                error=str(e),
                                user_id=user_id)
            # Fallback to regular logout
            logout_user()
            session.pop('keycloak_authenticated', None)
            session.pop('keycloak_token', None)
            flash('Has cerrado sesión (con advertencias).', 'warning')
            return redirect(url_for('main.index'))
    else:
        # Regular logout for local authentication
        audit_logger.info("Usuario cerró sesión", 
                         user_id=user_id,
                         logout_type="local")
        
        logout_user()
        flash('Has cerrado sesión correctamente', 'success')
        return redirect(url_for('main.index'))

@auth.route('/forgot-password', methods=['GET', 'POST'])
@log_security_event("password_reset_request", risk_level="medium")
def forgot_password():
    """Handle forgot password requests"""
    security_logger = get_security_logger()
    
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        if user:
            # Generate reset token
            token = user.generate_reset_token()
            db.session.commit()
            
            # Send reset email
            sent = EmailService.send_password_reset_email(user, token)
            if sent:
                security_logger.info("Email de reset de contraseña enviado exitosamente", 
                                   email=form.email.data,
                                   user_id=user.idUsuario,
                                   token_generated=True)
                flash('Se ha enviado un correo electrónico con instrucciones para restablecer tu contraseña.', 'success')
            else:
                security_logger.error("Fallo al enviar email de reset de contraseña", 
                                    email=form.email.data,
                                    user_id=user.idUsuario)
                flash('No se pudo enviar el correo electrónico. Por favor, contacta al administrador.', 'danger')
        else:
            # We don't want to reveal that the email doesn't exist, so we show the same message
            security_logger.warning("Intento de reset para email inexistente", 
                                   email=form.email.data)
            flash('Se ha enviado un correo electrónico con instrucciones para restablecer tu contraseña.', 'success')
            
        return redirect(url_for('auth.login'))
        
    return render_template('auth/forgot_password.html', title='Recuperar Contraseña', form=form)

@auth.route('/set-password/<string:user_id>/<string:token>', methods=['GET', 'POST'])
@log_security_event("password_reset_completion", risk_level="high")
def set_password(user_id, token):
    """Handle password reset/setup using a token"""
    security_logger = get_security_logger()
    
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    # Find the user
    user = Usuario.query.get(user_id)
    if not user:
        security_logger.warning("Intento de reset con usuario inexistente", 
                               user_id=user_id,
                               token=token[:10] + "...")
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('auth.login'))
        
    # Check if token is valid
    token_valid = user.is_reset_token_valid(token)
    error_message = None
    is_new_user = user.password_hash == generate_password_hash('password123')  # Default password check
    
    if not token_valid:
        security_logger.warning("Intento de reset con token inválido", 
                               user_id=user_id,
                               email=user.email,
                               token=token[:10] + "...")
    
    form = SetPasswordForm()
    if form.validate_on_submit():
        if token_valid:
            # Set the new password
            user.set_password(form.password.data)
            db.session.commit()
            
            security_logger.info("Contraseña actualizada exitosamente", 
                               user_id=user_id,
                               email=user.email,
                               is_new_user=is_new_user,
                               reset_type="token_reset")
            
            flash('Tu contraseña ha sido actualizada correctamente. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        else:
            error_message = 'El enlace no es válido o ha expirado.'
            
    return render_template('auth/set_password.html', 
                          title='Establecer Contraseña' if is_new_user else 'Restablecer Contraseña',
                          form=form, 
                          token_valid=token_valid,
                          error_message=error_message,
                          is_new_user=is_new_user)

# Keycloak Authentication Routes

@auth.route('/keycloak-login')
@log_security_event("keycloak_login_attempt", risk_level="medium")
def keycloak_login():
    """Initiate Keycloak OAuth2 login"""
    security_logger = get_security_logger()
    
    if current_user.is_authenticated:
        security_logger.info("Authenticated user attempted to access Keycloak login", 
                           user_id=current_user.idUsuario)
        if current_user.rol == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('tecnicos.dashboard'))
    
    security_logger.info("Starting Keycloak authentication",
                        operation="keycloak_login_initiate",
                        component="auth")
    
    try:
        # Import here to avoid circular imports and ensure fresh import
        from app.integrations.keycloak_oidc import keycloak_oidc
        
        # Log detailed diagnostic information
        security_logger.info("Keycloak OIDC diagnostic",
                           operation="keycloak_login_initiate",
                           component="auth",
                           keycloak_oidc_exists=keycloak_oidc is not None,
                           oauth_exists=keycloak_oidc.oauth is not None if keycloak_oidc else False,
                           keycloak_client_exists=keycloak_oidc.keycloak is not None if keycloak_oidc else False,
                           keycloak_client_type=type(keycloak_oidc.keycloak).__name__ if keycloak_oidc and keycloak_oidc.keycloak else None)
        
        # Check if keycloak_oidc is properly initialized
        if not keycloak_oidc:
            security_logger.error("Keycloak OIDC object is None",
                                operation="keycloak_login_initiate",
                                component="auth")
            flash('Keycloak authentication service is not available. Contact administrator.', 'error')
            return redirect(url_for('auth.login'))
        
        if not keycloak_oidc.oauth:
            security_logger.error("Keycloak OAuth object is None",
                                operation="keycloak_login_initiate",
                                component="auth")
            flash('OAuth service is not properly initialized. Contact administrator.', 'error')
            return redirect(url_for('auth.login'))
        
        if not keycloak_oidc.keycloak:
            security_logger.error("Keycloak client is None - reinitializing",
                                operation="keycloak_login_initiate",
                                component="auth")
            
            # Try to reinitialize the Keycloak client
            try:
                keycloak_oidc.init_app(current_app)
                security_logger.info("Keycloak client reinitialized",
                                   operation="keycloak_login_initiate",
                                   component="auth",
                                   client_now_exists=keycloak_oidc.keycloak is not None)
            except Exception as reinit_error:
                security_logger.error("Failed to reinitialize Keycloak client",
                                    operation="keycloak_login_initiate",
                                    component="auth",
                                    error=str(reinit_error))
                flash('Keycloak authentication is not properly configured. Contact administrator.', 'error')
                return redirect(url_for('auth.login'))
        
        # Final check after potential reinitialization
        if not keycloak_oidc.keycloak:
            security_logger.error("Keycloak client still None after reinitialization",
                                operation="keycloak_login_initiate",
                                component="auth")
            flash('Keycloak authentication service unavailable. Contact administrator.', 'error')
            return redirect(url_for('auth.login'))
        
        # Log configuration for debugging
        security_logger.info("Keycloak configuration check",
                           operation="keycloak_login_initiate",
                           component="auth",
                           server_url=current_app.config.get('KEYCLOAK_SERVER_URL'),
                           realm=current_app.config.get('KEYCLOAK_REALM'),
                           client_id=current_app.config.get('KEYCLOAK_CLIENT_ID'),
                           redirect_uri=current_app.config.get('KEYCLOAK_REDIRECT_URI'))
        
        # Attempt to initiate OAuth flow
        security_logger.info("Calling authorize_redirect",
                           operation="keycloak_login_initiate",
                           component="auth")
        
        redirect_response = keycloak_oidc.authorize_redirect()
        
        security_logger.info("Keycloak authorization redirect initiated successfully",
                           operation="keycloak_login_initiate",
                           component="auth",
                           redirect_response_type=type(redirect_response).__name__)
        
        return redirect_response
        
    except AttributeError as e:
        security_logger.error("Keycloak OIDC attribute error",
                            operation="keycloak_login_initiate",
                            component="auth",
                            error=str(e),
                            error_type="AttributeError")
        
        if current_app.config.get('KEYCLOAK_DEBUG', False):
            flash(f'Keycloak attribute error: {str(e)}', 'error')
            session['auth_debug_error'] = f"AttributeError: {str(e)}"
            return redirect(url_for('auth.auth_debug'))
        else:
            flash('Keycloak authentication service error. Contact administrator.', 'error')
            return redirect(url_for('auth.login'))
        
    except Exception as e:
        security_logger.error("Error starting Keycloak authentication",
                            operation="keycloak_login_initiate",
                            component="auth",
                            error=str(e),
                            error_type=type(e).__name__,
                            config_available=bool(current_app.config.get('KEYCLOAK_SERVER_URL')))
        
        # In debug mode, provide more detailed error information
        if current_app.config.get('KEYCLOAK_DEBUG', False):
            flash(f'Keycloak authentication error: {str(e)}', 'error')
            # Store error details for debug page
            session['auth_debug_error'] = f"Keycloak login error: {type(e).__name__}: {str(e)}"
            return redirect(url_for('auth.auth_debug'))
        else:
            flash('Authentication error. Please try again.', 'error')
            return redirect(url_for('auth.login'))

@auth.route('/callback')
@log_security_event("keycloak_callback", risk_level="medium")
def keycloak_callback():
    """Handle Keycloak OAuth2 callback"""
    security_logger = get_security_logger()
    audit_logger = get_audit_logger()
    
    # Log incoming request parameters for debugging
    security_logger.info("Callback received",
                        operation="keycloak_callback",
                        component="auth",
                        query_params=dict(request.args),
                        headers={k: v for k, v in request.headers if k.lower() not in ['authorization', 'cookie']},
                        referrer=request.referrer,
                        user_agent=request.user_agent.string,
                        remote_addr=request.remote_addr)
    
    # Check if we have required parameters
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    session_state = request.args.get('session_state')
    iss = request.args.get('iss')
    
    # Detailed parameter logging
    security_logger.info("Callback parameters analysis",
                        operation="keycloak_callback",
                        component="auth",
                        has_code=bool(code),
                        has_state=bool(state),
                        has_error=bool(error),
                        has_session_state=bool(session_state),
                        has_iss=bool(iss),
                        code_length=len(code) if code else 0,
                        state_value=state[:10] + "..." if state and len(state) > 10 else state)
    
    if error:
        security_logger.error("Error parameter received in callback",
                            operation="keycloak_callback",
                            component="auth",
                            error=error,
                            error_description=request.args.get('error_description'),
                            state=state)
        flash(f'Authentication error: {error}', 'error')
        return redirect(url_for('auth.login'))
    
    if not code:
        security_logger.warning("No authorization code received in callback",
                              operation="keycloak_callback",
                              component="auth",
                              all_params=dict(request.args))
        flash('Error: No authorization code received.', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        # Exchange authorization code for access token
        security_logger.info("Attempting to exchange code for token",
                           operation="keycloak_callback",
                           component="auth",
                           code_prefix=code[:10] + "..." if len(code) > 10 else code)
        
        # Log session state before token exchange
        security_logger.info("Session state before token exchange",
                           operation="keycloak_callback",
                           component="auth",
                           session_keys=list(session.keys()),
                           session_id=session.get('_id', 'unknown'))
        
        token = keycloak_oidc.authorize_access_token()
        
        if not token:
            security_logger.warning("No valid token received from Keycloak",
                                  operation="keycloak_callback",
                                  component="auth",
                                  oauth_client_id=current_app.config.get('KEYCLOAK_CLIENT_ID'),
                                  oauth_server_url=current_app.config.get('KEYCLOAK_SERVER_URL'))
            flash('Authentication error. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        security_logger.info("Token received successfully",
                           operation="keycloak_callback",
                           component="auth",
                           token_type=token.get('token_type'),
                           has_access_token=bool(token.get('access_token')),
                           has_id_token=bool(token.get('id_token')),
                           has_refresh_token=bool(token.get('refresh_token')),
                           expires_in=token.get('expires_in'),
                           scope=token.get('scope'))
        
        # Log session state after token exchange
        security_logger.info("Session state after token exchange",
                           operation="keycloak_callback",
                           component="auth",
                           session_keys=list(session.keys()),
                           keycloak_authenticated=session.get('keycloak_authenticated', False))
        
        # Login user using Keycloak token
        if keycloak_auth.login_user_from_keycloak(token):
            audit_logger.info("User successfully authenticated with Keycloak",
                            operation="keycloak_login_success",
                            component="auth",
                            user_id=current_user.idUsuario,
                            email=current_user.email,
                            role=current_user.rol)
            
            security_logger.info("User login successful",
                               operation="keycloak_callback",
                               component="auth",
                               user_id=current_user.idUsuario,
                               user_role=current_user.rol,
                               user_authenticated=current_user.is_authenticated)
            
            # Handle next parameter
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                if current_user.rol == 'admin':
                    next_page = url_for('admin.dashboard')
                else:
                    next_page = url_for('tecnicos.dashboard')
            
            security_logger.info("Redirecting user after successful login",
                               operation="keycloak_callback",
                               component="auth",
                               next_page=next_page,
                               user_id=current_user.idUsuario)
            
            # flash(f'Acceso correcto, {current_user.nombre}!', 'success')
            return redirect(next_page)
        else:
            security_logger.error("Failed to login user from Keycloak",
                                operation="keycloak_login_failed",
                                component="auth",
                                token_present=bool(token),
                                session_state=dict(session))
            flash('Error processing authentication. Contact administrator.', 'error')
            return redirect(url_for('auth.login'))
            
    except Exception as e:
        security_logger.error("Error in Keycloak callback",
                            operation="keycloak_callback",
                            component="auth",
                            error=str(e),
                            error_type=type(e).__name__,
                            traceback=str(e.__traceback__))
        
        # In debug mode, store error details and redirect to debug page
        if current_app.config.get('KEYCLOAK_DEBUG', False):
            session['auth_debug_error'] = f"Exception: {type(e).__name__}: {str(e)}"
            return redirect(url_for('auth.auth_debug'))
        
        flash('Authentication error. Please try again.', 'error')
        return redirect(url_for('auth.login'))

@auth.route('/keycloak-logout')
@login_required
@audit_user_action("keycloak_logout")
def keycloak_logout():
    """Legacy route - redirect to unified logout"""
    return redirect(url_for('auth.logout'))

@auth.route('/debug')
def auth_debug():
    """Debug route to show authentication information (only in debug mode)"""
    from flask import current_app
    
    # Only allow in debug mode
    if not current_app.config.get('KEYCLOAK_DEBUG', False):
        flash('Debug mode is not enabled.', 'error')
        return redirect(url_for('auth.login'))
    
    error_details = None
    try:
        # Try to get any stored error details from session
        error_details = session.pop('auth_debug_error', None)
    except:
        pass
    
    return render_template('auth/debug.html', 
                          title='Authentication Debug',
                          error_details=error_details)

@auth.route('/test-keycloak-config')
def test_keycloak_config():
    """Test Keycloak configuration without initiating OAuth flow"""
    if not current_app.config.get('KEYCLOAK_DEBUG', False):
        return redirect(url_for('auth.login'))
    
    config_status = {
        'KEYCLOAK_SERVER_URL': current_app.config.get('KEYCLOAK_SERVER_URL'),
        'KEYCLOAK_REALM': current_app.config.get('KEYCLOAK_REALM'),
        'KEYCLOAK_CLIENT_ID': current_app.config.get('KEYCLOAK_CLIENT_ID'),
        'KEYCLOAK_CLIENT_SECRET': '***' if current_app.config.get('KEYCLOAK_CLIENT_SECRET') else None,
        'KEYCLOAK_REDIRECT_URI': current_app.config.get('KEYCLOAK_REDIRECT_URI'),
        'keycloak_oidc_initialized': keycloak_oidc is not None,
        'keycloak_client_available': keycloak_oidc.keycloak is not None if keycloak_oidc else False
    }
    
    return f"<pre>{json.dumps(config_status, indent=2)}</pre>"

@auth.route('/keycloak-health')
def keycloak_health():
    """Simple health check for Keycloak integration"""
    try:
        from app.integrations.keycloak_oidc import keycloak_oidc
        
        status = {
            'status': 'ok',
            'keycloak_oidc_imported': True,
            'keycloak_oidc_exists': keycloak_oidc is not None,
            'oauth_client_exists': keycloak_oidc.oauth is not None if keycloak_oidc else False,
            'keycloak_client_exists': keycloak_oidc.keycloak is not None if keycloak_oidc else False,
            'config': {
                'server_url': current_app.config.get('KEYCLOAK_SERVER_URL'),
                'realm': current_app.config.get('KEYCLOAK_REALM'),
                'client_id': current_app.config.get('KEYCLOAK_CLIENT_ID'),
                'redirect_uri': current_app.config.get('KEYCLOAK_REDIRECT_URI')
            }
        }
        
        return json.dumps(status, indent=2), 200, {'Content-Type': 'application/json'}
        
    except Exception as e:
        error_status = {
            'status': 'error',
            'error': str(e),
            'error_type': type(e).__name__
        }
        return json.dumps(error_status, indent=2), 500, {'Content-Type': 'application/json'}

@auth.route('/reinit-keycloak')
def reinit_keycloak():
    """Manually reinitialize Keycloak OIDC client (debug mode only)"""
    if not current_app.config.get('KEYCLOAK_DEBUG', False):
        flash('Debug mode required for this operation.', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        from app.integrations.keycloak_oidc import keycloak_oidc
        
        # Force reinitialization
        keycloak_oidc.init_app(current_app)
        
        flash('Keycloak OIDC client reinitialized successfully.', 'success')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        flash(f'Failed to reinitialize Keycloak: {str(e)}', 'error')
        return redirect(url_for('auth.login'))

@auth.route('/env-status')
def env_status():
    """Show environment status (debug mode only)"""
    if not current_app.config.get('KEYCLOAK_DEBUG', False):
        return "Debug mode required", 403
    
    import os
    
    env_info = {
        'flask_config': {
            'FLASK_ENV': current_app.config.get('FLASK_ENV'),
            'APPLICATION_ROOT': current_app.config.get('APPLICATION_ROOT'),
            'KEYCLOAK_SERVER_URL': current_app.config.get('KEYCLOAK_SERVER_URL'),
            'KEYCLOAK_CLIENT_ID': current_app.config.get('KEYCLOAK_CLIENT_ID'),
            'KEYCLOAK_DEBUG': current_app.config.get('KEYCLOAK_DEBUG'),
        },
        'os_environ': {
            'FLASK_ENV': os.environ.get('FLASK_ENV'),
            'APPLICATION_ROOT': os.environ.get('APPLICATION_ROOT'),
            'KEYCLOAK_SERVER_URL': os.environ.get('KEYCLOAK_SERVER_URL'),
            'KEYCLOAK_CLIENT_ID': os.environ.get('KEYCLOAK_CLIENT_ID'),
            'KEYCLOAK_DEBUG': os.environ.get('KEYCLOAK_DEBUG'),
        },
        'working_directory': os.getcwd(),
        'env_file_exists': os.path.exists('.env'),
        'python_path': sys.path[:3]  # First 3 entries
    }
    
    return f"<pre>{json.dumps(env_info, indent=2)}</pre>"