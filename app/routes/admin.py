from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app, session
from flask_login import login_required, current_user
from app.models.models import db, Usuario, Laboratorio, Producto, Movimiento, Proveedor
from werkzeug.security import generate_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, BooleanField, FloatField, SelectMultipleField, FileField, SubmitField
from wtforms.validators import DataRequired, Email, Length, ValidationError, URL, Optional, Regexp
from app.integrations.google_drive import drive_integration
from app.utils.email_service import EmailService
import pandas as pd
import io

admin = Blueprint('admin', __name__)

# Authorization decorator
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'admin':
            flash('Acceso denegado: Se requiere privilegios de administrador', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Forms
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
        self.proveedor = kwargs.pop('obj', None)
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

class UsuarioForm(FlaskForm):
    idUsuario = StringField('ID Usuario', validators=[DataRequired(), Length(min=4, max=10)])
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    apellido = StringField('Apellido', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    telefono = StringField('Teléfono', validators=[Optional(), Length(max=20)])
    password = PasswordField('Contraseña (Solo para administradores)', validators=[Optional(), Length(min=6)])
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
    estadoFisico = SelectField('Estado Físico', 
                              choices=[('solido', 'Sólido'), ('liquido', 'Líquido'), ('gaseoso', 'Gaseoso')])
    controlSedronar = BooleanField('Control Sedronar')
    urlFichaSeguridad = StringField('URL Ficha de Seguridad', validators=[Optional(), URL(), Length(max=200)])

class MovimientoForm(FlaskForm):
    tipoMovimiento = SelectField('Tipo de Movimiento', choices=[
        ('ingreso', 'Ingreso'), 
        ('compra', 'Compra'), 
        ('uso', 'Uso'),
        ('transferencia', 'Transferencia')
    ])
    cantidad = FloatField('Cantidad', validators=[DataRequired()])
    unidadMedida = StringField('Unidad de Medida', validators=[DataRequired(), Length(max=10)])
    idProducto = SelectField('Producto', validators=[DataRequired()], coerce=str)
    idLaboratorio = SelectField('Laboratorio', validators=[DataRequired()], coerce=str)
    
    # Campos para movimientos tipo 'compra'
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
        super(MovimientoForm, self).__init__(*args, **kwargs)
        # Populate choices
        self.idLaboratorio.choices = [(lab.idLaboratorio, lab.nombre) for lab in Laboratorio.query.all()]
        self.idProducto.choices = [(p.idProducto, p.nombre) for p in Producto.query.all()]
        self.laboratorioDestino.choices = [(lab.idLaboratorio, lab.nombre) for lab in Laboratorio.query.all()]
        
        # Populate provider choices
        proveedores = Proveedor.query.order_by(Proveedor.nombre).all()
        self.idProveedor.choices = [(0, 'Nuevo proveedor...')] + [(p.idProveedor, f"{p.nombre} ({p.cuit})") for p in proveedores]
    
    def validate(self):
        if not super().validate():
            return False
            
        if self.tipoMovimiento.data == 'compra':
            if not self.tipoDocumento.data:
                self.tipoDocumento.errors.append('Debe seleccionar el tipo de documento para una compra')
                return False
            if not self.numeroDocumento.data:
                self.numeroDocumento.errors.append('Debe ingresar el número de documento para una compra')
                return False
                
        return True

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
    
    def __init__(self, *args, **kwargs):
        super(ReporteForm, self).__init__(*args, **kwargs)
        # Populate lab choices
        laboratorios = Laboratorio.query.all()
        self.laboratorio.choices = [('', 'Todos')] + [(lab.idLaboratorio, lab.nombre) for lab in laboratorios]

# Dashboard
@admin.route('/')
@admin_required
def dashboard():
    usuarios_count = Usuario.query.count()
    laboratorios_count = Laboratorio.query.count()
    productos_count = Producto.query.count()
    movimientos_count = Movimiento.query.count()
    
    return render_template('admin/dashboard.html', 
                           title='Panel de Administración',
                           usuarios_count=usuarios_count,
                           laboratorios_count=laboratorios_count,
                           productos_count=productos_count,
                           movimientos_count=movimientos_count)

# CRUD for Usuarios
@admin.route('/usuarios')
@admin_required
def list_usuarios():
    usuarios = Usuario.query.all()
    return render_template('admin/usuarios/list.html', title='Gestión de Usuarios', usuarios=usuarios)

@admin.route('/usuarios/new', methods=['GET', 'POST'])
@admin_required
def new_usuario():
    form = UsuarioForm()
    
    if form.validate_on_submit():
        # Check if user ID or email already exists
        if Usuario.query.filter_by(idUsuario=form.idUsuario.data).first():
            flash('El ID de usuario ya existe', 'danger')
            return render_template('admin/usuarios/form.html', title='Nuevo Usuario', form=form)
        
        if Usuario.query.filter_by(email=form.email.data).first():
            flash('El email ya está registrado', 'danger')
            return render_template('admin/usuarios/form.html', title='Nuevo Usuario', form=form)
        usuario = Usuario(
            idUsuario=form.idUsuario.data,
            nombre=form.nombre.data,
            apellido=form.apellido.data,
            email=form.email.data,
            telefono=form.telefono.data,
            rol=form.rol.data
        )
        
        # Set default password initially
        if form.rol.data == 'admin' and form.password.data:
            # For admin users, use provided password if available
            usuario.set_password(form.password.data)
        else:
            # Set a temporary password for technicians or if no password provided for admin
            usuario.set_password('password123')  # Default password
        
        # Assign labs
        selected_labs = form.labs_asignados.data
        for lab_id in selected_labs:
            lab = Laboratorio.query.get(lab_id)
            if lab:
                usuario.laboratorios.append(lab)
        
        # Save the user to get an ID
        db.session.add(usuario)
        db.session.commit()
        
        # If it's a technician, generate a reset token and send an email
        if usuario.rol == 'tecnico':
            try:
                # Generate reset token
                token = usuario.generate_reset_token()
                db.session.commit()
                
                # Send email with password setup link
                email_sent = EmailService.send_password_reset_email(usuario, token, is_new_user=True)
                
                if email_sent:
                    flash(f'Usuario creado correctamente. Se ha enviado un email a {usuario.email} para establecer la contraseña.', 'success')
                else:
                    flash('Usuario creado correctamente, pero hubo un problema al enviar el email. El usuario puede restablecer su contraseña desde la página de inicio de sesión.', 'warning')
                    current_app.logger.error(f"Failed to send password setup email to {usuario.email}")
            except Exception as e:
                current_app.logger.error(f"Error sending password setup email: {str(e)}")
                flash('Usuario creado correctamente, pero hubo un problema al enviar el email de configuración.', 'warning')
        else:
            flash('Usuario administrador creado correctamente', 'success')
        return redirect(url_for('admin.list_usuarios'))
    
    return render_template('admin/usuarios/form.html', title='Nuevo Usuario', form=form)

@admin.route('/usuarios/edit/<string:id>', methods=['GET', 'POST'])
@admin_required
def edit_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    form = UsuarioForm(obj=usuario)
    
    # Pre-select the user's laboratories
    if request.method == 'GET':
        form.labs_asignados.data = [lab.idLaboratorio for lab in usuario.laboratorios]
    
    if form.validate_on_submit():
        # Check if email already exists (for different user)
        existing_user = Usuario.query.filter_by(email=form.email.data).first()
        if existing_user and existing_user.idUsuario != usuario.idUsuario:
            flash('El email ya está registrado', 'danger')
            return render_template('admin/usuarios/form.html', title='Editar Usuario', form=form)
        
        usuario.nombre = form.nombre.data
        usuario.apellido = form.apellido.data
        usuario.email = form.email.data
        usuario.telefono = form.telefono.data
        usuario.rol = form.rol.data
        
        # Update password if provided
        if form.password.data:
            usuario.set_password(form.password.data)
        
        # Update laboratory assignments
        usuario.laboratorios = []  # Clear existing assignments
        selected_labs = form.labs_asignados.data
        for lab_id in selected_labs:
            lab = Laboratorio.query.get(lab_id)
            if lab:
                usuario.laboratorios.append(lab)
        
        db.session.commit()
        flash('Usuario actualizado correctamente', 'success')
        return redirect(url_for('admin.list_usuarios'))
    
    return render_template('admin/usuarios/form.html', title='Editar Usuario', form=form, usuario=usuario)

@admin.route('/usuarios/delete/<string:id>', methods=['POST'])
@admin_required
def delete_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    
    # Don't allow deletion of current user
    if usuario.idUsuario == current_user.idUsuario:
        flash('No puedes eliminar tu propio usuario', 'danger')
        return redirect(url_for('admin.list_usuarios'))
    
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuario eliminado correctamente', 'success')
    return redirect(url_for('admin.list_usuarios'))

# CRUD for Laboratorios
@admin.route('/laboratorios')
@admin_required
def list_laboratorios():
    laboratorios = Laboratorio.query.all()
    return render_template('admin/laboratorios/list.html', title='Gestión de Laboratorios', laboratorios=laboratorios)

@admin.route('/laboratorios/new', methods=['GET', 'POST'])
@admin_required
def new_laboratorio():
    form = LaboratorioForm()
    
    if form.validate_on_submit():
        # Check if lab ID already exists
        if Laboratorio.query.filter_by(idLaboratorio=form.idLaboratorio.data).first():
            flash('El ID de laboratorio ya existe', 'danger')
            return render_template('admin/laboratorios/form.html', title='Nuevo Laboratorio', form=form)
        
        laboratorio = Laboratorio(
            idLaboratorio=form.idLaboratorio.data,
            nombre=form.nombre.data,
            direccion=form.direccion.data,
            telefono=form.telefono.data,
            email=form.email.data
        )
        
        # Save the laboratory first to get an ID
        db.session.add(laboratorio)
        db.session.commit()
        
        # Create Google Drive folders
        try:
            folder_ids = drive_integration.create_laboratory_folders(
                laboratorio.idLaboratorio, 
                laboratorio.nombre
            )
            
            if folder_ids:
                # Update the laboratory with folder IDs
                laboratorio.laboratorio_folder_id = folder_ids.get('lab_folder_id')
                laboratorio.movimiento_folder_id = folder_ids.get('movimientos_folder_id')
                db.session.commit()
                flash('Laboratorio creado correctamente con integración a Google Drive', 'success')
            else:
                flash('Laboratorio creado correctamente, pero no se pudieron crear las carpetas en Google Drive', 'warning')
        except Exception as e:
            current_app.logger.error(f"Error creating Drive folders: {str(e)}")
            flash('Laboratorio creado correctamente, pero hubo un error en la integración con Google Drive', 'warning')
        
        return redirect(url_for('admin.list_laboratorios'))
    
    return render_template('admin/laboratorios/form.html', title='Nuevo Laboratorio', form=form)

@admin.route('/laboratorios/edit/<string:id>', methods=['GET', 'POST'])
@admin_required
def edit_laboratorio(id):
    laboratorio = Laboratorio.query.get_or_404(id)
    form = LaboratorioForm(obj=laboratorio)
    
    # Exclude idLaboratorio from validation when editing
    if request.method == 'GET':
        # No need to set form.idLaboratorio.data as it's already set by obj=laboratorio
        pass
    
    if form.validate_on_submit():
        # Update only editable fields, not the ID
        laboratorio.nombre = form.nombre.data
        laboratorio.direccion = form.direccion.data
        laboratorio.telefono = form.telefono.data
        laboratorio.email = form.email.data
        
        db.session.commit()
        flash('Laboratorio actualizado correctamente', 'success')
        return redirect(url_for('admin.list_laboratorios'))
    
    return render_template('admin/laboratorios/form.html', title='Editar Laboratorio', form=form, laboratorio=laboratorio)

@admin.route('/laboratorios/delete/<string:id>', methods=['POST'])
@admin_required
def delete_laboratorio(id):
    laboratorio = Laboratorio.query.get_or_404(id)
    
    # Check if lab has products or movements
    if laboratorio.productos or laboratorio.movimientos:
        flash('No se puede eliminar el laboratorio porque tiene productos o movimientos asociados', 'danger')
        return redirect(url_for('admin.list_laboratorios'))
    
    # Store folder IDs before deleting the laboratory
    folder_ids = {
        'lab_folder_id': laboratorio.laboratorio_folder_id,
        'movimientos_folder_id': laboratorio.movimiento_folder_id
    }
    
    # Delete the laboratory from database
    db.session.delete(laboratorio)
    db.session.commit()
    
    # Delete the folders from Google Drive if they exist
    if folder_ids['lab_folder_id'] or folder_ids['movimientos_folder_id']:
        try:
            success = drive_integration.delete_laboratory_folders(folder_ids)
            if success:
                flash('Laboratorio y sus carpetas en Google Drive eliminados correctamente', 'success')
            else:
                flash('Laboratorio eliminado, pero hubo un problema al eliminar las carpetas de Google Drive', 'warning')
        except Exception as e:
            current_app.logger.error(f"Error deleting Drive folders: {str(e)}")
            flash('Laboratorio eliminado, pero hubo un error en la eliminación de carpetas de Google Drive', 'warning')
    else:
        flash('Laboratorio eliminado correctamente', 'success')
        
    return redirect(url_for('admin.list_laboratorios'))

# CRUD for Productos
@admin.route('/productos')
@admin_required
def list_productos():
    # Obtener los filtros de los parámetros de consulta
    lab_id = request.args.get('laboratorio', None)
    tipo_producto = request.args.get('tipoProducto', None)
    
    # Obtener todos los laboratorios para el menú desplegable
    laboratorios = Laboratorio.query.all()
    
    # Definir los tipos de productos para el menú desplegable
    tipos_productos = [
        ('botiquin', 'Botiquín'),
        ('droguero', 'Droguero'),
        ('vidrio', 'Materiales de vidrio'),
        ('seguridad', 'Elementos de seguridad'),
        ('residuos', 'Residuos peligrosos')
    ]
    
    # Obtener todos los productos
    # Aplicar filtro por tipo de producto si se especifica
    if tipo_producto:
        productos = Producto.query.filter_by(tipoProducto=tipo_producto).all()
    else:
        productos = Producto.query.all()
    
    # Preparar datos de productos con stock
    productos_con_stock = []
    for producto in productos:
        if lab_id:
            # Si hay un laboratorio seleccionado, mostrar el stock de ese laboratorio
            stock = producto.stock_en_laboratorio(lab_id)
            # Si queremos filtrar y mostrar solo los productos que tienen stock en el laboratorio seleccionado
            # podemos comentar esta línea para excluir los productos con stock cero
            # if stock <= 0:
            #    continue
        else:
            # Si no hay laboratorio seleccionado, mostrar el stock total
            stock = producto.stock_total
                
        productos_con_stock.append({
            'producto': producto,
            'stock_total': stock
        })
    
    return render_template('admin/productos/list.html', 
                         title='Gestión de Productos', 
                         productos_con_stock=productos_con_stock,
                         laboratorios=laboratorios,
                         tipos_productos=tipos_productos,
                         selected_lab=lab_id,
                         selected_tipo=tipo_producto)

@admin.route('/productos/new', methods=['GET', 'POST'])
@admin_required
def new_producto():
    form = ProductoForm()
    
    if form.validate_on_submit():
        # Check if product ID already exists
        if Producto.query.filter_by(idProducto=form.idProducto.data).first():
            flash('El ID de producto ya existe', 'danger')
            return render_template('admin/productos/form.html', title='Nuevo Producto', form=form)
        
        producto = Producto(
            idProducto=form.idProducto.data,
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            tipoProducto=form.tipoProducto.data,
            estadoFisico=form.estadoFisico.data,
            controlSedronar=form.controlSedronar.data,
            urlFichaSeguridad=form.urlFichaSeguridad.data
        )
        
        db.session.add(producto)
        db.session.commit()
        flash('Producto creado correctamente', 'success')
        return redirect(url_for('admin.list_productos'))
    
    return render_template('admin/productos/form.html', title='Nuevo Producto', form=form)

@admin.route('/productos/edit/<string:id>', methods=['GET', 'POST'])
@admin_required
def edit_producto(id):
    producto = Producto.query.get_or_404(id)
    form = ProductoForm(obj=producto)
    
    if form.validate_on_submit():
        producto.nombre = form.nombre.data
        producto.descripcion = form.descripcion.data
        producto.tipoProducto = form.tipoProducto.data
        producto.estadoFisico = form.estadoFisico.data
        producto.controlSedronar = form.controlSedronar.data
        producto.urlFichaSeguridad = form.urlFichaSeguridad.data
        
        db.session.commit()
        flash('Producto actualizado correctamente', 'success')
        return redirect(url_for('admin.list_productos'))
    
    return render_template('admin/productos/form.html', title='Editar Producto', form=form, producto=producto)

@admin.route('/productos/delete/<string:id>', methods=['POST'])
@admin_required
def delete_producto(id):
    producto = Producto.query.get_or_404(id)
    
    # Check if product has movements
    if producto.movimientos:
        flash('No se puede eliminar el producto porque tiene movimientos asociados', 'danger')
        return redirect(url_for('admin.list_productos'))
    
    db.session.delete(producto)
    db.session.commit()
    flash('Producto eliminado correctamente', 'success')
    return redirect(url_for('admin.list_productos'))

@admin.route('/productos/importar', methods=['GET', 'POST'])
@admin_required
def importar_productos():
    form = ExcelUploadForm()
    
    # Eliminar el campo idLaboratorio del formulario ya que los productos ahora son globales
    if hasattr(form, 'idLaboratorio'):
        delattr(form, 'idLaboratorio')
    
    if form.validate_on_submit():
        try:
            # Leer el archivo Excel
            file_content = form.archivo.data.read()
            data_frame = pd.read_excel(io.BytesIO(file_content))
            
            # Validar las columnas del archivo
            required_columns = ['ID Producto', 'Nombre', 'Tipo de Producto', 
                               'Estado Físico', 'URL Ficha de Seguridad', 'Descripción', 'Control Sedronar']
            
            # Verificar si todas las columnas requeridas están presentes
            if not all(col in data_frame.columns for col in required_columns):
                missing_cols = [col for col in required_columns if col not in data_frame.columns]
                flash(f'El archivo no contiene todas las columnas requeridas. Faltan: {", ".join(missing_cols)}', 'danger')
                return redirect(url_for('admin.importar_productos'))
            
            # Mapeo de valores de campos a valores de la BD
            tipo_producto_map = {
                'Botiquín': 'botiquin',
                'Droguero': 'droguero',
                'Materiales de vidrio': 'vidrio',
                'Elementos de seguridad': 'seguridad',
                'Residuos peligrosos': 'residuos'
            }
            
            estado_fisico_map = {
                'Sólido': 'solido',
                'Líquido': 'liquido',
                'Gaseoso': 'gaseoso'
            }
            
            # Contadores para la información de proceso
            productos_creados = 0
            productos_actualizados = 0
            productos_saltados = 0
            errores = []
            
            # Procesar cada fila del Excel
            for index, row in data_frame.iterrows():
                try:
                    id_producto = str(row['ID Producto']).strip()
                    
                    # Mapear tipo de producto
                    tipo_producto_excel = str(row['Tipo de Producto']).strip()
                    tipo_producto = tipo_producto_map.get(tipo_producto_excel, None)
                    if not tipo_producto:
                        if tipo_producto_excel.lower() in tipo_producto_map.values():
                            # Si es una clave válida directamente
                            tipo_producto = tipo_producto_excel.lower()
                        else:
                            errores.append(f"Fila {index+2}: Tipo de producto '{tipo_producto_excel}' no válido.")
                            productos_saltados += 1
                            continue
                    
                    # Mapear estado físico
                    estado_fisico_excel = str(row['Estado Físico']).strip()
                    estado_fisico = estado_fisico_map.get(estado_fisico_excel, None)
                    if not estado_fisico:
                        if estado_fisico_excel.lower() in estado_fisico_map.values():
                            # Si es una clave válida directamente
                            estado_fisico = estado_fisico_excel.lower()
                        else:
                            errores.append(f"Fila {index+2}: Estado físico '{estado_fisico_excel}' no válido.")
                            productos_saltados += 1
                            continue
                    
                    # Manejar Control Sedronar como booleano
                    control_sedronar = False
                    if not pd.isna(row['Control Sedronar']):
                        control_value = str(row['Control Sedronar']).strip().lower()
                        control_sedronar = control_value in ['true', 'verdadero', 'sí', 'si', '1', 'yes', 'y', 'true']
                    
                    # URL de ficha de seguridad (opcional)
                    url_ficha = None
                    if not pd.isna(row['URL Ficha de Seguridad']):
                        url_ficha = str(row['URL Ficha de Seguridad']).strip()
                    
                    # Descripción (opcional)
                    descripcion = None
                    if not pd.isna(row['Descripción']):
                        descripcion = str(row['Descripción']).strip()
                    
                    # Verificar si el producto ya existe
                    producto_existente = Producto.query.filter_by(idProducto=id_producto).first()
                    
                    if producto_existente:
                        # Actualizar producto existente
                        producto_existente.nombre = str(row['Nombre']).strip()
                        producto_existente.descripcion = descripcion
                        producto_existente.tipoProducto = tipo_producto
                        producto_existente.estadoFisico = estado_fisico
                        producto_existente.controlSedronar = control_sedronar
                        producto_existente.urlFichaSeguridad = url_ficha
                        productos_actualizados += 1
                    else:
                        # Crear nuevo producto (ahora son globales, sin asignación a laboratorio)
                        nuevo_producto = Producto(
                            idProducto=id_producto,
                            nombre=str(row['Nombre']).strip(),
                            descripcion=descripcion,
                            tipoProducto=tipo_producto,
                            estadoFisico=estado_fisico,
                            controlSedronar=control_sedronar,
                            urlFichaSeguridad=url_ficha
                        )
                        
                        db.session.add(nuevo_producto)
                        productos_creados += 1
                        
                except Exception as e:
                    errores.append(f"Fila {index+2}: Error procesando producto: {str(e)}")
                    productos_saltados += 1
            
            # Guardar cambios en la base de datos
            db.session.commit()
            
            # Mostrar resumen del proceso
            flash(f'Importación completada: {productos_creados} productos creados, {productos_actualizados} actualizados, {productos_saltados} saltados', 'success')
            
            # Mostrar errores si ocurrieron
            if errores:
                error_message = "<br>".join(errores[:10])
                if len(errores) > 10:
                    error_message += f"<br>... y {len(errores) - 10} errores más."
                flash(f'Se encontraron los siguientes errores:<br>{error_message}', 'warning')
            
            return redirect(url_for('admin.list_productos'))
            
        except Exception as e:
            flash(f'Error al procesar el archivo: {str(e)}', 'danger')
            return redirect(url_for('admin.importar_productos'))
    
    return render_template('admin/productos/importar.html', title='Importar Productos', form=form)

# CRUD for Movimientos
@admin.route('/movimientos')
@admin_required
def list_movimientos():
    movimientos = Movimiento.query.all()
    return render_template('admin/movimientos/list.html', title='Gestión de Movimientos', movimientos=movimientos)

@admin.route('/movimientos/new', methods=['GET', 'POST'])
@admin_required
def new_movimiento():
    form = MovimientoForm()
    
    if form.validate_on_submit():
        # Generate a unique movement ID
        import random
        import string
        movement_id = 'MOV' + ''.join(random.choices(string.digits, k=6))
        
        # Verificar que el producto existe
        producto = Producto.query.get(form.idProducto.data)
        if not producto:
            flash('El producto seleccionado no existe', 'danger')
            return render_template('admin/movimientos/form.html', title='Nuevo Movimiento', form=form)
        
        # Variables for movement
        tipo_movimiento = form.tipoMovimiento.data
        url_documento = None
        lab_destino = None
        tipo_documento = None
        fecha_factura = None
        
        # Process based on movement type
        if tipo_movimiento == 'compra':
            tipo_documento = form.tipoDocumento.data
            
            # Process fecha_factura (converting string to date if provided)
            if form.fechaFactura.data:
                from datetime import datetime
                try:
                    fecha_factura = datetime.strptime(form.fechaFactura.data, '%Y-%m-%d').date()
                except ValueError:
                    flash('El formato de la fecha de factura no es válido. Utilice el formato YYYY-MM-DD.', 'warning')
            
            # Process document upload if provided
            if form.documento.data:
                try:
                    import base64
                    from app.integrations.google_drive import drive_integration
                    
                    # Read file and encode as base64
                    file_data = base64.b64encode(form.documento.data.read()).decode('utf-8')
                    file_name = form.documento.data.filename
                    file_type = "application/pdf"  # Assuming PDFs only
                    
                    # Upload document to Google Drive
                    result = drive_integration.upload_movimiento_documento(
                        lab_id=form.idLaboratorio.data,
                        movimiento_id=movement_id,
                        file_data=file_data,
                        file_name=file_name,
                        file_type=file_type
                    )
                    
                    if result:
                        url_documento = result.get('file_url')
                    else:
                        flash('Error al subir el documento. El movimiento se registrará sin documento adjunto.', 'warning')
                except Exception as e:
                    flash(f'Error al procesar el documento: {str(e)}', 'danger')
        
        elif tipo_movimiento == 'transferencia':
            lab_destino = form.laboratorioDestino.data
            if not lab_destino:
                flash('Debe seleccionar un laboratorio destino para la transferencia', 'danger')
                return render_template('admin/movimientos/form.html', title='Nuevo Movimiento', form=form)
        
        # For all egress-like movements (uso, transferencia), check stock
        if tipo_movimiento in ['uso', 'transferencia']:
            laboratorio = Laboratorio.query.get_or_404(form.idLaboratorio.data)
            stock_actual = laboratorio.get_stock_producto(form.idProducto.data)
            
            if form.cantidad.data > stock_actual:
                flash(f'No hay suficiente stock disponible en este laboratorio. Stock actual: {stock_actual} {form.unidadMedida.data}', 'danger')
                return render_template('admin/movimientos/form.html', title='Nuevo Movimiento', form=form)
        
        # Create the movement record
        movimiento = Movimiento(
            idMovimiento=movement_id,
            tipoMovimiento=tipo_movimiento,
            cantidad=form.cantidad.data,
            unidadMedida=form.unidadMedida.data,
            idProducto=form.idProducto.data,
            idLaboratorio=form.idLaboratorio.data,
            tipoDocumento=tipo_documento,
            numeroDocumento=form.numeroDocumento.data if tipo_movimiento == 'compra' else None,
            urlDocumento=url_documento,
            fechaFactura=fecha_factura,
            idProveedor=form.idProveedor.data if tipo_movimiento == 'compra' and form.idProveedor.data != 0 else None,
            laboratorioDestino=lab_destino        )
        
        db.session.add(movimiento)
        
        # If it's a transfer, create an ingress movement for the destination laboratory
        if tipo_movimiento == 'transferencia' and lab_destino:
            movement_id_dest = 'MOV' + ''.join(random.choices(string.digits, k=6))
            
            movimiento_dest = Movimiento(
                idMovimiento=movement_id_dest,
                tipoMovimiento='ingreso',
                cantidad=form.cantidad.data,
                unidadMedida=form.unidadMedida.data,
                idProducto=form.idProducto.data,
                idLaboratorio=lab_destino,
                # We include a reference to the original movement
                tipoDocumento='transferencia',
                laboratorioDestino=form.idLaboratorio.data  # Original lab becomes "source" in this context
            )
            db.session.add(movimiento_dest)
        
        db.session.commit()
        flash('Movimiento registrado correctamente', 'success')
        return redirect(url_for('admin.list_movimientos'))
    
    return render_template('admin/movimientos/form.html', title='Nuevo Movimiento', form=form)

@admin.route('/api/get_products_by_lab/<string:lab_id>')
@admin_required
def get_products_by_lab(lab_id):
    productos = Producto.query.filter_by(idLaboratorio=lab_id).all()
    return {'products': [{'id': p.idProducto, 'nombre': p.nombre} for p in productos]}

@admin.route('/api/get_products')
@admin_required
def get_products():
    productos = Producto.query.all()
    return {'products': [{'id': p.idProducto, 'nombre': p.nombre} for p in productos]}

@admin.route('/movimientos/delete/<string:id>', methods=['POST'])
@admin_required
def delete_movimiento(id):
    movimiento = Movimiento.query.get_or_404(id)
    db.session.delete(movimiento)
    db.session.commit()
    flash('Movimiento eliminado correctamente', 'success')
    return redirect(url_for('admin.list_movimientos'))

# CRUD for Proveedores
@admin.route('/proveedores')
@admin_required
def list_proveedores():
    proveedores = Proveedor.query.order_by(Proveedor.nombre).all()
    return render_template('admin/proveedores/list.html', 
                           title='Gestión de Proveedores', 
                           proveedores=proveedores)

@admin.route('/proveedores/new', methods=['GET', 'POST'])
@admin_required
def new_proveedor():
    form = ProveedorForm()
    
    if form.validate_on_submit():
        # Limpiar CUIT (remover guiones) antes de guardar
        cleaned_cuit = ''.join(filter(str.isdigit, form.cuit.data))
        
        proveedor = Proveedor(
            nombre=form.nombre.data,
            direccion=form.direccion.data,
            telefono=form.telefono.data,
            email=form.email.data,
            cuit=cleaned_cuit
        )
        
        db.session.add(proveedor)
        db.session.commit()
        flash('Proveedor creado correctamente', 'success')
        return redirect(url_for('admin.list_proveedores'))
    
    return render_template('admin/proveedores/form.html', 
                           title='Nuevo Proveedor', 
                           form=form)

@admin.route('/proveedores/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_proveedor(id):
    proveedor = Proveedor.query.get_or_404(id)
    form = ProveedorForm(obj=proveedor)
    
    # Para la validación de unicidad del CUIT
    form.proveedor = proveedor
    
    if form.validate_on_submit():
        # Limpiar CUIT (remover guiones) antes de guardar
        cleaned_cuit = ''.join(filter(str.isdigit, form.cuit.data))
        
        proveedor.nombre = form.nombre.data
        proveedor.direccion = form.direccion.data
        proveedor.telefono = form.telefono.data
        proveedor.email = form.email.data
        proveedor.cuit = cleaned_cuit
        
        db.session.commit()
        flash('Proveedor actualizado correctamente', 'success')
        return redirect(url_for('admin.list_proveedores'))
    
    return render_template('admin/proveedores/form.html', 
                           title='Editar Proveedor', 
                           form=form, 
                           proveedor=proveedor)

@admin.route('/proveedores/delete/<int:id>', methods=['POST'])
@admin_required
def delete_proveedor(id):
    proveedor = Proveedor.query.get_or_404(id)
    
    # Verificar si hay movimientos asociados al proveedor
    movimientos_asociados = Movimiento.query.filter_by(cuitProveedor=proveedor.cuit).first()
    
    if movimientos_asociados:
        flash('No se puede eliminar el proveedor porque tiene movimientos asociados', 'danger')
        return redirect(url_for('admin.list_proveedores'))
    
    db.session.delete(proveedor)
    db.session.commit()
    flash('Proveedor eliminado correctamente', 'success')
    return redirect(url_for('admin.list_proveedores'))

# Reportes
@admin.route('/reportes/movimientos', methods=['GET', 'POST'])
@admin_required
def reporte_movimientos():
    from datetime import datetime
    from sqlalchemy import and_, or_
    
    form = ReporteForm()
    reporte_data = []
    
    if form.validate_on_submit():
        try:
            # Convertir fechas
            fecha_inicial = datetime.strptime(form.fecha_inicial.data, '%Y-%m-%d')
            fecha_final = datetime.strptime(form.fecha_final.data, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            
            # Filtrar por tipo de producto si se selecciona uno
            productos_query = Producto.query
            if form.tipo_producto.data:
                productos_query = productos_query.filter_by(tipoProducto=form.tipo_producto.data)
            productos = productos_query.all()
            
            # Construir consulta base para movimientos
            movimientos_query = Movimiento.query.filter(
                and_(
                    Movimiento.timestamp >= fecha_inicial,
                    Movimiento.timestamp <= fecha_final
                )
            )
            
            # Filtrar por laboratorio si se selecciona uno
            if form.laboratorio.data:
                movimientos_query = movimientos_query.filter_by(idLaboratorio=form.laboratorio.data)
            
            # Para cada producto, obtener sus movimientos y calcular stocks
            for producto in productos:
                # Obtener el stock inicial (justo antes de fecha_inicial)
                ingresos_antes = db.session.query(db.func.sum(Movimiento.cantidad)).filter(
                    and_(
                        Movimiento.idProducto == producto.idProducto,
                        Movimiento.tipoMovimiento.in_(['ingreso', 'compra']),
                        Movimiento.timestamp < fecha_inicial
                    )
                ).scalar() or 0
                
                egresos_antes = db.session.query(db.func.sum(Movimiento.cantidad)).filter(
                    and_(
                        Movimiento.idProducto == producto.idProducto,
                        Movimiento.tipoMovimiento.in_(['uso', 'transferencia']),
                        Movimiento.timestamp < fecha_inicial
                    )
                ).scalar() or 0
                
                stock_inicial = ingresos_antes - egresos_antes
                
                # Filtrar movimientos de este producto en el período seleccionado
                movimientos_producto = movimientos_query.filter_by(idProducto=producto.idProducto).order_by(Movimiento.timestamp).all()
                
                # Si no hay movimientos para este producto en el período, no lo incluimos en el reporte
                if not movimientos_producto:
                    continue
                
                # Para cada movimiento del producto, calcular stock antes y después
                stock_actual = stock_inicial
                for movimiento in movimientos_producto:
                    # Determinar efecto en stock
                    if movimiento.tipoMovimiento in ['ingreso', 'compra']:
                        stock_despues = stock_actual + movimiento.cantidad
                    else:  # uso o transferencia
                        stock_despues = stock_actual - movimiento.cantidad
                      # Obtener CUIT del proveedor si es un movimiento de compra
                    cuit_proveedor = None
                    if movimiento.tipoMovimiento == 'compra' and movimiento.idProveedor:
                        proveedor = Proveedor.query.get(movimiento.idProveedor)
                        if proveedor:
                            cuit_proveedor = proveedor.cuit
                    
                    # Agregar a los datos del reporte
                    reporte_data.append({
                        'fecha': movimiento.timestamp,
                        'producto_id': producto.idProducto,
                        'producto_nombre': producto.nombre,
                        'stock_inicial_cantidad': stock_actual,
                        'stock_inicial_unidad': movimiento.unidadMedida,
                        'tipo_movimiento': movimiento.tipoMovimiento,
                        'cantidad': movimiento.cantidad,
                        'unidad_medida': movimiento.unidadMedida,
                        'stock_final_cantidad': stock_despues,
                        'stock_final_unidad': movimiento.unidadMedida,
                        'tipo_documento': movimiento.tipoDocumento,
                        'numero_documento': movimiento.numeroDocumento,
                        'cuit_proveedor': cuit_proveedor
                    })
                    
                    # Actualizar stock para el siguiente movimiento
                    stock_actual = stock_despues
            
            # Ordenar por fecha
            reporte_data.sort(key=lambda x: x['fecha'])
            
            # Guardar en sesión para exportar a Excel
            session['reporte_data'] = [
                {k: (v.strftime('%d/%m/%Y %H:%M:%S') if k == 'fecha' else v) 
                 for k, v in item.items()}
                for item in reporte_data
            ]
            
            flash('Reporte generado correctamente', 'success')
            
        except ValueError:
            flash('Error en el formato de fechas. Use el formato YYYY-MM-DD', 'danger')
        except Exception as e:
            flash(f'Error al generar el reporte: {str(e)}', 'danger')
    
    return render_template('admin/reportes/movimientos.html', 
                          title='Reporte de Movimientos',
                          form=form,
                          reporte_data=reporte_data)

@admin.route('/reportes/movimientos/excel')
@admin_required
def exportar_reporte_excel():
    import pandas as pd
    from datetime import datetime
    from io import BytesIO
    from flask import send_file
    
    # Recuperar datos de la sesión
    reporte_data = session.get('reporte_data', [])
    
    if not reporte_data:
        flash('No hay datos para exportar', 'warning')
        return redirect(url_for('admin.reporte_movimientos'))
    
    # Crear DataFrame con pandas
    df = pd.DataFrame(reporte_data)
      # Reordenar columnas según el formato solicitado
    columnas_ordenadas = [
        'fecha',
        'producto_nombre',
        'stock_inicial_cantidad',
        'stock_inicial_unidad',
        'tipo_movimiento',
        'cantidad',
        'unidad_medida',
        'stock_final_cantidad',
        'stock_final_unidad',
        'tipo_documento',
        'numero_documento',
        'cuit_proveedor'
    ]
    
    # Verificar que todas las columnas existan en el DataFrame
    columnas_existentes = [col for col in columnas_ordenadas if col in df.columns]
    df = df[columnas_existentes]
      # Renombrar las columnas para el archivo Excel
    columnas_excel = {
        'fecha': 'Fecha',
        'producto_nombre': 'Producto',
        'stock_inicial_cantidad': 'Stock Inicial - Cantidad',
        'stock_inicial_unidad': 'Stock Inicial - Unidad de medida',
        'tipo_movimiento': 'Movimiento - Tipo',
        'cantidad': 'Movimiento - Cantidad',
        'unidad_medida': 'Movimiento - Unidad de Medida',
        'stock_final_cantidad': 'Stock Final - Cantidad',
        'stock_final_unidad': 'Stock Final - Unidad de medida',
        'tipo_documento': 'Documento para operación - Tipo',
        'numero_documento': 'Documento para operación - Número',
        'cuit_proveedor': 'CUIT Proveedor'
    }
    df = df.rename(columns=columnas_excel)
    
    # Crear un archivo Excel en memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Reporte de Movimientos', index=False)
        
        # Formatear la hoja para que sea más legible
        workbook = writer.book
        worksheet = writer.sheets['Reporte de Movimientos']
        
        # Formato para los encabezados
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Aplicar formato a los encabezados
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            # Ajustar ancho de columna basado en el contenido
            max_len = max(
                df[value].astype(str).map(len).max(),
                len(str(value))
            ) + 2
            worksheet.set_column(col_num, col_num, max_len)
    
    # Preparar el archivo para descarga
    output.seek(0)
    
    # Generar nombre de archivo con fecha y hora
    fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"reporte_movimientos_{fecha_actual}.xlsx"
    
    # Enviar archivo al cliente
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )