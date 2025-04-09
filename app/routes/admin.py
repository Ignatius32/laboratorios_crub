from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from app.models.models import db, Usuario, Laboratorio, Producto, Movimiento, Proveedor
from werkzeug.security import generate_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, BooleanField, FloatField, SelectMultipleField, FileField, SubmitField
from wtforms.validators import DataRequired, Email, Length, ValidationError, URL, Optional, Regexp
from app.integrations.google_drive import drive_integration
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
    password = PasswordField('Contraseña', validators=[Optional(), Length(min=6)])
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
    tipoMovimiento = SelectField('Tipo de Movimiento', choices=[('ingreso', 'Ingreso'), ('egreso', 'Egreso')])
    cantidad = FloatField('Cantidad', validators=[DataRequired()])
    unidadMedida = StringField('Unidad de Medida', validators=[DataRequired(), Length(max=10)])
    idProducto = SelectField('Producto', validators=[DataRequired()], coerce=str)
    idLaboratorio = SelectField('Laboratorio', validators=[DataRequired()], coerce=str)
    
    def __init__(self, *args, **kwargs):
        super(MovimientoForm, self).__init__(*args, **kwargs)
        # Populate choices
        self.idLaboratorio.choices = [(lab.idLaboratorio, lab.nombre) for lab in Laboratorio.query.all()]
        # Populate product choices with all products
        self.idProducto.choices = [(p.idProducto, p.nombre) for p in Producto.query.all()]

class ExcelUploadForm(FlaskForm):
    archivo = FileField('Archivo Excel', validators=[DataRequired()])

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
        
        # Set password
        if form.password.data:
            usuario.set_password(form.password.data)
        else:
            usuario.set_password('password123')  # Default password
        
        # Assign labs
        selected_labs = form.labs_asignados.data
        for lab_id in selected_labs:
            lab = Laboratorio.query.get(lab_id)
            if lab:
                usuario.laboratorios.append(lab)
        
        db.session.add(usuario)
        db.session.commit()
        flash('Usuario creado correctamente', 'success')
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
    productos = Producto.query.all()
    return render_template('admin/productos/list.html', title='Gestión de Productos', productos=productos)

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
        
        # Para movimientos de tipo egreso, verificar stock disponible en el laboratorio
        if form.tipoMovimiento.data == 'egreso':
            producto = Producto.query.get_or_404(form.idProducto.data)
            laboratorio = Laboratorio.query.get_or_404(form.idLaboratorio.data)
            
            # Obtener el stock actual del producto en ese laboratorio
            stock_actual = laboratorio.get_stock_producto(form.idProducto.data)
            
            if form.cantidad.data > stock_actual:
                flash(f'Stock insuficiente. Stock actual en este laboratorio: {stock_actual}', 'danger')
                return render_template('admin/movimientos/form.html', title='Nuevo Movimiento', form=form)
        
        movimiento = Movimiento(
            idMovimiento=movement_id,
            tipoMovimiento=form.tipoMovimiento.data,
            cantidad=form.cantidad.data,
            unidadMedida=form.unidadMedida.data,
            idProducto=form.idProducto.data,
            idLaboratorio=form.idLaboratorio.data
        )
        
        db.session.add(movimiento)
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