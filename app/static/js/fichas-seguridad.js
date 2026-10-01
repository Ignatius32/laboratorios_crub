/**
 * Visor de fichas de seguridad.
 *
 * Vivía embebido en base.html (unas 400 líneas dentro de un <script>), lo que
 * impedía cachearlo y mezclaba plantilla con lógica. Las URL de la aplicación
 * llegan por window.APP_URLS, que base.html arma con url_for: antes estaban
 * escritas a mano como "/descargar_archivo_drive/…" y bajo un despliegue en
 * subdirectorio (/laboratorios-crub) apuntaban fuera de la aplicación, así que
 * ninguna ficha se abría en producción.
 */

/**
 * Modal global para visualizar fichas de seguridad de productos químicos
 * Maneja PDFs, documentos de Word e imágenes desde Google Drive
 */
let fichasSeguridadModalInstance = null;
let lastFichaDriveId = null;
let lastFichaTipo = null;
let lastProductoNombre = null;

/**
 * Función principal para mostrar una ficha de seguridad
 * @param {string} driveId - ID del archivo en Google Drive
 * @param {string} nombreProducto - Nombre del producto químico
 * @param {string} tipoArchivo - Tipo de archivo (pdf, doc, docx, jpg, png, etc.)
 */
function showFichaSeguridad(driveId, nombreProducto, tipoArchivo = 'pdf') {
    // Elementos del DOM
    const modal = document.getElementById('fichasSeguridadModal');
    const modalTitle = document.getElementById('nombreProductoModal');
    const viewerContainer = document.getElementById('fichaViewerContainer');
    const loadingSpinner = document.getElementById('fichaLoadingSpinner');
    const openBtn = document.getElementById('openFichaNewTabBtn');
    const downloadBtn = document.getElementById('downloadFichaBtn');
    
    // Guardar información para uso posterior
    lastFichaDriveId = driveId;
    lastFichaTipo = tipoArchivo;
    lastProductoNombre = nombreProducto;
    
    // Actualizar título del modal
    modalTitle.textContent = nombreProducto || 'Producto desconocido';
    
    // Validar que se haya proporcionado un ID de Drive
    if (!driveId || driveId.trim() === '') {
        mostrarErrorFicha('No se ha configurado una ficha de seguridad para este producto.');
        mostrarModal();
        return;
    }
    
    // Mostrar spinner de carga
    mostrarCargaFicha();

    // Construir URLs para el archivo
    const fileType = (tipoArchivo || 'pdf').toLowerCase();
    const previewUrl = window.APP_URLS.descargarArchivo(driveId);
    const previewUrlDirecto = window.APP_URLS.fichaDirecta(driveId);

    // Configurar botones de acción
    configurarBotonesFicha(previewUrl, previewUrlDirecto);
      // Cargar documento según su tipo
    setTimeout(() => {
        cargarDocumentoPorTipo(fileType, previewUrl, previewUrlDirecto, nombreProducto);
    }, 300); // Pequeña pausa para mostrar el spinner
    
    // Mostrar modal
    mostrarModal();
}        /**
 * Carga el documento según su tipo de archivo
 * @param {string} fileType - Tipo de archivo
 * @param {string} previewUrl - URL del archivo (método principal)
 * @param {string} previewUrlDirecto - URL directa de Google Drive (fallback)
 * @param {string} nombreProducto - Nombre del producto
 */
