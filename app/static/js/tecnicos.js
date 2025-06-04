// Script específico para la sección de técnicos

$(document).ready(function() {
    // Inicializar tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Inicializar tablas de datos
    if ($('.tecnico-table').length) {
        $('.tecnico-table').DataTable({
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
    }
    
    // Filtros dinámicos para productos
    $('#filterTipoProducto').on('change', function() {
        let valor = $(this).val();
        if (valor) {
            $('.producto-item').hide();
            $('.producto-item[data-tipo="' + valor + '"]').show();
        } else {
            $('.producto-item').show();
        }
    });
    
    // Búsqueda rápida para productos
    $('#quickSearch').on('keyup', function() {
        let valor = $(this).val().toLowerCase();
        
        if (valor) {
            $('.producto-item').each(function() {
                let texto = $(this).text().toLowerCase();
                if (texto.indexOf(valor) > -1) {
                    $(this).show();
                } else {
                    $(this).hide();
                }
            });
        } else {
            $('.producto-item').show();
        }
    });
    
    // Funcionalidad para selección de productos en movimientos
    $('.select-producto').on('click', function() {
        const productoId = $(this).data('producto-id');
        const productoNombre = $(this).data('producto-nombre');
        
        $('#selectedProductoId').val(productoId);
        $('#selectedProductoNombre').text(productoNombre);
        $('#productoSeleccionado').removeClass('d-none');
        
        // Cerrar modal si existe
        if ($('#seleccionarProductoModal').length) {
            $('#seleccionarProductoModal').modal('hide');
        }
    });
    
    // Validación de cantidad en movimientos
    $('#cantidad').on('change', function() {
        const cantidad = parseInt($(this).val());
        const stock = parseInt($('#stockActual').val());
        const tipoMovimiento = $('#tipoMovimiento').val();
        
        if (tipoMovimiento === 'salida' && cantidad > stock) {
            $('#cantidadError').text('La cantidad no puede ser mayor al stock disponible (' + stock + ')').show();
            $('#submitBtn').prop('disabled', true);
        } else {
            $('#cantidadError').hide();
            $('#submitBtn').prop('disabled', false);
        }
    });
    
    // Animar tarjetas al cargar la página
    $('.card').each(function(index) {
        $(this).css('animation-delay', (index * 0.1) + 's');
        $(this).addClass('fade-in');
    });
});

// Las funciones de confirmación ahora están en common.js
// confirmarEliminacion() está disponible globalmente como confirmarEliminacion()

/**
 * Función para actualizar el stock disponible al seleccionar un producto
 */
function actualizarStockDisponible(productoId, labId) {
    if (!productoId) return;
    
    // Aquí se haría una llamada AJAX para obtener el stock actual
    $.ajax({
        url: '/tecnicos/obtener-stock/' + labId + '/' + productoId,
        method: 'GET',
        success: function(response) {
            $('#stockActual').val(response.stock);
            $('#stockDisponible').text(response.stock);
            
            // Mostrar advertencia si el stock es bajo
            if (response.stock <= response.stockMinimo) {
                $('#stockAdvertencia').removeClass('d-none');
            } else {
                $('#stockAdvertencia').addClass('d-none');
            }
        },
        error: function() {
            console.error('Error al obtener el stock');
        }
    });
}
