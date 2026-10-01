"""Preparación de archivos subidos por formulario antes de mandarlos a Drive."""

import base64

# Lo que se acepta como ficha de seguridad desde el panel de administración.
EXTENSIONES_FICHA = ('pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx')


def preparar_ficha_seguridad(archivo, extensiones=EXTENSIONES_FICHA):
    """Valida el archivo de ficha de seguridad y lo devuelve en base64.

    Devuelve la terna (contenido_base64, extension, error). Cuando `error` no es
    None es el mensaje listo para flash() y los otros dos vienen en None.

    Este bloque estaba escrito dos veces, palabra por palabra, en new_producto y
    en edit_producto: mismas comprobaciones, misma lista de extensiones, mismos
    mensajes. Dos copias significan que endurecer la validación en una deja la
    otra floja, que es exactamente el tipo de descuido que conviene evitar en el
    camino que recibe archivos de afuera.
    """
    nombre = getattr(archivo, 'filename', None)
    if not nombre or '.' not in nombre:
        return None, None, 'Error: Archivo inválido'

    extension = nombre.rsplit('.', 1)[1].lower()
    if extension not in extensiones:
        return None, None, ('Error: Tipo de archivo no permitido. '
                            'Use PDF, JPG, PNG, DOC o DOCX.')

    return base64.b64encode(archivo.read()).decode('utf-8'), extension, None
