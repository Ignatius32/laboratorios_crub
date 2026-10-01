"""Formularios de movimientos."""

from flask_wtf import FlaskForm
from wtforms import FileField, FloatField, SelectField, StringField
from wtforms.validators import DataRequired, Length, Optional, URL

from app.models.models import Laboratorio, Producto, Proveedor


# Tampoco se unifican. El del panel elige laboratorio de origen
# (idLaboratorio) porque el administrador puede cargar en cualquiera; el de
# técnicos lo toma de la URL y recibe por parámetro los laboratorios a los que
# la persona tiene acceso. Además difieren en el coerce de idProveedor (str
# contra int) y en dónde ubican la opción "Nuevo proveedor…". Son dos
# formularios parecidos, no uno duplicado.

class MovimientoForm(FlaskForm):
    tipoMovimiento = SelectField('Tipo de Movimiento', choices=[
        ('ingreso', 'Ingreso'), 
        ('compra', 'Compra'), 
        ('uso', 'Uso'),
        ('transferencia', 'Transferencia')
    ])
    cantidad = FloatField('Cantidad', validators=[DataRequired()])
    unidadMedida = SelectField('Unidad de Medida', choices=[
        ('Lt', 'Litros (Lt)'),
        ('Kg', 'Kilogramos (Kg)')
    ], validators=[DataRequired()])
    idProducto = SelectField('Producto', validators=[DataRequired()], coerce=str)
    idLaboratorio = SelectField('Laboratorio', validators=[DataRequired()], coerce=str)
    
    # Campos para movimientos tipo 'compra'
    tipoDocumento = SelectField('Tipo de Documento', choices=[
        ('factura', 'Factura'),
        ('remito', 'Remito')
    ], validators=[Optional()])
    numeroDocumento = StringField('Número de Documento', validators=[Optional(), Length(max=50)])
    fechaFactura = StringField('Fecha de Factura', validators=[Optional()])
    idProveedor = SelectField('Proveedor', validators=[Optional()])
    documento = FileField('Documento (PDF)', validators=[Optional()])
    
    # Campo para movimientos tipo 'transferencia'
    laboratorioDestino = SelectField('Laboratorio Destino', validators=[Optional()], coerce=str)
    
    def __init__(self, *args, **kwargs):
        super(MovimientoForm, self).__init__(*args, **kwargs)
        # Populate choices
        self.idLaboratorio.choices = [(lab.idLaboratorio, lab.nombre) for lab in Laboratorio.query.all()]
        self.idProducto.choices = [(p.idProducto, p.nombre) for p in Producto.query.all()]
        self.laboratorioDestino.choices = [(lab.idLaboratorio, lab.nombre) for lab in Laboratorio.query.all()]
        
        # Populate provider choices - Opción vacía al inicio y "Nuevo proveedor..." al final
        proveedores = Proveedor.query.order_by(Proveedor.nombre).all()
        self.idProveedor.choices = [('', 'Seleccione un proveedor')] + [(p.idProveedor, f"{p.nombre} ({p.cuit})") for p in proveedores] + [(0, '➕ Nuevo proveedor...')]
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
            
        if self.tipoMovimiento.data == 'compra':
            if not self.tipoDocumento.data:
                self.tipoDocumento.errors.append('Debe seleccionar el tipo de documento para una compra')
                return False
            if not self.numeroDocumento.data:
                self.numeroDocumento.errors.append('Debe ingresar el número de documento para una compra')
                return False
                
        return True


class MovimientoTecnicoForm(FlaskForm):
    tipoMovimiento = SelectField('Tipo de Movimiento', choices=[
        ('ingreso', 'Ingreso'), 
        ('compra', 'Compra'), 
        ('uso', 'Uso'),
        ('transferencia', 'Transferencia')
    ])
    cantidad = FloatField('Cantidad', validators=[DataRequired()])
    unidadMedida = SelectField('Unidad de Medida', choices=[
        ('Lt', 'Litros (Lt)'),
        ('Kg', 'Kilogramos (Kg)')
    ], validators=[DataRequired()])
    idProducto = SelectField('Producto', validators=[DataRequired()], coerce=str)
    
    # Campos para movimientos tipo 'compra'    tipoDocumento = SelectField('Tipo de Documento', choices=[
    tipoDocumento = SelectField('Tipo de Documento', choices=[    
        ('factura', 'Factura'),
        ('remito', 'Remito')
    ], validators=[Optional()])
    numeroDocumento = StringField('Número de Documento', validators=[Optional(), Length(max=50)])
    fechaFactura = StringField('Fecha de Factura', validators=[Optional()])
    idProveedor = SelectField('Proveedor', validators=[Optional()], coerce=int)
    documento = FileField('Documento (PDF)', validators=[Optional()])
    
    # Campo para movimientos tipo 'transferencia'
    laboratorioDestino = SelectField('Laboratorio Destino', validators=[Optional()], coerce=str)
    
    def __init__(self, *args, **kwargs):
        self.laboratorios = kwargs.pop('laboratorios', [])
        super(MovimientoTecnicoForm, self).__init__(*args, **kwargs)
        
        # Populate product choices with all products
        productos = Producto.query.all()
        if productos:
            self.idProducto.choices = [(p.idProducto, p.nombre) for p in productos]
        else:
            self.idProducto.choices = [('', 'No hay productos disponibles')]
            
        # Populate laboratory destination choices
        if self.laboratorios:
            self.laboratorioDestino.choices = [(lab.idLaboratorio, lab.nombre) for lab in self.laboratorios]
        else:
            self.laboratorioDestino.choices = [('', 'No hay laboratorios disponibles')]
            
        # Populate provider choices
        proveedores = Proveedor.query.order_by(Proveedor.nombre).all()
        self.idProveedor.choices = [(0, 'Nuevo proveedor...')] + [(p.idProveedor, f"{p.nombre} ({p.cuit})") for p in proveedores]
    def validate(self, **kwargs):
        if not super().validate(**kwargs):
            return False
            
        if self.tipoMovimiento.data == 'compra':
            if not self.tipoDocumento.data:
                self.tipoDocumento.errors.append('Debe seleccionar el tipo de documento para una compra')
                return False
            if not self.numeroDocumento.data:
                self.numeroDocumento.errors.append('Debe ingresar el número de documento para una compra')
                return False
                
        return True
