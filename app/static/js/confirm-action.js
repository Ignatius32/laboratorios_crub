/**
 * Manejador para confirmaciones de acciones destructivas
 */
document.addEventListener('DOMContentLoaded', function() {
    // Seleccionar todos los botones o enlaces con la clase 'confirm-action'
    const confirmButtons = document.querySelectorAll('.confirm-action');
    
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            // Prevenir la acción predeterminada (navegación o envío del formulario)
            event.preventDefault();
            
            // Obtener el mensaje personalizado del atributo data-message o usar un mensaje predeterminado
            const message = this.getAttribute('data-message') || '¿Está seguro que desea realizar esta acción?';
            
            // Mostrar diálogo de confirmación
            if (confirm(message)) {
                // Si el usuario confirma, ejecutar la acción original
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
            }
        });
    });
});