function cargarDocumentoPorTipo(fileType, previewUrl, previewUrlDirecto, nombreProducto) {
    const viewerContainer = document.getElementById('fichaViewerContainer');

    try {
        let nodoVisor;

        if (['pdf'].includes(fileType)) {
            // Para PDFs usar iframe con parámetros de embebido y fallback
            nodoVisor = crearIframeFicha(
                `${previewUrl}#toolbar=1&navpanes=1&scrollbar=1&page=1&view=FitH`,
                nombreProducto,
                () => cargarConFallback(previewUrlDirecto, nombreProducto)
            );
        } else if (['doc', 'docx'].includes(fileType)) {
            // Para documentos de Word, usar iframe con visualizador y fallback
            nodoVisor = crearIframeFicha(
                previewUrl,
                nombreProducto,
                () => cargarConFallback(previewUrlDirecto, nombreProducto)
            );
        } else if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg'].includes(fileType)) {
            // Para imágenes mostrar directamente con fallback
            nodoVisor = document.createElement('div');
            nodoVisor.className = 'text-center p-4';

            const imagen = document.createElement('img');
            imagen.src = previewUrl;
            imagen.className = 'img-fluid';
            imagen.style.maxHeight = '600px';
            imagen.style.borderRadius = '8px';
            imagen.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
            imagen.alt = `Ficha de Seguridad - ${nombreProducto || ''}`;
            imagen.addEventListener('load', ocultarCargaFicha);
            imagen.addEventListener('error', function manejarError() {
                // Primer error: reintentar con la URL directa de Drive.
                // Segundo error: ya no hay de dónde cargar.
                if (imagen.src.includes('ficha_seguridad_directo')) {
                    imagen.removeEventListener('error', manejarError);
                    mostrarErrorFicha('Error al cargar la imagen de la ficha de seguridad.');
                } else {
                    imagen.src = previewUrlDirecto;
                }
            });

            nodoVisor.appendChild(imagen);
        } else {
            // Para otros tipos de archivo mostrar mensaje con ambas opciones
            nodoVisor = crearAvisoNoVisualizable(fileType, previewUrl, previewUrlDirecto);
        }

        // Insertar el contenido y ocultar spinner
        viewerContainer.replaceChildren(nodoVisor);

        // Si es una imagen o contenido sin iframe, ocultar spinner inmediatamente
        if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg'].includes(fileType) || !['pdf', 'doc', 'docx'].includes(fileType)) {
            setTimeout(ocultarCargaFicha, 500);
        }

    } catch (error) {
        console.error('Error al cargar la ficha de seguridad:', error);
        mostrarErrorFicha('Error técnico al cargar la ficha de seguridad.');
    }
}

/**
 * Crea el iframe del visor.
 * Se construye vía DOM (no innerHTML) para que el nombre del producto
 * nunca se interprete como marcado.
 * @param {string} src - URL a cargar
 * @param {string} nombreProducto - Nombre del producto
 * @param {Function} [alFallar] - Callback opcional ante error de carga
 * @returns {HTMLIFrameElement}
 */
function crearIframeFicha(src, nombreProducto, alFallar) {
    const iframe = document.createElement('iframe');
    iframe.src = src;
    iframe.width = '100%';
    iframe.height = '700px';
    iframe.style.border = 'none';
    iframe.style.minHeight = '700px';
    iframe.title = `Ficha de Seguridad - ${nombreProducto || ''}`;
    iframe.setAttribute('allow', 'fullscreen');
    iframe.addEventListener('load', ocultarCargaFicha);
    if (typeof alFallar === 'function') {
        iframe.addEventListener('error', alFallar);
    }
    return iframe;
}

/**
 * Crea el aviso para tipos de archivo que no se pueden mostrar en línea
 * @param {string} fileType - Tipo de archivo
 * @param {string} previewUrl - URL de descarga
 * @param {string} previewUrlDirecto - URL directa de Google Drive
 * @returns {HTMLDivElement}
 */
function crearAvisoNoVisualizable(fileType, previewUrl, previewUrlDirecto) {
    const aviso = document.createElement('div');
    aviso.className = 'alert alert-info m-4';
    aviso.innerHTML = `
        <i class="fas fa-file-alt fa-2x mb-3 d-block text-center"></i>
        <h5 class="text-center">Archivo no visualizable en línea</h5>
        <p class="text-center mb-3"></p>
        <div class="text-center">
            <a class="btn btn-primary me-2" target="_blank" rel="noopener">
                <i class="fas fa-download me-2"></i>Descargar archivo
            </a>
            <a class="btn btn-outline-primary" target="_blank" rel="noopener">
                <i class="fas fa-external-link-alt me-2"></i>Abrir en Google Drive
            </a>
        </div>
    `;

    const parrafo = aviso.querySelector('p');
    parrafo.textContent = `Este tipo de archivo (${(fileType || '').toUpperCase()}) no puede ser visualizado directamente en el navegador.`;

    const enlaces = aviso.querySelectorAll('a');
    enlaces[0].href = previewUrl;
    enlaces[1].href = previewUrlDirecto;

    return aviso;
}

/**
 * Función de fallback para cargar con URL directa de Google Drive
 * @param {string} fallbackUrl - URL directa de Google Drive
 * @param {string} nombreProducto - Nombre del producto
 */
function cargarConFallback(fallbackUrl, nombreProducto) {
    console.log('Cargando con fallback URL:', fallbackUrl);
    const viewerContainer = document.getElementById('fichaViewerContainer');

    viewerContainer.replaceChildren(crearIframeFicha(fallbackUrl, nombreProducto));
    setTimeout(ocultarCargaFicha, 1000);
}

