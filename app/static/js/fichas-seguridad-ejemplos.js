/**
 * Ejemplos de uso del Modal de Fichas de Seguridad
 * Para testing y demostración de funcionalidades
 */

// Ejemplo 1: Usar con ID directo de Google Drive
function ejemploFichaDirecta() {
    showFichaSeguridad(
        '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms', 
        'Ácido Sulfúrico H₂SO₄', 
        'pdf'
    );
}

// Ejemplo 2: Usar con URL completa de Google Drive
function ejemploFichaDesdeUrl() {
    mostrarFichaSeguridadDesdeUrl(
        'https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view?usp=sharing',
        'Hidróxido de Sodio NaOH'
    );
}

// Ejemplo 3: Manejar producto sin ficha
function ejemploSinFicha() {
    showFichaSeguridad(
        null, 
        'Producto sin ficha configurada', 
        'pdf'
    );
}

// Ejemplo 4: Ficha con imagen
function ejemploFichaImagen() {
    showFichaSeguridad(
        'imagen_ficha_ejemplo_id', 
        'Acetona C₃H₆O', 
        'jpg'
    );
}

// Ejemplo 5: Ficha con documento Word
function ejemploFichaWord() {
    showFichaSeguridad(
        'documento_word_ejemplo_id', 
        'Formaldehído CH₂O', 
        'docx'
    );
}

// Función para demostrar todos los ejemplos
function demostrarTodosLosEjemplos() {
    console.log('🧪 Demostraciones de fichas de seguridad disponibles:');
    console.log('- ejemploFichaDirecta(): PDF con ID directo');
    console.log('- ejemploFichaDesdeUrl(): PDF desde URL completa');
    console.log('- ejemploSinFicha(): Manejo de productos sin ficha');
    console.log('- ejemploFichaImagen(): Ficha en formato imagen');
    console.log('- ejemploFichaWord(): Ficha en formato Word');
    console.log('- ejemploFichaTemporal(): Solución temporal directa a Google Drive');
    console.log('\n💡 Para usar: Abre la consola del navegador y ejecuta cualquiera de estas funciones');
}

/**
 * SOLUCIÓN TEMPORAL - Función que usa directamente Google Drive
 * Esta función evita el backend mientras configuras las credenciales
 */
function convertirUrlGoogleDriveAPreview(driveUrl) {
    if (!driveUrl) return null;
    
    // Extraer ID de diferentes formatos de URL de Google Drive
    const patterns = [
        /\/file\/d\/([a-zA-Z0-9-_]+)/,
        /id=([a-zA-Z0-9-_]+)/,
        /\/d\/([a-zA-Z0-9-_]+)/
    ];
    
    let fileId = null;
    for (const pattern of patterns) {
        const match = driveUrl.match(pattern);
        if (match) {
            fileId = match[1];
            break;
        }
    }
    
    // Si no encontramos ID, verificar si la URL ya es solo el ID
    if (!fileId && /^[a-zA-Z0-9-_]+$/.test(driveUrl)) {
        fileId = driveUrl;
    }
    
    if (fileId) {
        return `https://drive.google.com/file/d/${fileId}/preview`;
    }
    
    return driveUrl; // Devolver URL original si no podemos convertirla
}

/**
 * SOLUCIÓN TEMPORAL - Función que bypasea el backend
 * Usa directamente Google Drive para mostrar fichas
 */
