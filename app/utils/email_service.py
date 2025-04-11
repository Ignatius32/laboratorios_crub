import os
from flask import current_app, url_for
from app.integrations.google_drive import drive_integration

class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    def send_email(to, subject, html_content):
        """
        Send an email using Google Apps Script integration
        
        Args:
            to (str): Recipient email address
            subject (str): Email subject
            html_content (str): HTML content of the email
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Get email configuration from environment or config
            sender_name = os.environ.get('MAIL_SENDER_NAME') or current_app.config.get('MAIL_SENDER_NAME', 'Sistema de Gestión de Laboratorios CRUB')
            reply_to = os.environ.get('MAIL_REPLY_TO') or current_app.config.get('MAIL_REPLY_TO', 'no-reply@crub.edu.ar')
            
            # Use Google Drive integration to send email
            success = drive_integration.send_email(
                to=to,
                subject=subject,
                html_body=html_content,
                sender_name=sender_name,
                reply_to=reply_to
            )
            
            if success:
                current_app.logger.info(f"Email sent to {to} with subject '{subject}'")
            else:
                current_app.logger.error(f"Failed to send email to {to}")
                
            return success
            
        except Exception as e:
            current_app.logger.error(f"Failed to send email: {str(e)}")
            return False
    
    @staticmethod
    def send_password_reset_email(user, token, is_new_user=False):
        """
        Send a password reset email to a user
        
        Args:
            user (Usuario): The user to send the email to
            token (str): The password reset token
            is_new_user (bool): True if this is a new user, False for password reset
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        # Generate password reset URL
        reset_url = url_for('auth.set_password', token=token, user_id=user.idUsuario, _external=True)
        
        # Set subject and content based on whether this is a new user or password reset
        if is_new_user:
            subject = "Bienvenido al Sistema de Gestión de Laboratorios CRUB"
            html_content = f"""
            <html>
                <body>
                    <h2>Bienvenido, {user.nombre} {user.apellido}!</h2>
                    <p>Se ha creado una cuenta para ti en el Sistema de Gestión de Laboratorios CRUB.</p>
                    <p>Por favor, establece tu contraseña haciendo clic en el siguiente enlace:</p>
                    <p><a href="{reset_url}">Establecer contraseña</a></p>
                    <p>Este enlace expirará en 24 horas.</p>
                    <p>Si no has solicitado esta cuenta, por favor ignora este mensaje.</p>
                    <p>Saludos,<br>El equipo del Sistema de Gestión de Laboratorios CRUB</p>
                </body>
            </html>
            """
        else:
            subject = "Restablecimiento de contraseña - Sistema de Gestión de Laboratorios CRUB"
            html_content = f"""
            <html>
                <body>
                    <h2>Hola, {user.nombre} {user.apellido}!</h2>
                    <p>Has solicitado restablecer tu contraseña para el Sistema de Gestión de Laboratorios CRUB.</p>
                    <p>Por favor, haz clic en el siguiente enlace para establecer una nueva contraseña:</p>
                    <p><a href="{reset_url}">Restablecer contraseña</a></p>
                    <p>Este enlace expirará en 24 horas.</p>
                    <p>Si no has solicitado este restablecimiento, por favor ignora este mensaje.</p>
                    <p>Saludos,<br>El equipo del Sistema de Gestión de Laboratorios CRUB</p>
                </body>
            </html>
            """
        
        # Send the email
        return EmailService.send_email(user.email, subject, html_content)