/**
 * Configura los botones de acción del modal
 * @param {string} previewUrl - URL del archivo
 * @param {string} previewUrlDirecto - URL directa de Google Drive
 */
function configurarBotonesFicha(previewUrl, previewUrlDirecto) {
    const openBtn = document.getElementById('openFichaNewTabBtn');
    const downloadBtn = document.getElementById('downloadFichaBtn');
    
    // Configurar URLs de los botones (usar URL directa para abrir en nueva pestaña)
    openBtn.href = previewUrlDirecto || previewUrl;
    downloadBtn.href = previewUrl; // Usar URL de descarga para el botón de descarga
    
    // Mostrar botones
    openBtn.style.display = '';
    downloadBtn.style.display = '';
    
    // Agregar atributo de descarga al botón de descarga
    downloadBtn.setAttribute('download', `ficha_seguridad_${lastProductoNombre || 'producto'}.${lastFichaTipo || 'pdf'}`);
}

/**
 * Muestra el spinner de carga
 */
function mostrarCargaFicha() {
    const viewerContainer = document.getElementById('fichaViewerContainer');
    const loadingSpinner = document.getElementById('fichaLoadingSpinner');
    
    viewerContainer.innerHTML = '';
    loadingSpinner.classList.remove('d-none');
}

/**
 * Oculta el spinner de carga
 */
function ocultarCargaFicha() {
    const loadingSpinner = document.getElementById('fichaLoadingSpinner');
    loadingSpinner.classList.add('d-none');
}

/**
 * Muestra un mensaje de error en el modal
 * @param {string} mensaje - Mensaje de error a mostrar
 */
function mostrarErrorFicha(mensaje) {
    const viewerContainer = document.getElementById('fichaViewerContainer');
    const openBtn = document.getElementById('openFichaNewTabBtn');
    const downloadBtn = document.getElementById('downloadFichaBtn');
    
    viewerContainer.innerHTML = `
        <div class="alert alert-warning m-4">
            <i class="fas fa-exclamation-triangle fa-2x mb-3 d-block text-center text-warning"></i>
            <h5 class="text-center">Ficha de Seguridad No Disponible</h5>
            <p class="text-center mb-0" data-mensaje-error></p>
            <hr>
            <p class="text-center small text-muted mb-0">
                <i class="fas fa-info-circle me-1"></i>
                Contacte al administrador del laboratorio para obtener la ficha de seguridad correspondiente.
            </p>
        </div>
    `;
    viewerContainer.querySelector('[data-mensaje-error]').textContent = mensaje;
    
    // Ocultar botones si hay error
    openBtn.style.display = 'none';
    downloadBtn.style.display = 'none';
    
    ocultarCargaFicha();
}

/**
 * Muestra el modal
 */
function mostrarModal() {
    fichasSeguridadModalInstance = new bootstrap.Modal(document.getElementById('fichasSeguridadModal'));
    fichasSeguridadModalInstance.show();
}

/**
 * Maneja el evento de cerrar modal para limpiar contenido
 */
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('fichasSeguridadModal');
    const openBtn = document.getElementById('openFichaNewTabBtn');
    const downloadBtn = document.getElementById('downloadFichaBtn');

    // Apertura de fichas de seguridad por delegación.
    // Los datos viajan en atributos data-*, nunca dentro de un onclick:
    // así el nombre del producto jamás se evalúa como código.
    // Al estar delegado en document también funciona con las filas que
    // DataTables agrega dinámicamente al paginar.
    document.addEventListener('click', function(evento) {
        const disparador = evento.target.closest('[data-ficha-url]');
        if (!disparador) {
            return;
        }

        evento.preventDefault();
        const url = disparador.dataset.fichaUrl;
        const nombre = disparador.dataset.fichaNombre || '';

        if (disparador.dataset.fichaModo === 'temporal') {
            mostrarFichaSeguridadTemporal(url, nombre);
        } else {
            mostrarFichaSeguridadDesdeUrl(url, nombre);
        }
    });

    // Limpiar contenido al cerrar el modal
    modal.addEventListener('hidden.bs.modal', function () {
        document.getElementById('fichaViewerContainer').innerHTML = '';
        document.getElementById('nombreProductoModal').textContent = 'Producto';
        lastFichaDriveId = null;
        lastFichaTipo = null;
        lastProductoNombre = null;
        ocultarCargaFicha();
    });
    
    // Cerrar modal automáticamente al hacer clic en los botones de acción
    if (openBtn) {
        openBtn.addEventListener('click', function(e) {
            if (fichasSeguridadModalInstance) {
                setTimeout(() => {
                    fichasSeguridadModalInstance.hide();
                }, 300);
            }
        });
    }
    
    if (downloadBtn) {
        downloadBtn.addEventListener('click', function(e) {
            if (fichasSeguridadModalInstance) {
                setTimeout(() => {
                    fichasSeguridadModalInstance.hide();
                }, 300);
            }
        });
    }
});        /**
 * Función de utilidad para extraer el ID de Google Drive de una URL
 * @param {string} url - URL de Google Drive
 * @returns {string|null} - ID del archivo o null si no se encuentra
 */
