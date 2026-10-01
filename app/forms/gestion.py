"""Formularios de gestión: usuarios, laboratorios, importación y reportes."""

from flask_wtf import FlaskForm
from wtforms import FileField, SelectField, SelectMultipleField, StringField
from wtforms.validators import DataRequired, Email, Length, Optional

from app.models.models import Laboratorio


class UsuarioForm(FlaskForm):
    """Los datos del usuario que administra esta aplicación.

    No hay campo de contraseña: las administra Keycloak. Nombre, apellido, mail
    y rol se sobrescriben con lo que diga el realm en el próximo ingreso de esa
    persona; lo que de verdad se administra acá son los laboratorios asignados.
    Por eso también sirve para dar de alta a alguien antes de su primer
    ingreso: es la forma de dejarle los laboratorios ya asignados.
    """
    idUsuario = StringField('DNI', validators=[DataRequired(), Length(min=4, max=10)])
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    apellido = StringField('Apellido', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    telefono = StringField('Teléfono', validators=[Optional(), Length(max=20)])
    rol = SelectField('Rol', choices=[('tecnico', 'Técnico'), ('admin', 'Administrador')])
    labs_asignados = SelectMultipleField('Laboratorios Asignados', coerce=str)

    def __init__(self, *args, **kwargs):
        super(UsuarioForm, self).__init__(*args, **kwargs)
        # Populate labs choices
        self.labs_asignados.choices = [(lab.idLaboratorio, lab.nombre) for lab in Laboratorio.query.all()]


class LaboratorioForm(FlaskForm):
    idLaboratorio = StringField('ID Laboratorio', validators=[DataRequired(), Length(min=4, max=10)])
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    direccion = StringField('Dirección', validators=[DataRequired(), Length(max=200)])
    telefono = StringField('Teléfono', validators=[Optional(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])


class ExcelUploadForm(FlaskForm):
    archivo = FileField('Archivo Excel', validators=[DataRequired()])


class ReporteForm(FlaskForm):
    fecha_inicial = StringField('Fecha Inicial', validators=[DataRequired()])
    fecha_final = StringField('Fecha Final', validators=[DataRequired()])
    tipo_producto = SelectField('Tipo de Producto', choices=[
        ('', 'Todos'), 
        ('botiquin', 'Botiquín'), 
        ('droguero', 'Droguero'), 
        ('vidrio', 'Materiales de vidrio'), 
        ('seguridad', 'Elementos de seguridad'),
        ('residuos', 'Residuos peligrosos')
    ], validators=[Optional()])
    laboratorio = SelectField('Laboratorio', validators=[Optional()], coerce=str)
    control_sedronar = SelectField('Control Sedronar', choices=[
        ('', 'Todos los productos'),
        ('true', 'Solo productos Sedronar'),
        ('false', 'Solo productos NO Sedronar')
    ], validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(ReporteForm, self).__init__(*args, **kwargs)
        # Populate lab choices
        laboratorios = Laboratorio.query.all()
        self.laboratorio.choices = [('', 'Todos')] + [(lab.idLaboratorio, lab.nombre) for lab in laboratorios]
