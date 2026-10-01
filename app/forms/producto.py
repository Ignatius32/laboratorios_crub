"""Formularios de productos."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import BooleanField, FileField, FloatField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, URL

from app.models.models import UNIDADES

# Con una primera opción vacía: sin ella el desplegable arranca en Lt y un
# producto que va en Kg queda mal cargado sin que nadie haya elegido nada.
OPCIONES_UNIDAD = [('', 'Seleccione…')] + [(u, u) for u in UNIDADES]


# Estos dos NO se unifican, y la diferencia es deliberada: las opciones de
# tipoProducto del formulario de técnicos no incluyen 'droguero'. Fusionarlos
# habilitaría a cualquier laboratorista a dar de alta productos de droguero,
# que es justamente lo que la separación impide. Las otras diferencias
# (urlFichaSeguridad sólo en el panel, FileAllowed sólo en el de técnicos)
# también son de alcance, no descuidos.

class ProductoForm(FlaskForm):
    idProducto = StringField('ID Producto', validators=[DataRequired(), Length(min=4, max=10)])
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    descripcion = TextAreaField('Descripción', validators=[Optional()])
    tipoProducto = SelectField('Tipo de Producto', 
                              choices=[('botiquin', 'Botiquín'), 
                                      ('droguero', 'Droguero'), 
                                      ('vidrio', 'Materiales de vidrio'), 
                                      ('seguridad', 'Elementos de seguridad'),
                                      ('residuos', 'Residuos peligrosos')])
    unidadMedida = SelectField('Unidad de Medida', choices=OPCIONES_UNIDAD,
                               validators=[DataRequired('Elija la unidad de medida del producto.')])
    stockMinimo = FloatField('Stock Mínimo', validators=[Optional()])
    marca = StringField('Marca', validators=[Optional(), Length(max=100)])
    controlSedronar = BooleanField('Control Sedronar')
    urlFichaSeguridad = StringField('URL Ficha de Seguridad', validators=[Optional(), URL(), Length(max=200)])
    fichaSeguridad = FileField('Ficha de Seguridad (Archivo)', validators=[Optional()])


class ProductoTecnicoForm(FlaskForm):
    idProducto = StringField('ID Producto', validators=[DataRequired(), Length(min=4, max=10)])
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    descripcion = TextAreaField('Descripción', validators=[Optional()])
    tipoProducto = SelectField('Tipo de Producto', 
                              choices=[('botiquin', 'Botiquín'), 
                                      ('vidrio', 'Materiales de vidrio'), 
                                      ('seguridad', 'Elementos de seguridad'),
                                      ('residuos', 'Residuos peligrosos')])
    unidadMedida = SelectField('Unidad de Medida', choices=OPCIONES_UNIDAD,
                               validators=[DataRequired('Elija la unidad de medida del producto.')])
    controlSedronar = BooleanField('Control Sedronar')
    fichaSeguridad = FileField('Ficha de Seguridad', 
                              validators=[Optional(), 
                                        FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 
                                                  'Solo se permiten archivos PDF e imágenes (JPG, PNG)')])
    stockMinimo = FloatField('Stock Mínimo', validators=[Optional()])
    marca = StringField('Marca', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Guardar')