function mostrarFichaSeguridadTemporal(urlFicha, nombreProducto) {
    const modal = document.getElementById('fichasSeguridadModal');
    const modalTitle = document.getElementById('nombreProductoModal');
    const viewerContainer = document.getElementById('fichaViewerContainer');
    const openBtn = document.getElementById('openFichaNewTabBtn');
    const downloadBtn = document.getElementById('downloadFichaBtn');
    
    // Actualizar título
    modalTitle.textContent = nombreProducto || 'Producto desconocido';
    
    // Convertir URL a formato preview
    const previewUrl = convertirUrlGoogleDriveAPreview(urlFicha);
    
    if (!previewUrl) {
        // Usar la función de error ya existente
        if (typeof mostrarErrorFicha === 'function') {
            mostrarErrorFicha('URL de ficha de seguridad no válida.');
        } else {
            viewerContainer.innerHTML = `
                <div class="alert alert-warning m-4">
                    <h5>URL no válida</h5>
                    <p>La URL de la ficha de seguridad no es válida.</p>
                </div>
            `;
        }
        
        // Mostrar modal
        if (typeof mostrarModal === 'function') {
            mostrarModal();
        } else {
            const modalInstance = new bootstrap.Modal(modal);
            modalInstance.show();
        }
        return;
    }
    
    // Configurar botones
    openBtn.href = previewUrl;
    downloadBtn.href = previewUrl.replace('/preview', '/view'); // URL de descarga
    openBtn.style.display = '';
    downloadBtn.style.display = '';
    
    // Mostrar spinner de carga
    viewerContainer.innerHTML = `
        <div class="d-flex justify-content-center align-items-center" style="height: 400px;">
            <div class="text-center">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <p class="text-muted">Cargando ficha de seguridad...</p>
            </div>
        </div>
    `;
    
    // Mostrar modal
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
    
    // Cargar contenido después de mostrar el modal.
    // El iframe se construye vía DOM: interpolar nombreProducto dentro de
    // innerHTML permitiría inyectar marcado desde el nombre del producto.
    setTimeout(() => {
        const iframe = document.createElement('iframe');
        iframe.src = previewUrl;
        iframe.width = '100%';
        iframe.height = '700px';
        iframe.style.border = 'none';
        iframe.style.minHeight = '700px';
        iframe.title = `Ficha de Seguridad - ${nombreProducto || ''}`;
        iframe.setAttribute('allow', 'fullscreen');
        iframe.addEventListener('load', () => console.log('Ficha cargada exitosamente'));

        viewerContainer.replaceChildren(iframe);
    }, 500);
}

// Ejemplo usando la solución temporal
function ejemploFichaTemporal() {
    mostrarFichaSeguridadTemporal(
        'https://drive.google.com/file/d/1z8vE4t-d1Je64zEWJIAq0XSivnaU_4R-/view',
        'Producto de Prueba (Temporal)'
    );
}

/**
 * Función de testing para verificar diferentes formatos de URL
 */
function testearConversionUrls() {
    const urlsTest = [
        'https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view',
        'https://drive.google.com/open?id=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms',
        'https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit',
        '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms',
        '1z8vE4t-d1Je64zEWJIAq0XSivnaU_4R-'  // Tu ID de ejemplo
    ];
    
    console.log('🧪 Testing conversión de URLs:');
    urlsTest.forEach(url => {
        const converted = convertirUrlGoogleDriveAPreview(url);
        console.log(`Original: ${url}`);
        console.log(`Convertida: ${converted}`);
        console.log('---');
    });
}

// Exponer funciones para testing en la consola del navegador
if (typeof window !== 'undefined') {
    window.ejemploFichaDirecta = ejemploFichaDirecta;
    window.ejemploFichaDesdeUrl = ejemploFichaDesdeUrl;
    window.ejemploSinFicha = ejemploSinFicha;
    window.ejemploFichaImagen = ejemploFichaImagen;
    window.ejemploFichaWord = ejemploFichaWord;
    window.ejemploFichaTemporal = ejemploFichaTemporal;
    window.testearConversionUrls = testearConversionUrls;
    window.mostrarFichaSeguridadTemporal = mostrarFichaSeguridadTemporal;
    window.demostrarTodosLosEjemplos = demostrarTodosLosEjemplos;
}

