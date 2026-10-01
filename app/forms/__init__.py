"""Los formularios de la aplicación.

Vivían dentro de app/routes/admin.py y app/routes/tecnicos.py, que así mezclaban
definición de formularios, vistas y helpers en archivos de 1600 y 950 líneas.
Acá quedan agrupados por entidad y se importan desde las rutas.
"""

from app.forms.gestion import (ExcelUploadForm, LaboratorioForm, ReporteForm,
                               UsuarioForm)
from app.forms.movimiento import MovimientoForm, MovimientoTecnicoForm
from app.forms.producto import ProductoForm, ProductoTecnicoForm
from app.forms.proveedor import ProveedorForm, ProveedorTecnicoForm

__all__ = [
    'ExcelUploadForm', 'LaboratorioForm', 'MovimientoForm',
    'MovimientoTecnicoForm', 'ProductoForm', 'ProductoTecnicoForm',
    'ProveedorForm', 'ProveedorTecnicoForm', 'ReporteForm', 'UsuarioForm',
]
