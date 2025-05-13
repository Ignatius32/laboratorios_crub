/**
 * Manejador para confirmaciones de acciones destructivas usando modales de Bootstrap
 */
document.addEventListener('DOMContentLoaded', function() {
    // Crear un modal genérico reutilizable y agregarlo al final del body
    const modalHTML = `
    <div class="modal fade" id="confirmActionModal" tabindex="-1" aria-labelledby="confirmActionModalLabel" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="confirmActionModalLabel">Confirmar acción</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <p id="confirmActionMessage"></p>
                    <p class="text-danger mt-2" id="confirmActionWarning"></p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                    <button type="button" class="btn btn-danger" id="confirmActionButton">Confirmar</button>
                </div>
            </div>
        </div>
    </div>`;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Obtener referencias a los elementos del modal
    const confirmActionModal = document.getElementById('confirmActionModal');
    const bsConfirmModal = new bootstrap.Modal(confirmActionModal);
    const confirmActionMessage = document.getElementById('confirmActionMessage');
    const confirmActionWarning = document.getElementById('confirmActionWarning');
    const confirmActionButton = document.getElementById('confirmActionButton');
    
    // Variable para almacenar temporalmente la acción actual
    let currentAction = null;
    
    // Seleccionar todos los botones o enlaces con la clase 'confirm-action'
    const confirmButtons = document.querySelectorAll('.confirm-action');
    
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            // Prevenir la acción predeterminada (navegación o envío del formulario)
            event.preventDefault();
            
            // Obtener el mensaje personalizado y la advertencia del atributo data
            const message = this.getAttribute('data-message') || '¿Está seguro que desea realizar esta acción?';
            const warning = this.getAttribute('data-warning') || 'Esta acción no se puede deshacer.';
            const btnText = this.getAttribute('data-btn-text') || 'Confirmar';
            const btnClass = this.getAttribute('data-btn-class') || 'btn-danger';
            
            // Configurar el modal
            confirmActionMessage.textContent = message;
            confirmActionWarning.textContent = warning;
            confirmActionButton.textContent = btnText;
            
            // Eliminar clases btn-* existentes y añadir la nueva
            confirmActionButton.className = 'btn';
            confirmActionButton.classList.add(btnClass);
            
            // Guardar la acción actual para ejecutarla más tarde
            currentAction = () => {
                if (this.tagName === 'A') {
                    // Si es un enlace, navegar a la URL
                    window.location.href = this.getAttribute('href');
                } else if (this.tagName === 'BUTTON' && this.form) {
                    // Si es un botón dentro de un formulario, enviar el formulario
                    this.form.submit();
                } else if (this.getAttribute('data-form')) {
                    // Si tiene un atributo data-form, buscar y enviar ese formulario
                    document.getElementById(this.getAttribute('data-form')).submit();
                } else if (this.getAttribute('data-url')) {
                    // Si tiene un atributo data-url, navegar a esa URL
                    window.location.href = this.getAttribute('data-url');
                }
            };
            
            // Mostrar el modal
            bsConfirmModal.show();
        });
    });
    
    // Configurar el evento de clic para el botón de confirmación
    confirmActionButton.addEventListener('click', function() {
        // Ocultar el modal
        bsConfirmModal.hide();
        
        // Ejecutar la acción guardada después de un breve retraso
        // para permitir que el modal se cierre completamente
        setTimeout(() => {
            if (currentAction) {
                currentAction();
                currentAction = null;
            }
        }, 300);
    });
});
