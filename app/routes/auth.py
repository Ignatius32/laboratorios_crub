from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from app.models.models import Usuario, db
from app.utils.email_service import EmailService
from werkzeug.security import generate_password_hash

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
def login():
    if current_user.is_authenticated:
        if current_user.rol == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            # Verificar si el técnico tiene laboratorios asignados y redirigir al primero
            if current_user.laboratorios:
                return redirect(url_for('tecnicos.panel_laboratorio', lab_id=current_user.laboratorios[0].idLaboratorio))
            else:
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
            else:
                flash('Error: No se encontró un usuario administrador en la base de datos', 'danger')
                return redirect(url_for('auth.login'))
                
            return redirect(url_for('admin.dashboard'))
        else:
            # Try to authenticate as regular user
            user = Usuario.query.filter_by(email=form.email.data).first()
            if user is None or not user.check_password(form.password.data):
                flash('Email o contraseña incorrectos', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=form.remember_me.data)
            
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                if user.rol == 'admin':
                    next_page = url_for('admin.dashboard')
                else:
                    # Redirigir a técnicos a su panel de laboratorio específico si tiene asignado
                    if user.laboratorios:
                        # Redirigir al panel del primer laboratorio asignado
                        next_page = url_for('tecnicos.panel_laboratorio', lab_id=user.laboratorios[0].idLaboratorio)
                    else:
                        # Alternativa si el técnico no tiene laboratorios asignados
                        next_page = url_for('tecnicos.dashboard')
            return redirect(next_page)
    
    return render_template('auth/login.html', title='Iniciar sesión', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente', 'success')
    return redirect(url_for('main.index'))

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password requests"""
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
                flash('Se ha enviado un correo electrónico con instrucciones para restablecer tu contraseña.', 'success')
            else:
                flash('No se pudo enviar el correo electrónico. Por favor, contacta al administrador.', 'danger')
        else:
            # We don't want to reveal that the email doesn't exist, so we show the same message
            flash('Se ha enviado un correo electrónico con instrucciones para restablecer tu contraseña.', 'success')
            
        return redirect(url_for('auth.login'))
        
    return render_template('auth/forgot_password.html', title='Recuperar Contraseña', form=form)

@auth.route('/set-password/<string:user_id>/<string:token>', methods=['GET', 'POST'])
def set_password(user_id, token):
    """Handle password reset/setup using a token"""
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    # Find the user
    user = Usuario.query.get(user_id)
    if not user:
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('auth.login'))
        
    # Check if token is valid
    token_valid = user.is_reset_token_valid(token)
    error_message = None
    is_new_user = user.password_hash == generate_password_hash('password123')  # Default password check
    
    form = SetPasswordForm()
    if form.validate_on_submit():
        if token_valid:
            # Set the new password
            user.set_password(form.password.data)
            db.session.commit()
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