function extraerDriveIdDeUrl(url) {
    if (!url) return null;
    
    // Patrones comunes de URLs de Google Drive
    const patterns = [
        /\/file\/d\/([a-zA-Z0-9-_]+)/,
        /id=([a-zA-Z0-9-_]+)/,
        /\/d\/([a-zA-Z0-9-_]+)/
    ];
    
    for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match) return match[1];
    }
    
    // Si la URL parece ser solo el ID
    if (/^[a-zA-Z0-9-_]+$/.test(url)) {
        return url;
    }
    
    return null;
}

/**
 * Función auxiliar que extrae el ID de Drive de una URL y llama a showFichaSeguridad
 * @param {string} url - URL completa de Google Drive
 * @param {string} nombreProducto - Nombre del producto
 * @param {string} tipoArchivo - Tipo de archivo (opcional, por defecto 'pdf')
 */
function mostrarFichaSeguridadDesdeUrl(url, nombreProducto, tipoArchivo = 'pdf') {
    const driveId = extraerDriveIdDeUrl(url);
    
    if (!driveId) {
        console.error('No se pudo extraer el ID de Google Drive de la URL:', url);
        mostrarErrorFicha('URL de ficha de seguridad no válida. Contacte al administrador.');
        mostrarModal();
        return;
    }
    
    // Intentar detectar el tipo de archivo desde la URL o el nombre
    let tipoDetectado = tipoArchivo;
    if (url.includes('.pdf') || url.includes('pdf')) {
        tipoDetectado = 'pdf';
    } else if (url.includes('.doc')) {
        tipoDetectado = url.includes('.docx') ? 'docx' : 'doc';
    } else if (url.includes('.jpg') || url.includes('.jpeg')) {
        tipoDetectado = 'jpg';
    } else if (url.includes('.png')) {
        tipoDetectado = 'png';
    }
    
    showFichaSeguridad(driveId, nombreProducto, tipoDetectado);
}
/**
 * Muestra una ficha embebiendo Google Drive directamente, sin pasar por el
 * backend. Se usa con data-ficha-modo="temporal".
 *
 * Venía de fichas-seguridad-ejemplos.js, un archivo de demostración que se
 * cargaba en todas las páginas y que además de esta función traía siete
 * ejemplos, un volcado de SQL de prueba dentro de una cadena y un console.log
 * en cada carga. Se conservó sólo esto, que es lo único que el visor llama.
 *
 * @param {string} urlFicha - URL o ID de Google Drive
 * @param {string} nombreProducto - Nombre del producto
 */
function mostrarFichaSeguridadTemporal(urlFicha, nombreProducto) {
    const viewerContainer = document.getElementById('fichaViewerContainer');
    const openBtn = document.getElementById('openFichaNewTabBtn');
    const downloadBtn = document.getElementById('downloadFichaBtn');

    document.getElementById('nombreProductoModal').textContent =
        nombreProducto || 'Producto desconocido';

    const driveId = extraerDriveIdDeUrl(urlFicha);
    if (!driveId) {
        mostrarErrorFicha('URL de ficha de seguridad no válida.');
        mostrarModal();
        return;
    }

    const previewUrl = `https://drive.google.com/file/d/${driveId}/preview`;
    openBtn.href = previewUrl;
    downloadBtn.href = `https://drive.google.com/file/d/${driveId}/view`;
    openBtn.style.display = '';
    downloadBtn.style.display = '';

    mostrarCargaFicha();
    mostrarModal();

    setTimeout(() => {
        viewerContainer.replaceChildren(crearIframeFicha(previewUrl, nombreProducto));
    }, 300);
}
