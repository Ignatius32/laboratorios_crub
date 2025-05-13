// Admin Panel JavaScript

// Inicializar DataTables para todas las tablas de administración
$(document).ready(function() {
    // Configuración para tablas de administración
    $('.admin-table').DataTable({
        language: {
            url: '/static/js/Spanish.json'
        },
        responsive: true,
        stateSave: true,
        lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]],
        columnDefs: [
            { 
                targets: -1, // Última columna (acciones)
                orderable: false,
                searchable: false
            }
        ]
    });

    // Animación para tarjetas de dashboard
    $('.admin-dashboard-stats, .admin-panel-card').each(function(index) {
        $(this).css({
            'animation-delay': (index * 0.1) + 's',
            'animation': 'fadeIn 0.6s ease-in-out forwards'
        });
    });

    // Mejorar experiencia en formularios
    $('.admin-form .form-control, .admin-form .form-select').on('focus', function() {
        $(this).closest('.form-group').addClass('focused');
    });
    
    $('.admin-form .form-control, .admin-form .form-select').on('blur', function() {
        $(this).closest('.form-group').removeClass('focused');
    });

    // Tooltips para botones de acción
    $('[data-bs-toggle="tooltip"]').tooltip();
});

// Función para confirmar eliminación
function confirmarEliminar(url, nombre) {
    if (confirm('¿Estás seguro que deseas eliminar ' + nombre + '?')) {
        window.location = url;
    }
}
