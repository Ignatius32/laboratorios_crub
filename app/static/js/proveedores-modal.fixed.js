/**
 * Gestiona la funcionalidad del modal de creación de proveedores
 * Este script maneja la interacción con el modal para crear nuevos proveedores
 * sin recargar la página, agregándolos dinámicamente al select.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Referencias a elementos del DOM
    const btnNuevoProveedor = document.getElementById('btnNuevoProveedor');
    const idProveedorSelect = document.getElementById('idProveedor');
    const nuevoProveedorForm = document.getElementById('nuevoProveedorForm');
    const modalElement = document.getElementById('nuevoProveedorModal');
    
    // Si no encontramos los elementos necesarios, no continuamos
    if (!btnNuevoProveedor || !idProveedorSelect || !nuevoProveedorForm || !modalElement) {
        console.warn('No se encontraron todos los elementos necesarios para el modal de proveedores');
        return;
    }
    
    // Inicializar el modal de Bootstrap
    const nuevoProveedorModal = new bootstrap.Modal(modalElement);
    
    // Configurar el botón para abrir el modal de nuevo proveedor
    btnNuevoProveedor.addEventListener('click', function() {
        // Limpiar el formulario
        nuevoProveedorForm.reset();
        
        // Eliminar clases de error
        document.querySelectorAll('#nuevoProveedorModal .is-invalid').forEach(el => {
            el.classList.remove('is-invalid');
        });
        
        // Limpiar mensajes de error
        document.querySelectorAll('#nuevoProveedorModal .invalid-feedback').forEach(el => {
            el.textContent = '';
        });
        
        // Abrir el modal
        nuevoProveedorModal.show();
    });
    
    // Manejar el evento submit del formulario
    nuevoProveedorForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Mostrar indicador de carga
        const guardarBtn = document.getElementById('guardarProveedor');
        const originalBtnText = guardarBtn.innerHTML;
        guardarBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Guardando...';
        guardarBtn.disabled = true;
        
        // Obtener los datos del formulario
        const formData = new FormData(this);
        
        // Enviar solicitud para crear un nuevo proveedor
        fetch('/tecnicos/api/nuevo_proveedor', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': formData.get('csrf_token')
            }
        })
        .then(response => {
            // Check if the response is ok
            if (!response.ok) {
                throw new Error('Server responded with status: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Si la creación fue exitosa, agregar la nueva opción al select
                const nuevaOpcion = new Option(
                    data.nombre + " (" + data.cuit + ")", 
                    data.idProveedor, 
                    true,  // Selected
                    true   // Default selected
                );
                
                // Agregamos la nueva opción después de la primera (que podría ser "Nuevo proveedor...")
                idProveedorSelect.add(nuevaOpcion, 1);
                idProveedorSelect.value = data.idProveedor;
                
                // Cerrar el modal
                nuevoProveedorModal.hide();
                
                // Mostrar mensaje de éxito si SweetAlert2 está disponible
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        title: 'Éxito',
                        text: 'Proveedor creado correctamente',
                        icon: 'success',
                        timer: 2000,
                        showConfirmButton: false
                    });
                } else {
                    // Fallback si no está disponible SweetAlert2
                    alert('Proveedor creado correctamente');
                }
            } else {
                // Mostrar errores
                if (data.error) {
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            title: 'Error',
                            text: data.error,
                            icon: 'error'
                        });
                    } else {
                        alert('Error: ' + data.error);
                    }
                    
                    // Marcar campos con error si es necesario
                    if (data.error.includes('CUIT')) {
                        document.getElementById('cuit').classList.add('is-invalid');
                        document.getElementById('errorCuit').textContent = 'Ya existe un proveedor con este CUIT';
                    }
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: 'Error',
                    text: 'Ocurrió un error al procesar la solicitud',
                    icon: 'error'
                });
            } else {
                alert('Ocurrió un error al procesar la solicitud');
            }
        })
        .finally(() => {
            // Siempre restaurar el botón para eliminar el spinner
            guardarBtn.innerHTML = originalBtnText;
            guardarBtn.disabled = false;
        });
    });
    
    // Si el usuario hace click en la opción "Nuevo proveedor..." en el select
    if (idProveedorSelect) {
        idProveedorSelect.addEventListener('change', function() {
            if (this.value === "0") {
                // Abrir el modal directamente
                btnNuevoProveedor.click();
                
                // Restaurar la selección previa
                if (this.dataset.lastValue) {
                    this.value = this.dataset.lastValue;
                } else {
                    // O simplemente seleccionar la primera opción no "Nuevo proveedor..."
                    for (let i = 0; i < this.options.length; i++) {
                        if (this.options[i].value !== "0") {
                            this.selectedIndex = i;
                            break;
                        }
                    }
                }
            } else {
                // Guardar el valor seleccionado
                this.dataset.lastValue = this.value;
            }
        });
    }
});
