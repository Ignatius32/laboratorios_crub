"""Formulario de proveedores, compartido por el panel y los laboratorios."""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp, ValidationError

from app.models.models import Proveedor


class ProveedorForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    direccion = StringField('Dirección', validators=[Optional(), Length(max=200)])
    telefono = StringField('Teléfono', validators=[Optional(), Length(max=50)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    cuit = StringField('CUIT', validators=[
        DataRequired(), 
        Length(min=11, max=13),
        Regexp(r'^\d{2}-?\d{8}-?\d{1}$', message='Formato de CUIT inválido. Use XX-XXXXXXXX-X o XXXXXXXXXXX.')
    ])
    submit = SubmitField('Guardar')

    def __init__(self, *args, **kwargs):
        # obj se MIRA pero no se saca: WTForms lo necesita para rellenar los
        # campos. Antes acá había un kwargs.pop('obj'), así que el formulario de
        # edición llegaba a la plantilla en blanco —nombre, CUIT, correo y
        # teléfono vacíos— y como nombre y CUIT son obligatorios, guardar sin
        # recargarlos a mano fallaba la validación: editar un proveedor desde el
        # panel estaba roto.
        self.proveedor = kwargs.get('obj')
        super(ProveedorForm, self).__init__(*args, **kwargs)

    def validate_cuit(self, cuit):
        # Limpiar CUIT (remover guiones) antes de verificar unicidad
        cleaned_cuit = ''.join(filter(str.isdigit, cuit.data))
        
        # Buscar un proveedor con el mismo CUIT
        proveedor = Proveedor.query.filter_by(cuit=cleaned_cuit).first()
        
        # Si estamos editando, excluir el proveedor actual de la validación de unicidad
        if proveedor and self.proveedor and proveedor.idProveedor != self.proveedor.idProveedor:
            raise ValidationError('Este CUIT ya está registrado para otro proveedor.')
        elif proveedor and not self.proveedor:
            raise ValidationError('Este CUIT ya está registrado.')


# Los técnicos usan exactamente el mismo formulario. Existía una copia,
# ProveedorTecnicoForm, con los mismos campos y una validación de CUIT que sólo
# se diferenciaba en no contemplar la edición; como ProveedorForm sin `obj` se
# comporta igual que aquella (rechaza cualquier CUIT repetido, con el mismo
# mensaje), la copia no aportaba nada. Se deja el nombre como alias para no
# tocar los sitios de uso.
ProveedorTecnicoForm = ProveedorForm

