import os
from flask import current_app
from app.integrations.google_drive import drive_integration

class EmailService:
    """Service for sending emails.

    Ya no manda mails de contraseña: esta aplicación no las administra. Quien
    la olvidó la restablece en las pantallas de cuenta de Huayca
    (URL_RESET_PASSWORD), que es donde viven de verdad.
    """

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
