from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models.models import db, Usuario, Laboratorio, Producto, Movimiento, Proveedor
from flask_wtf import FlaskForm
from wtforms import SelectField, FloatField, StringField, TextAreaField, BooleanField, FileField, SubmitField
from wtforms.validators import DataRequired, Length, URL, Optional, Email, Regexp, ValidationError

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
class ProveedorTecnicoForm(FlaskForm):
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
    
    def validate_cuit(self, cuit):
        # Limpiar CUIT (remover guiones) antes de verificar unicidad
        cleaned_cuit = ''.join(filter(str.isdigit, cuit.data))
        
        # Verificar si el CUIT ya existe
        proveedor = Proveedor.query.filter_by(cuit=cleaned_cuit).first()
        if proveedor:
            raise ValidationError('Este CUIT ya está registrado.')

class MovimientoTecnicoForm(FlaskForm):
    tipoMovimiento = SelectField('Tipo de Movimiento', choices=[
        ('ingreso', 'Ingreso'), 
        ('compra', 'Compra'), 
        ('uso', 'Uso'),
        ('transferencia', 'Transferencia')
    ])
    cantidad = FloatField('Cantidad', validators=[DataRequired()])
    unidadMedida = StringField('Unidad de Medida', validators=[DataRequired(), Length(max=10)])
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

class ProductoTecnicoForm(FlaskForm):
    idProducto = StringField('ID Producto', validators=[DataRequired(), Length(min=4, max=10)])
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    descripcion = TextAreaField('Descripción', validators=[Optional()])
    tipoProducto = SelectField('Tipo de Producto', 
                              choices=[('botiquin', 'Botiquín'), 
                                      ('vidrio', 'Materiales de vidrio'), 
                                      ('seguridad', 'Elementos de seguridad'),
                                      ('residuos', 'Residuos peligrosos')])
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
    
    # En lugar de filtrar por laboratorio, obtenemos todos los productos
    # y calculamos su stock en este laboratorio específico
    productos = Producto.query.all()
    
    # Para cada producto, calcular su stock en este laboratorio específico
    productos_con_stock = []
    for producto in productos:
        stock_en_lab = producto.stock_en_laboratorio(lab_id)
        # Solo mostramos productos que tienen stock en este laboratorio
        if stock_en_lab > 0:
            productos_con_stock.append({
                'producto': producto,
                'stock': stock_en_lab
            })
    
    return render_template('tecnicos/panel_laboratorio.html',
                           title=f'Panel - {laboratorio.nombre}',
                           laboratorio=laboratorio,
                           productos_con_stock=productos_con_stock)

