/**
 * JavaScript para mejoras responsivas en filtros de productos
 * Sistema de Gestión de Laboratorios CRUB
 */

document.addEventListener('DOMContentLoaded', function() {
    // Detectar si estamos en un dispositivo móvil
    const isMobile = window.innerWidth <= 768;
    
    // Función para ajustar el comportamiento de los filtros en móviles
    function adjustMobileFilters() {
        const filtersContainer = document.querySelector('.filters-container');
        if (!filtersContainer) return;
        
        // En móviles, hacer que los selects ocupen todo el ancho
        if (isMobile) {
            const selects = filtersContainer.querySelectorAll('select, input[type="text"]');
            selects.forEach(select => {
                select.style.width = '100%';
                select.style.minWidth = 'unset';
            });
        }
    }
    
    // Función para mejorar la interacción con el checkbox "Mostrar todos"
    function enhanceCheckboxInteraction() {
        const checkbox = document.getElementById('mostrarTodos');
        if (!checkbox) return;
        
        // Agregar indicador visual cuando el checkbox cambia
        checkbox.addEventListener('change', function() {
            const label = this.nextElementSibling;
            if (label) {
                if (this.checked) {
                    label.textContent = 'Mostrar todos ✓';
                    setTimeout(() => {
                        label.textContent = 'Mostrar todos';
                    }, 1000);
                } else {
                    label.textContent = 'Solo con stock ✓';
                    setTimeout(() => {
                        label.textContent = 'Mostrar todos';
                    }, 1000);
                }
            }
        });
    }
    
    // Función para mejorar la accesibilidad de los botones
    function enhanceButtonAccessibility() {
        const filterButton = document.querySelector('.filter-actions .btn-primary');
        const clearButton = document.querySelector('.filter-actions .btn-outline-secondary');
        
        if (filterButton) {
            filterButton.setAttribute('aria-label', 'Aplicar filtros de búsqueda');
        }
        
        if (clearButton) {
            clearButton.setAttribute('aria-label', 'Limpiar todos los filtros');
        }
    }
    
    // Función para manejar el redimensionamiento de ventana
    function handleResize() {
        const currentIsMobile = window.innerWidth <= 768;
        if (currentIsMobile !== isMobile) {
            // Solo recargar si hay un cambio significativo en el tamaño
            location.reload();
        }
    }
    
    // Función para mejorar la experiencia táctil en móviles
    function enhanceTouchExperience() {
        if (!('ontouchstart' in window)) return;
        
        const buttons = document.querySelectorAll('.filter-actions .btn');
        buttons.forEach(button => {
            button.addEventListener('touchstart', function() {
                this.style.transform = 'scale(0.98)';
            });
            
            button.addEventListener('touchend', function() {
                this.style.transform = 'scale(1)';
            });
        });
    }
    
    // Función para agregar feedback visual al envío del formulario
    function addFormSubmitFeedback() {
        const form = document.querySelector('.filters-container');
        if (!form) return;
        
        form.addEventListener('submit', function() {
            const submitButton = this.querySelector('.btn-primary');
            if (submitButton) {
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Filtrando...';
                submitButton.disabled = true;
            }
        });
    }
    
    // Función para mejorar el comportamiento del campo de búsqueda
    function enhanceSearchField() {
        const searchField = document.getElementById('search');
        if (!searchField) return;
        
        // Agregar funcionalidad de búsqueda en tiempo real (debounced)
        let searchTimeout;
        searchField.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const value = this.value;
            
            if (value.length === 0) {
                // Si se borra todo el contenido, agregar visual feedback
                this.style.borderColor = '#28a745';
                setTimeout(() => {
                    this.style.borderColor = '';
                }, 500);
            }
        });
        
        // Mejorar el placeholder en móviles
        if (isMobile && searchField.placeholder.length > 20) {
            searchField.placeholder = 'Buscar producto...';
        }
    }
    
    // Ejecutar todas las mejoras
    adjustMobileFilters();
    enhanceCheckboxInteraction();
    enhanceButtonAccessibility();
    enhanceTouchExperience();
    addFormSubmitFeedback();
    enhanceSearchField();
    
    // Escuchar cambios de tamaño de ventana
    window.addEventListener('resize', handleResize);
    
    // Mejorar la experiencia en orientación landscape/portrait en móviles
    window.addEventListener('orientationchange', function() {
        setTimeout(adjustMobileFilters, 100);
    });
});

// Función para mostrar/ocultar filtros en móviles (toggle)
function toggleMobileFilters() {
    const filtersContainer = document.querySelector('.filters-container');
    if (!filtersContainer) return;
    
    if (filtersContainer.style.display === 'none') {
        filtersContainer.style.display = 'flex';
    } else {
        filtersContainer.style.display = 'none';
    }
}

// Exportar funciones para uso global si es necesario
window.ProductFilters = {
    toggleMobileFilters: toggleMobileFilters
};
