from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models.models import db, Usuario, Laboratorio, Producto, Movimiento
from flask_wtf import FlaskForm
from wtforms import SelectField, FloatField, StringField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Length, URL, Optional

tecnicos = Blueprint('tecnicos', __name__)

# Ensure the user is a technician
def tecnico_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'tecnico':
            flash('Acceso denegado: Se requiere ser técnico para acceder a esta página', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Ensure the technician has access to the specified laboratory
def lab_access_required(f):
    def decorated_function(*args, **kwargs):
        lab_id = kwargs.get('lab_id')
        if not lab_id:
            abort(404)
        
        # Check if user has access to this lab
        user_labs = [lab.idLaboratorio for lab in current_user.laboratorios]
        if lab_id not in user_labs:
            flash('No tienes acceso a este laboratorio', 'danger')
            return redirect(url_for('tecnicos.dashboard'))
        
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Forms
class MovimientoTecnicoForm(FlaskForm):
    tipoMovimiento = SelectField('Tipo de Movimiento', choices=[('ingreso', 'Ingreso'), ('egreso', 'Egreso')])
    cantidad = FloatField('Cantidad', validators=[DataRequired()])
    unidadMedida = StringField('Unidad de Medida', validators=[DataRequired(), Length(max=10)])
    idProducto = SelectField('Producto', validators=[DataRequired()], coerce=str)
    
    def __init__(self, lab_id, *args, **kwargs):
        super(MovimientoTecnicoForm, self).__init__(*args, **kwargs)
        # Populate product choices for the given laboratory
        productos = Producto.query.filter_by(idLaboratorio=lab_id).all()
        self.idProducto.choices = [(p.idProducto, p.nombre) for p in productos]

class ProductoTecnicoForm(FlaskForm):
    idProducto = StringField('ID Producto', validators=[DataRequired(), Length(min=4, max=10)])
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    descripcion = TextAreaField('Descripción', validators=[Optional()])
    tipoProducto = StringField('Tipo de Producto', validators=[DataRequired(), Length(max=50)])
    estadoFisico = SelectField('Estado Físico', 
                              choices=[('solido', 'Sólido'), ('liquido', 'Líquido'), ('gaseoso', 'Gaseoso')])
    controlSedronar = BooleanField('Control Sedronar')
    urlFichaSeguridad = StringField('URL Ficha de Seguridad', validators=[Optional(), URL(), Length(max=200)])


# Dashboard for technicians
@tecnicos.route('/')
@login_required
@tecnico_required
def dashboard():
    laboratorios = current_user.laboratorios
    return render_template('tecnicos/dashboard.html', 
                           title='Panel de Técnico',
                           laboratorios=laboratorios)

# Laboratory view for technicians
@tecnicos.route('/panel/<string:lab_id>')
@login_required
@tecnico_required
@lab_access_required
def panel_laboratorio(lab_id):
    laboratorio = Laboratorio.query.get_or_404(lab_id)
    productos = Producto.query.filter_by(idLaboratorio=lab_id).all()
    return render_template('tecnicos/panel_laboratorio.html',
                           title=f'Panel - {laboratorio.nombre}',
                           laboratorio=laboratorio,
                           productos=productos)

# Product management for technicians
@tecnicos.route('/panel/<string:lab_id>/productos')
@login_required
@tecnico_required
@lab_access_required
def list_productos(lab_id):
    laboratorio = Laboratorio.query.get_or_404(lab_id)
    productos = Producto.query.filter_by(idLaboratorio=lab_id).all()
    return render_template('tecnicos/productos/list.html',
                           title=f'Productos - {laboratorio.nombre}',
                           laboratorio=laboratorio,
                           productos=productos)

@tecnicos.route('/panel/<string:lab_id>/productos/new', methods=['GET', 'POST'])
@login_required
@tecnico_required
@lab_access_required
def new_producto(lab_id):
    laboratorio = Laboratorio.query.get_or_404(lab_id)
    form = ProductoTecnicoForm()
    
    if form.validate_on_submit():
        # Check if product ID already exists
        if Producto.query.filter_by(idProducto=form.idProducto.data).first():
            flash('El ID de producto ya existe', 'danger')
            return render_template('tecnicos/productos/form.html', 
                                  title='Nuevo Producto', 
                                  form=form,
                                  laboratorio=laboratorio)
        
        producto = Producto(
            idProducto=form.idProducto.data,
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            tipoProducto=form.tipoProducto.data,
            estadoFisico=form.estadoFisico.data,
            controlSedronar=form.controlSedronar.data,
            urlFichaSeguridad=form.urlFichaSeguridad.data,
            idLaboratorio=lab_id
        )
        
        db.session.add(producto)
        db.session.commit()
        flash('Producto creado correctamente', 'success')
        return redirect(url_for('tecnicos.list_productos', lab_id=lab_id))
    
    return render_template('tecnicos/productos/form.html',
                           title='Nuevo Producto',
                           form=form,
                           laboratorio=laboratorio)

@tecnicos.route('/panel/<string:lab_id>/productos/edit/<string:id>', methods=['GET', 'POST'])
@login_required
@tecnico_required
@lab_access_required
def edit_producto(lab_id, id):
    laboratorio = Laboratorio.query.get_or_404(lab_id)
    producto = Producto.query.get_or_404(id)
    
    # Ensure the product belongs to the lab
    if producto.idLaboratorio != lab_id:
        flash('Este producto no pertenece a este laboratorio', 'danger')
        return redirect(url_for('tecnicos.list_productos', lab_id=lab_id))
    
    form = ProductoTecnicoForm(obj=producto)
    
    if form.validate_on_submit():
        producto.nombre = form.nombre.data
        producto.descripcion = form.descripcion.data
        producto.tipoProducto = form.tipoProducto.data
        producto.estadoFisico = form.estadoFisico.data
        producto.controlSedronar = form.controlSedronar.data
        producto.urlFichaSeguridad = form.urlFichaSeguridad.data
        
        db.session.commit()
        flash('Producto actualizado correctamente', 'success')
        return redirect(url_for('tecnicos.list_productos', lab_id=lab_id))
    
    return render_template('tecnicos/productos/form.html',
                           title='Editar Producto',
                           form=form,
                           producto=producto,
                           laboratorio=laboratorio)

# Movement management for technicians
@tecnicos.route('/panel/<string:lab_id>/movimientos')
@login_required
@tecnico_required
@lab_access_required
def list_movimientos(lab_id):
    laboratorio = Laboratorio.query.get_or_404(lab_id)
    movimientos = Movimiento.query.filter_by(idLaboratorio=lab_id).all()
    return render_template('tecnicos/movimientos/list.html',
                           title=f'Movimientos - {laboratorio.nombre}',
                           laboratorio=laboratorio,
                           movimientos=movimientos)

@tecnicos.route('/panel/<string:lab_id>/movimientos/new', methods=['GET', 'POST'])
@login_required
@tecnico_required
@lab_access_required
def new_movimiento(lab_id):
    laboratorio = Laboratorio.query.get_or_404(lab_id)
    form = MovimientoTecnicoForm(lab_id)
    
    if form.validate_on_submit():
        # Generate a unique movement ID
        import random
        import string
        movement_id = 'MOV' + ''.join(random.choices(string.digits, k=6))
        
        # Verify the product belongs to this laboratory
        producto = Producto.query.get(form.idProducto.data)
        if not producto or producto.idLaboratorio != lab_id:
            flash('El producto seleccionado no pertenece a este laboratorio', 'danger')
            return redirect(url_for('tecnicos.new_movimiento', lab_id=lab_id))
        
        # For outgoing movements, check if there is enough stock
        if form.tipoMovimiento.data == 'egreso':
            # Calculate current stock
            ingresos = sum(m.cantidad for m in Movimiento.query.filter_by(
                idProducto=form.idProducto.data, 
                tipoMovimiento='ingreso'
            ).all())
            
            egresos = sum(m.cantidad for m in Movimiento.query.filter_by(
                idProducto=form.idProducto.data, 
                tipoMovimiento='egreso'
            ).all())
            
            stock_actual = ingresos - egresos
            
            if form.cantidad.data > stock_actual:
                flash(f'No hay suficiente stock disponible. Stock actual: {stock_actual} {producto.unidadMedida}', 'danger')
                return render_template('tecnicos/movimientos/form.html',
                                      title='Nuevo Movimiento',
                                      form=form,
                                      laboratorio=laboratorio)
        
        movimiento = Movimiento(
            idMovimiento=movement_id,
            tipoMovimiento=form.tipoMovimiento.data,
            cantidad=form.cantidad.data,
            unidadMedida=form.unidadMedida.data,
            idProducto=form.idProducto.data,
            idLaboratorio=lab_id
        )
        
        db.session.add(movimiento)
        db.session.commit()
        flash('Movimiento registrado correctamente', 'success')
        return redirect(url_for('tecnicos.list_movimientos', lab_id=lab_id))
    
    return render_template('tecnicos/movimientos/form.html',
                           title='Nuevo Movimiento',
                           form=form,
                           laboratorio=laboratorio)

# View product details
@tecnicos.route('/panel/<string:lab_id>/productos/<string:id>')
@login_required
@tecnico_required
@lab_access_required
def view_producto(lab_id, id):
    laboratorio = Laboratorio.query.get_or_404(lab_id)
    producto = Producto.query.get_or_404(id)
    
    # Ensure the product belongs to the lab
    if producto.idLaboratorio != lab_id:
        flash('Este producto no pertenece a este laboratorio', 'danger')
        return redirect(url_for('tecnicos.list_productos', lab_id=lab_id))
    
    # Get all movements for this product
    movimientos = Movimiento.query.filter_by(idProducto=id).order_by(Movimiento.timestamp.desc()).all()
    
    return render_template('tecnicos/productos/view.html',
                           title=f'Producto: {producto.nombre}',
                           producto=producto,
                           laboratorio=laboratorio,
                           movimientos=movimientos)