# Product management for technicians
@tecnicos.route('/panel/<string:lab_id>/productos')
@login_required
@tecnico_required
@lab_access_required
def list_productos(lab_id):
    laboratorio = Laboratorio.query.get_or_404(lab_id)
    
    # Obtenemos todos los productos
    productos = Producto.query.all()
    
    # Para cada producto, calculamos su stock en este laboratorio específico
    productos_con_stock = []
    for producto in productos:
        stock_en_lab = producto.stock_en_laboratorio(lab_id)
        productos_con_stock.append({
            'producto': producto,
            'stock': stock_en_lab
        })
    
    return render_template('tecnicos/productos/list.html',
                          title=f'Productos - {laboratorio.nombre}',
                          laboratorio=laboratorio,
                          productos_con_stock=productos_con_stock)

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
        
        # Verificar que no se está intentando crear un producto tipo droguero
        if form.tipoProducto.data == 'droguero':
            flash('Los técnicos no están autorizados para crear productos de tipo Droguero', 'danger')
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
            urlFichaSeguridad=form.urlFichaSeguridad.data
        )
        
        db.session.add(producto)
        db.session.commit()
        
        # Crear un movimiento de ingreso inicial para este laboratorio
        import random
        import string
        movement_id = 'MOV' + ''.join(random.choices(string.digits, k=6))
        
        movimiento = Movimiento(
            idMovimiento=movement_id,
            tipoMovimiento='ingreso',
            cantidad=0,  # Stock inicial 0
            unidadMedida='unidades',  # Unidad por defecto
            idProducto=form.idProducto.data,
            idLaboratorio=lab_id
        )
        
        db.session.add(movimiento)
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
    # Redirigir a la vista de detalle del producto, ya que los técnicos no pueden editar productos
    flash('Solo los administradores pueden editar productos', 'warning')
    return redirect(url_for('tecnicos.view_producto', lab_id=lab_id, id=id))

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
    
    # Get all laboratories except the current one for transfers
    all_laboratorios = Laboratorio.query.filter(Laboratorio.idLaboratorio != lab_id).all()
    # Initialize form with all available laboratories
    form = MovimientoTecnicoForm(laboratorios=all_laboratorios)
    
    # Obtener todos los proveedores y agregarlos al formulario
    proveedores = Proveedor.query.order_by(Proveedor.nombre).all()
    form.idProveedor.choices = [(0, 'Nuevo proveedor...')] + [(p.idProveedor, f"{p.nombre} ({p.cuit})") for p in proveedores]
    
    # Pre-select product if provided in query param
    if request.args.get('producto'):
        form.idProducto.data = request.args.get('producto')
    
    if form.validate_on_submit():
        # Generate a unique movement ID
        import random
        import string
        movement_id = 'MOV' + ''.join(random.choices(string.digits, k=6))
        
        # Verificar que el producto existe
        producto = Producto.query.get(form.idProducto.data)
        if not producto:
            flash('El producto seleccionado no existe', 'danger')
            return redirect(url_for('tecnicos.new_movimiento', lab_id=lab_id))
        
        # Variables for movement
        tipo_movimiento = form.tipoMovimiento.data
        url_documento = None
        lab_destino = None
        tipo_documento = None
          # Process based on movement type        if tipo_movimiento == 'compra':
            # For purchase movements, handle document upload
        if tipo_movimiento == 'compra':
            tipo_documento = form.tipoDocumento.data
            
            # Process fecha_factura (converting string to date if provided)
            fecha_factura = None
            if form.fechaFactura.data:
                from datetime import datetime
                try:
                    fecha_factura = datetime.strptime(form.fechaFactura.data, '%Y-%m-%d').date()
                except ValueError:
                    flash('El formato de la fecha de factura no es válido. Utilice el formato YYYY-MM-DD.', 'warning')
            
            # Check if a provider was selected or if we need to create a new one
            id_proveedor = form.idProveedor.data
            if id_proveedor == 0:
                # Redirect to new provider form with return URL
                return redirect(url_for('tecnicos.new_proveedor', 
                    return_to=url_for('tecnicos.new_movimiento', lab_id=lab_id)))
            
            # Check if document was uploaded
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
                        lab_id=lab_id,
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
            # For transfer movements, set destination laboratory
            lab_destino = form.laboratorioDestino.data
            if not lab_destino:
                flash('Debe seleccionar un laboratorio destino para la transferencia', 'danger')
                return render_template('tecnicos/movimientos/form.html',
                                     title='Nuevo Movimiento',
                                     form=form,
                                     laboratorio=laboratorio)
        
        # For all egress-like movements (uso, transferencia), check stock
        if tipo_movimiento in ['uso', 'transferencia']:
            # Calcular stock actual en este laboratorio
            stock_actual = laboratorio.get_stock_producto(form.idProducto.data)
            
            if form.cantidad.data > stock_actual:
                flash(f'No hay suficiente stock disponible en este laboratorio. Stock actual: {stock_actual} {form.unidadMedida.data}', 'danger')
                return render_template('tecnicos/movimientos/form.html',
                                     title='Nuevo Movimiento',
                                     form=form,
                                     laboratorio=laboratorio)        # Create the movement record
        movimiento = Movimiento(
            idMovimiento=movement_id,
            tipoMovimiento=tipo_movimiento,
            cantidad=form.cantidad.data,
            unidadMedida=form.unidadMedida.data,
            idProducto=form.idProducto.data,
            idLaboratorio=lab_id,
            tipoDocumento=tipo_documento,
            urlDocumento=url_documento,
            laboratorioDestino=lab_destino,
            fechaFactura=fecha_factura if tipo_movimiento == 'compra' else None,
            idProveedor=form.idProveedor.data if tipo_movimiento == 'compra' and form.idProveedor.data != 0 else None,            numeroDocumento=form.numeroDocumento.data if tipo_movimiento == 'compra' else None
        )
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
                laboratorioDestino=lab_id  # Original lab becomes "source" in this context
            )
            db.session.add(movimiento_dest)
        
        # Commit para guardar los movimientos
        db.session.commit()
        
        # Actualizar stock
        from app.utils.stock_service import actualizar_stock_por_movimiento
        actualizar_stock_por_movimiento(movimiento)
        
        # Para transferencias, actualizar el stock en el destino con el movimiento creado
        if tipo_movimiento == 'transferencia' and lab_destino and 'movimiento_dest' in locals():
            actualizar_stock_por_movimiento(movimiento_dest)
        
        # Guardar los cambios en el stock
        db.session.commit()
        
        flash('Movimiento registrado correctamente', 'success')
        return redirect(url_for('tecnicos.list_movimientos', lab_id=lab_id))
    
    return render_template('tecnicos/movimientos/form.html',
                           title='Nuevo Movimiento',
                           form=form,
                           laboratorio=laboratorio)