// HTML de ejemplo para botones de testing
const htmlEjemplos = `
<div class="card mt-4">
    <div class="card-header">
        <h5>Ejemplos de Fichas de Seguridad</h5>
    </div>
    <div class="card-body">
        <div class="row">
            <div class="col-md-6 mb-3">
                <button class="btn btn-warning w-100" onclick="ejemploFichaDirecta()">
                    <i class="fas fa-shield-alt me-2"></i>Ácido Sulfúrico (PDF)
                </button>
            </div>
            <div class="col-md-6 mb-3">
                <button class="btn btn-warning w-100" onclick="ejemploFichaDesdeUrl()">
                    <i class="fas fa-shield-alt me-2"></i>Hidróxido de Sodio (URL)
                </button>
            </div>
            <div class="col-md-6 mb-3">
                <button class="btn btn-secondary w-100" onclick="ejemploSinFicha()">
                    <i class="fas fa-exclamation-triangle me-2"></i>Sin Ficha
                </button>
            </div>
            <div class="col-md-6 mb-3">
                <button class="btn btn-info w-100" onclick="ejemploFichaImagen()">
                    <i class="fas fa-image me-2"></i>Acetona (Imagen)
                </button>
            </div>
            <div class="col-md-6 mb-3">
                <button class="btn btn-success w-100" onclick="ejemploFichaWord()">
                    <i class="fas fa-file-word me-2"></i>Formaldehído (Word)
                </button>
            </div>
            <div class="col-md-6 mb-3">
                <button class="btn btn-danger w-100" onclick="ejemploFichaTemporal()">
                    <i class="fas fa-external-link-alt me-2"></i>Ficha Temporal (Drive)
                </button>
            </div>
            <div class="col-md-6 mb-3">
                <button class="btn btn-outline-primary w-100" onclick="mostrarEjemplos()">
                    <i class="fas fa-code me-2"></i>Ver Console Log
                </button>
            </div>
        </div>
    </div>
</div>
`;

// Datos de ejemplo para testing en base de datos
const productosEjemplo = [
    {
        idProducto: 'QUIM001',
        nombre: 'Ácido Sulfúrico H₂SO₄',
        urlFichaSeguridad: 'https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view',
        tipoProducto: 'droguero',
        estadoFisico: 'liquido',
        controlSedronar: false
    },
    {
        idProducto: 'QUIM002',
        nombre: 'Hidróxido de Sodio NaOH',
        urlFichaSeguridad: '1ABC123DefGhi456JklMno789PqrStu901VwxYz234',
        tipoProducto: 'droguero',
        estadoFisico: 'solido',
        controlSedronar: false
    },
    {
        idProducto: 'QUIM003',
        nombre: 'Acetona C₃H₆O',
        urlFichaSeguridad: 'https://drive.google.com/open?id=1XYZ789AbcDef012GhiJkl345MnoPqr678',
        tipoProducto: 'droguero',
        estadoFisico: 'liquido',
        controlSedronar: true
    },
    {
        idProducto: 'QUIM004',
        nombre: 'Formaldehído CH₂O',
        urlFichaSeguridad: null, // Sin ficha configurada
        tipoProducto: 'droguero',
        estadoFisico: 'liquido',
        controlSedronar: true
    }
];

// SQL de ejemplo para insertar productos de prueba
const sqlEjemplos = `
-- Productos químicos de ejemplo con fichas de seguridad
INSERT INTO producto (idProducto, nombre, descripcion, tipoProducto, estadoFisico, controlSedronar, urlFichaSeguridad, stockMinimo, marca) VALUES
('QUIM001', 'Ácido Sulfúrico H₂SO₄', 'Ácido fuerte utilizado en análisis químicos', 'droguero', 'liquido', 0, 'https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view', 1.0, 'Sigma-Aldrich'),
('QUIM002', 'Hidróxido de Sodio NaOH', 'Base fuerte para neutralización y síntesis', 'droguero', 'solido', 0, '1ABC123DefGhi456JklMno789PqrStu901VwxYz234', 0.5, 'Merck'),
('QUIM003', 'Acetona C₃H₆O', 'Solvente orgánico de uso común', 'droguero', 'liquido', 1, 'https://drive.google.com/open?id=1XYZ789AbcDef012GhiJkl345MnoPqr678', 2.0, 'Sintorgan'),
('QUIM004', 'Formaldehído CH₂O', 'Conservante y desinfectante', 'droguero', 'liquido', 1, NULL, 0.1, 'Anedra');

-- Laboratorio de ejemplo
INSERT INTO laboratorio (idLaboratorio, nombre, direccion, telefono, email) VALUES
('LAB001', 'Laboratorio de Química Analítica', 'Av. Pioneros del Valle 2500', '294-4445600', 'quimica@crub.uncoma.edu.ar');

-- Stock inicial de ejemplo
INSERT INTO stock (idProducto, idLaboratorio, cantidad) VALUES
('QUIM001', 'LAB001', 5.0),
('QUIM002', 'LAB001', 2.5),
('QUIM003', 'LAB001', 10.0),
('QUIM004', 'LAB001', 0.5);
`;

console.log('Archivo de ejemplos cargado. Usa mostrarEjemplos() para ver las funciones disponibles.');
