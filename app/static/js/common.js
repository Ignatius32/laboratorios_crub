/**
 * Funciones JavaScript comunes para toda la aplicación
 * Sistema de Gestión de Laboratorios CRUB
 */

/**
 * Función unificada para confirmar eliminación de elementos
 * @param {string} mensaje - Mensaje personalizado o nombre del elemento a eliminar
 * @param {string} url - URL para realizar la eliminación (opcional)
 * @returns {boolean} - true si se confirma, false si se cancela
 */
function confirmarEliminacion(mensaje, url = null) {
    // Si no se pasa URL, significa que se está usando como simple confirmación
    if (url === null) {
        // Formato: confirmarEliminacion('¿Estás seguro que deseas eliminar este producto?')
        return confirm(mensaje);
    } else {
        // Formato: confirmarEliminacion('el producto XYZ', '/admin/productos/delete/123')
        const mensajeCompleto = `¿Estás seguro que deseas eliminar ${mensaje}?`;
        if (confirm(mensajeCompleto)) {
            window.location.href = url;
            return true;
        }
        return false;
    }
}

/**
 * Alias para compatibilidad con código existente
 * @param {string} url - URL para realizar la eliminación
 * @param {string} nombre - Nombre del elemento a eliminar
 */
function confirmarEliminar(url, nombre) {
    return confirmarEliminacion(nombre, url);
}

/**
 * Inicializar funcionalidades comunes cuando se carga el DOM
 */
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips de Bootstrap en toda la aplicación
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => 
        new bootstrap.Tooltip(tooltipTriggerEl)
    );
    
    // Mejorar experiencia en formularios
    const formControls = document.querySelectorAll('.form-control, .form-select');
    formControls.forEach(control => {
        control.addEventListener('focus', function() {
            this.closest('.form-group, .mb-3')?.classList.add('focused');
        });
        
        control.addEventListener('blur', function() {            this.closest('.form-group, .mb-3')?.classList.remove('focused');
        });
    });
});

/**
 * Función para mostrar mensajes de éxito/error
 * @param {string} mensaje - Mensaje a mostrar
 * @param {string} tipo - Tipo de mensaje: 'success', 'error', 'warning', 'info'
 */
function mostrarMensaje(mensaje, tipo = 'info') {
    // Crear elemento de alerta
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${tipo === 'error' ? 'danger' : tipo} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
    `;
    
    // Insertar al inicio del contenido principal
    const mainContent = document.querySelector('main, .container, .container-fluid');
    if (mainContent) {
        mainContent.insertBefore(alertDiv, mainContent.firstChild);
        
        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

/**
 * Función para validar formularios antes del envío
 * @param {HTMLFormElement} form - Formulario a validar
 * @returns {boolean} - true si es válido, false si no
 */
function validarFormulario(form) {
    const camposRequeridos = form.querySelectorAll('[required]');
    let esValido = true;
    
    camposRequeridos.forEach(campo => {
        if (!campo.value.trim()) {
            campo.classList.add('is-invalid');
            esValido = false;
        } else {
            campo.classList.remove('is-invalid');
        }
    });
    
    return esValido;
}