# View product details for technicians
@tecnicos.route('/panel/<string:lab_id>/productos/view/<string:id>')
@login_required
@tecnico_required
@lab_access_required
def view_producto(lab_id, id):
    laboratorio = Laboratorio.query.get_or_404(lab_id)
    producto = Producto.query.get_or_404(id)
    stock_en_lab = producto.stock_en_laboratorio(lab_id)
    return render_template('tecnicos/productos/view.html',
                          title=f'Detalle de Producto - {producto.nombre}',
                          laboratorio=laboratorio,
                          producto=producto,
                          stock_en_lab=stock_en_lab)

# Stock visualization for technicians - GLOBAL STOCK
@tecnicos.route('/panel/<string:lab_id>/stock/global')
@login_required
@tecnico_required
@lab_access_required
def visualizar_stock_global(lab_id):
    laboratorio = Laboratorio.query.get_or_404(lab_id)
    
    # Get all laboratories
    todos_laboratorios = Laboratorio.query.all()
    
    # Obtener todos los productos con su stock global
    productos = Producto.query.all()
    productos_info = []
    for producto in productos:
        # Para cada producto, calculamos su stock global y el stock en este laboratorio
        stock_global = producto.stock_total  # Accedido como propiedad, sin paréntesis
        stock_en_lab = producto.stock_en_laboratorio(lab_id)
        
        # Obtener laboratorios donde hay stock de este producto
        laboratorios_con_stock = []
        for lab in todos_laboratorios:
            stock_en_este_lab = producto.stock_en_laboratorio(lab.idLaboratorio)
            if stock_en_este_lab > 0:
                laboratorios_con_stock.append({
                    'nombre': lab.nombre,
                    'id': lab.idLaboratorio,
                    'stock': stock_en_este_lab
                })
        
        productos_info.append({
            'id': producto.idProducto,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'tipo': producto.tipoProducto,
            'estado_fisico': producto.estadoFisico,
            'stock_global': stock_global,
            'stock_local': stock_en_lab,
            'control_sedronar': producto.controlSedronar,
            'laboratorios_con_stock': laboratorios_con_stock
        })
    
    return render_template('tecnicos/stock/visualizar.html',
                          title='Stock Global',
                          laboratorio=laboratorio,
                          productos=productos_info,
                          es_global=True)

# Stock visualization for technicians - LOCAL STOCK
@tecnicos.route('/panel/<string:lab_id>/stock/local')
@login_required
@tecnico_required
@lab_access_required
def visualizar_stock(lab_id):
    laboratorio = Laboratorio.query.get_or_404(lab_id)
    
    # Obtener todos los productos
    productos = Producto.query.all()
    productos_info = []
    
    for producto in productos:
        stock_en_lab = producto.stock_en_laboratorio(lab_id)
        productos_info.append({
            'id': producto.idProducto,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'tipo': producto.tipoProducto,
            'estado_fisico': producto.estadoFisico,
            'stock': stock_en_lab,
            'control_sedronar': producto.controlSedronar
        })
    
    return render_template('tecnicos/stock/visualizar.html',
                          title=f'Stock - {laboratorio.nombre}',
                          laboratorio=laboratorio,
                          productos=productos_info,
                          es_global=False)

# Proveedores management for technicians
@tecnicos.route('/proveedores')
@login_required
@tecnico_required
def list_proveedores():
    proveedores = Proveedor.query.order_by(Proveedor.nombre).all()
    return render_template('tecnicos/proveedores/list.html', 
                          title='Lista de Proveedores',
                          proveedores=proveedores)

@tecnicos.route('/proveedores/new', methods=['GET', 'POST'])
@login_required
@tecnico_required
def new_proveedor():
    form = ProveedorTecnicoForm()
    return_to = request.args.get('return_to')
    
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
        
        # Si hay una URL de retorno, redirigir a ella
        if return_to:
            return redirect(return_to)
        return redirect(url_for('tecnicos.list_proveedores'))
    
    return render_template('tecnicos/proveedores/form.html', 
                          title='Nuevo Proveedor', 
                          form=form)

@tecnicos.route('/proveedores/<int:id>')
@login_required
@tecnico_required
def view_proveedor(id):
    proveedor = Proveedor.query.get_or_404(id)
    
    # Buscar movimientos asociados a este proveedor
    movimientos = Movimiento.query.filter_by(cuitProveedor=proveedor.cuit).all()
    
    return render_template('tecnicos/proveedores/view.html',
                          title=f'Proveedor: {proveedor.nombre}',
                          proveedor=proveedor,
                          movimientos=movimientos)