"""
Utilidades de paginación para el manejo de resultados filtrados que requieren
paginación manual en lugar de utilizar la paginación de SQLAlchemy.
"""

class ManualPagination:
    """
    Implementación de una paginación manual para casos donde necesitamos
    filtrar resultados después de obtenerlos de la base de datos.
    
    Esta clase imita el comportamiento de la clase Pagination de SQLAlchemy,
    ofreciendo propiedades y métodos similares para su uso en plantillas.
    """
    
    def __init__(self, items, page, per_page, total):
        """
        Inicializa un objeto de paginación manual.
        
        Args:
            items: Lista de elementos para la página actual
            page: Número de página actual (basado en 1)
            per_page: Número de elementos por página
            total: Número total de elementos en todas las páginas
        """
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    @property
    def has_prev(self):
        """Indica si hay una página anterior disponible."""
        return self.page > 1
        
    @property
    def has_next(self):
        """Indica si hay una página siguiente disponible."""
        return self.page < self.pages
        
    @property
    def prev_num(self):
        """Devuelve el número de la página anterior o None si no hay."""
        return self.page - 1 if self.has_prev else None
        
    @property
    def next_num(self):
        """Devuelve el número de la página siguiente o None si no hay."""
        return self.page + 1 if self.has_next else None
        
    def iter_pages(self, left_edge=2, left_current=2, right_current=2, right_edge=2):
        """
        Itera a través de los números de página a mostrar en la paginación.
        
        Este método imita el comportamiento de SQLAlchemy Pagination.iter_pages,
        generando los números de página que deberían mostrarse en la UI de paginación,
        con ellipsis donde sea apropiado.
        
        Args:
            left_edge: Número de páginas en el borde izquierdo
            left_current: Número de páginas a la izquierda de la página actual
            right_current: Número de páginas a la derecha de la página actual
            right_edge: Número de páginas en el borde derecho
            
        Yields:
            Números de página a mostrar o None para indicar ellipsis
        """
        last = 0
        for num in range(1, self.pages + 1):
            if (num <= left_edge or
                (self.page - left_current - 1 < num < self.page + right_current) or
                num > self.pages - right_edge):
                if last + 1 != num:
                    yield None
                yield num
                last = num
