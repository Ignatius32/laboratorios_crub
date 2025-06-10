from flask import Blueprint, render_template, redirect, url_for, Response, request, abort
from flask_login import current_user, login_required
from datetime import datetime
import base64
import io
from app.integrations.google_drive import drive_integration

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.rol == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('tecnicos.dashboard'))
    return render_template('index.html', title='Inicio', now=datetime.now())

@main.route('/about')
def about():
    return render_template('about.html', title='Acerca de', now=datetime.now())

@main.route('/descargar_archivo_drive/<file_id>')
@login_required
def descargar_archivo_drive(file_id):
    """
    Endpoint para servir archivos desde Google Drive
    Usado principalmente para fichas de seguridad embebidas en modales
    """
    try:
        # Validar el file_id (debe ser alfanumérico y guiones)
        if not file_id or not file_id.replace('-', '').replace('_', '').isalnum():
            abort(400, description="ID de archivo no válido")
        
        # Intentar obtener el archivo desde Google Drive
        file_result = drive_integration.download_file(file_id)
        
        if not file_result or 'error' in file_result:
            error_msg = file_result.get('error') if file_result else 'Archivo no encontrado'
            abort(404, description=f"No se pudo obtener el archivo: {error_msg}")
        
        # Decodificar los datos del archivo
        try:
            file_data = base64.b64decode(file_result['file_data'])
        except Exception as e:
            abort(500, description="Error al decodificar el archivo")
        
        # Obtener información del archivo
        file_name = file_result.get('file_name', f'archivo_{file_id}')
        mime_type = file_result.get('mime_type', 'application/octet-stream')
        file_size = file_result.get('file_size', len(file_data))
        
        # Determinar el tipo MIME apropiado para archivos comunes
        if not mime_type or mime_type == 'application/octet-stream':
            if file_name.lower().endswith('.pdf'):
                mime_type = 'application/pdf'
            elif file_name.lower().endswith(('.jpg', '.jpeg')):
                mime_type = 'image/jpeg'
            elif file_name.lower().endswith('.png'):
                mime_type = 'image/png'
            elif file_name.lower().endswith('.gif'):
                mime_type = 'image/gif'
            elif file_name.lower().endswith(('.doc', '.docx')):
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        
        # Crear el objeto de respuesta
        response = Response(
            file_data,
            mimetype=mime_type,
            headers={
                'Content-Disposition': f'inline; filename="{file_name}"',
                'Content-Length': str(file_size),
                'Cache-Control': 'public, max-age=3600',  # Cache por 1 hora
                'X-Content-Type-Options': 'nosniff',
                # Headers adicionales para PDFs
                'X-Frame-Options': 'SAMEORIGIN',  # Permitir embebido en iframe del mismo origen
                'Content-Security-Policy': "frame-ancestors 'self'"
            }
        )
        
        # Para PDFs, agregar headers adicionales para mejor compatibilidad
        if mime_type == 'application/pdf':
            response.headers['Accept-Ranges'] = 'bytes'
        
        return response
        
    except Exception as e:
        # Log del error para debugging
        from flask import current_app
        current_app.logger.error(f"Error al servir archivo {file_id}: {str(e)}")
        abort(500, description="Error interno del servidor")

@main.route('/vista_previa_archivo/<file_id>')
@login_required
def vista_previa_archivo(file_id):
    """
    Endpoint alternativo que intenta obtener una URL de streaming directo
    para casos donde la descarga completa no sea necesaria
    """
    try:
        # Validar el file_id
        if not file_id or not file_id.replace('-', '').replace('_', '').isalnum():
            abort(400, description="ID de archivo no válido")
        
        # Intentar obtener URL de streaming
        stream_result = drive_integration.get_file_stream_url(file_id)
        
        if stream_result and 'stream_url' in stream_result and not 'error' in stream_result:
            # Redirigir a la URL de streaming de Google Drive
            return redirect(stream_result['stream_url'])
        else:
            # Si no hay URL de streaming, usar el método de descarga
            return redirect(url_for('main.descargar_archivo_drive', file_id=file_id))
            
    except Exception as e:
        # Log del error para debugging
        from flask import current_app
        current_app.logger.error(f"Error al obtener vista previa {file_id}: {str(e)}")
        # Fallback al método de descarga
        return redirect(url_for('main.descargar_archivo_drive', file_id=file_id))

@main.route('/ficha_seguridad_directo/<file_id>')
@login_required  
def ficha_seguridad_directo(file_id):
    """
    Endpoint simplificado que redirige directamente a Google Drive
    para casos donde la descarga completa no sea necesaria
    """
    try:
        # Validar el file_id
        if not file_id or not file_id.replace('-', '').replace('_', '').isalnum():
            abort(400, description="ID de archivo no válido")
        
        # Construir URL directa de Google Drive para embebido
        drive_url = f"https://drive.google.com/file/d/{file_id}/preview"
        
        # Log de la acción
        from flask import current_app
        current_app.logger.info(f"Redirigiendo a ficha de seguridad: {file_id}")
        
        return redirect(drive_url)
        
    except Exception as e:
        # Log del error para debugging
        from flask import current_app
        current_app.logger.error(f"Error al acceder a ficha directa {file_id}: {str(e)}")
        abort(500, description="Error interno del servidor")