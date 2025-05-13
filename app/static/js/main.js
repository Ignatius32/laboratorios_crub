// Main JavaScript file

// Close alert messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    // Auto close alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Función para mostrar indicadores de carga
function showLoading(message = 'Procesando...') {
    // Crear el overlay para el spinner
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(255, 255, 255, 0.7)';
    overlay.style.zIndex = '9999';
    overlay.style.display = 'flex';
    overlay.style.justifyContent = 'center';
    overlay.style.alignItems = 'center';
    overlay.style.flexDirection = 'column';

    // Crear el spinner
    const spinner = document.createElement('div');
    spinner.className = 'spinner-border text-primary';
    spinner.setAttribute('role', 'status');
    spinner.style.width = '3rem';
    spinner.style.height = '3rem';

    // Mensaje de carga
    const messageElement = document.createElement('p');
    messageElement.className = 'mt-3';
    messageElement.textContent = message;
    messageElement.style.fontWeight = '500';

    // Agregar spinner y mensaje al overlay
    overlay.appendChild(spinner);
    overlay.appendChild(messageElement);

    // Agregar overlay al body
    document.body.appendChild(overlay);
}

// Función para ocultar indicador de carga
function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// Mostrar spinner al enviar formularios
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function() {
            if (form.getAttribute('data-no-loader') !== 'true') {
                showLoading('Enviando información...');
            }
        });
    });
});