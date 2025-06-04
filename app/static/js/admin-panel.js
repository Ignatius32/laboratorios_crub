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
        ]    });

    // Mejorar experiencia en formularios
    $('.admin-form .form-control, .admin-form .form-select').on('focus', function() {
        $(this).closest('.form-group').addClass('focused');
    });
    
    $('.admin-form .form-control, .admin-form .form-select').on('blur', function() {
        $(this).closest('.form-group').removeClass('focused');
    });

    // Tooltips para botones de acción    $('[data-bs-toggle="tooltip"]').tooltip();
});

// Las funciones de confirmación ahora están en common.js
// confirmarEliminar() está disponible globalmente
