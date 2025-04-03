from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models.models import db, Usuario, Laboratorio, Producto, Movimiento
from werkzeug.security import generate_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, BooleanField, FloatField, SelectMultipleField
from wtforms.validators import DataRequired, Email, Length, ValidationError, URL, Optional

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
    tipoProducto = StringField('Tipo de Producto', validators=[DataRequired(), Length(max=50)])
    estadoFisico = SelectField('Estado Físico', 
                              choices=[('solido', 'Sólido'), ('liquido', 'Líquido'), ('gaseoso', 'Gaseoso')])
    controlSedronar = BooleanField('Control Sedronar')
    urlFichaSeguridad = StringField('URL Ficha de Seguridad', validators=[Optional(), URL(), Length(max=200)])
    idLaboratorio = SelectField('Laboratorio', validators=[DataRequired()], coerce=str)
    
    def __init__(self, *args, **kwargs):
        super(ProductoForm, self).__init__(*args, **kwargs)
        # Populate lab choices
        self.idLaboratorio.choices = [(lab.idLaboratorio, lab.nombre) for lab in Laboratorio.query.all()]

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
        # We will update product choices based on selected lab in the frontend

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
        
        db.session.add(laboratorio)
        db.session.commit()
        flash('Laboratorio creado correctamente', 'success')
        return redirect(url_for('admin.list_laboratorios'))
    
    return render_template('admin/laboratorios/form.html', title='Nuevo Laboratorio', form=form)

@admin.route('/laboratorios/edit/<string:id>', methods=['GET', 'POST'])
@admin_required
def edit_laboratorio(id):
    laboratorio = Laboratorio.query.get_or_404(id)
    form = LaboratorioForm(obj=laboratorio)
    
    if form.validate_on_submit():
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
    
    db.session.delete(laboratorio)
    db.session.commit()
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
            urlFichaSeguridad=form.urlFichaSeguridad.data,
            idLaboratorio=form.idLaboratorio.data
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
        producto.idLaboratorio = form.idLaboratorio.data
        
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
    
    # Get products for selected lab (will be handled with JavaScript in frontend)
    if request.method == 'GET':
        lab_id = request.args.get('lab_id', '')
        if lab_id:
            productos = Producto.query.filter_by(idLaboratorio=lab_id).all()
            form.idProducto.choices = [(p.idProducto, p.nombre) for p in productos]
        else:
            form.idProducto.choices = []
    
    if form.validate_on_submit():
        # Generate a unique movement ID
        import random
        import string
        movement_id = 'MOV' + ''.join(random.choices(string.digits, k=6))
        
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

@admin.route('/movimientos/delete/<string:id>', methods=['POST'])
@admin_required
def delete_movimiento(id):
    movimiento = Movimiento.query.get_or_404(id)
    db.session.delete(movimiento)
    db.session.commit()
    flash('Movimiento eliminado correctamente', 'success')
    return redirect(url_for('admin.list_movimientos'))