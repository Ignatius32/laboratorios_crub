from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app.models.models import db, Laboratorio, Producto, Movimiento, Proveedor
from app import csrf
from app.forms import (MovimientoTecnicoForm, ProductoTecnicoForm,
                       ProveedorTecnicoForm)
import base64
import functools
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
from app.integrations.google_drive import drive_integration
from app.utils.logging_decorators import (
    log_business_operation, 
    audit_user_action,
    monitor_performance,
    log_data_modification
)
from app.utils.stock_service import (
    get_stock_for_product_in_lab,
    get_stock_by_lab_map,
    consulta_productos_con_stock,
)

tecnicos = Blueprint('tecnicos', __name__)

def tecnico_required(f):
    """Exige ser técnico, o administrador.

    Antes exigía `rol == 'tecnico'` a secas, así que un administrador no podía
    abrir ninguna pantalla de esta sección: no había forma de mirar el día a día
    de un laboratorio desde la cuenta que administra el sistema. Quien administra
    todo también puede ver.
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol not in ('tecnico', 'admin'):
            flash('Acceso denegado: Se requiere ser técnico para acceder a esta página', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def lab_access_required(f):
    """Exige que el laboratorio exista y que la persona lo tenga asignado.

    El administrador entra a cualquiera: no se le asignan laboratorios, los
    administra todos.
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        lab_id = kwargs.get('lab_id')
        if not lab_id:
            abort(404)

        if current_user.rol == 'admin':
            Laboratorio.query.get_or_404(lab_id)
            return f(*args, **kwargs)

        user_labs = [lab.idLaboratorio for lab in current_user.laboratorios]
        if lab_id not in user_labs:
            flash('No tienes acceso a este laboratorio', 'danger')
            return redirect(url_for('tecnicos.dashboard'))

        return f(*args, **kwargs)
    return decorated_function



# Dashboard for technicians
@tecnicos.route('/')
@login_required
@tecnico_required
def dashboard():
    # Al administrador no se le asignan laboratorios: los ve todos.
    if current_user.rol == 'admin':
        laboratorios = Laboratorio.query.order_by(Laboratorio.nombre).all()
    else:
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

    # El filtro "tiene stock acá" lo resuelve la base. Antes se traía
    # Producto.query.all(), se calculaba el saldo del catálogo entero en memoria
    # y se descartaba casi todo: el costo crecía con el catálogo y no con lo que
    # el panel muestra.
    consulta, stock = consulta_productos_con_stock(lab_id)
    productos_con_stock = [
        {'producto': fila.Producto, 'stock': fila.stock}
        for fila in consulta.filter(stock > 0)
    ]

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

    # Obtener los filtros de los parámetros de consulta
    tipo_producto = request.args.get('tipoProducto', None)
    search_term = request.args.get('search', None)

    # Parámetros de paginación
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Filtro para mostrar solo productos con stock
    solo_con_stock = request.args.get('con_stock', False, type=lambda v: v.lower() == 'true')

    # Definir los tipos de productos para el menú desplegable
    tipos_productos = [
        ('botiquin', 'Botiquín'),
        ('droguero', 'Droguero'),
        ('vidrio', 'Materiales de vidrio'),
        ('seguridad', 'Elementos de seguridad'),
        ('residuos', 'Residuos peligrosos')
    ]

    # Un solo camino para los dos casos. Antes había dos ramas: sin filtro de
    # stock se paginaba en SQL, y con filtro se traía todo el catálogo, se
    # calculaba el saldo en Python, se descartaba y se cortaba una página a mano
    # con la ManualPagination de app/utils. Ahora el saldo es una columna, así
    # que "con stock" es un WHERE más y la paginación es siempre la de la base.
    consulta, stock = consulta_productos_con_stock(lab_id)

    if tipo_producto:
        consulta = consulta.filter(Producto.tipoProducto == tipo_producto)

    if search_term:
        consulta = consulta.filter(Producto.nombre.ilike(f'%{search_term}%'))

    if solo_con_stock:
        consulta = consulta.filter(stock > 0)

    productos_paginados = consulta.paginate(page=page, per_page=per_page, error_out=False)
    productos_con_stock = [
        {'producto': fila.Producto, 'stock': fila.stock}
        for fila in productos_paginados.items
    ]

    return render_template('tecnicos/productos/list.html',
                          title=f'Productos - {laboratorio.nombre}',
                          laboratorio=laboratorio,
                          productos_con_stock=productos_con_stock,
                          tipos_productos=tipos_productos,
                          selected_tipo=tipo_producto,
                          search_term=search_term,
                          pagination=productos_paginados,
                          total_productos=productos_paginados.total)

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
          # Manejar la subida de la ficha de seguridad
        ficha_seguridad_id = None
        if form.fichaSeguridad.data:
            try:
                # Verificar configuración de Google Drive
                if not drive_integration.script_url:
                    flash('Error de configuración: URL de Google Script no configurada', 'danger')
                    return render_template('tecnicos/productos/form.html', 
                                          title='Nuevo Producto', 
                                          form=form,
                                          laboratorio=laboratorio)
                
                # Leer el archivo y convertirlo a base64
                file_data = form.fichaSeguridad.data.read()
                if len(file_data) == 0:
                    flash('Error: El archivo está vacío', 'warning')
                    return render_template('tecnicos/productos/form.html', 
                                          title='Nuevo Producto', 
                                          form=form,
                                          laboratorio=laboratorio)
                
                file_b64 = base64.b64encode(file_data).decode('utf-8')
                
                # Obtener la extensión del archivo
                filename = secure_filename(form.fichaSeguridad.data.filename)
                if not filename:
                    flash('Error: Nombre de archivo no válido', 'warning')
                    return render_template('tecnicos/productos/form.html', 
                                          title='Nuevo Producto', 
                                          form=form,
                                          laboratorio=laboratorio)
                
                file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                if not file_extension:
                    flash('Error: No se pudo determinar la extensión del archivo', 'warning')
                    return render_template('tecnicos/productos/form.html', 
                                          title='Nuevo Producto', 
                                          form=form,
                                          laboratorio=laboratorio)
                  # Subir el archivo a Google Drive
                result = drive_integration.upload_ficha_seguridad(
                    form.idProducto.data,
                    file_b64,
                    file_extension
                )
                
                if result and 'file_id' in result:
                    ficha_seguridad_id = result['file_id']
                    flash('Ficha de seguridad subida correctamente', 'success')
                elif result and 'error' in result:
                    flash(f'Error al subir la ficha de seguridad: {result["error"]}', 'warning')
                    # Continuar creando el producto sin la ficha
                else:
                    flash('Error desconocido al subir la ficha de seguridad', 'warning')
                    # Continuar creando el producto sin la ficha
                    
            except Exception as e:
                flash(f'Error al procesar la ficha de seguridad: {str(e)}', 'warning')
                # Continuar creando el producto sin la ficha
        
        producto = Producto(
            idProducto=form.idProducto.data,
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            tipoProducto=form.tipoProducto.data,
            unidadMedida=form.unidadMedida.data,
            controlSedronar=form.controlSedronar.data,
            urlFichaSeguridad=ficha_seguridad_id,  # Guardar el ID del archivo en lugar de URL
            stockMinimo=form.stockMinimo.data or 0,
            marca=form.marca.data
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
            unidadMedida=producto.unidadMedida,
            idProducto=form.idProducto.data,
            idLaboratorio=lab_id,
            created_by=current_user.idUsuario if current_user.is_authenticated else None
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
    
    # Parámetros de paginación
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Mismo motivo que en admin.list_movimientos: la plantilla lee el nombre
    # del producto y el del proveedor en cada fila, y sin joinedload eso son
    # dos SELECT por movimiento.
    query = (Movimiento.query
             .filter_by(idLaboratorio=lab_id)
             .options(joinedload(Movimiento.producto),
                      joinedload(Movimiento.proveedor))
             .order_by(Movimiento.timestamp.desc()))
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    total_movimientos = pagination.total
    movimientos = pagination.items

    # El laboratorio destino de una transferencia se guarda como texto, sin
    # clave foránea, así que hay que resolver el nombre acá. La plantilla lo
    # buscaba recorriendo current_user.laboratorios: al administrador, que no
    # tiene laboratorios asignados, le quedaba el destino en blanco.
    nombres_laboratorios = {
        lab.idLaboratorio: lab.nombre for lab in Laboratorio.query.all()
    }

    return render_template('tecnicos/movimientos/list.html',
                           title=f'Movimientos - {laboratorio.nombre}',
                           laboratorio=laboratorio,
                           movimientos=movimientos,
                           pagination=pagination,
                           nombres_laboratorios=nombres_laboratorios,
                           total_movimientos=total_movimientos)

@tecnicos.route('/panel/<string:lab_id>/movimientos/new', methods=['GET', 'POST'])
@login_required
@tecnico_required
@lab_access_required
@log_business_operation("crear movimiento en laboratorio")
@audit_user_action("movement_creation")
@monitor_performance(threshold_ms=3000)
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
        if not producto.unidadMedida:
            flash('El producto no tiene unidad de medida. Pida a un administrador que la cargue (Lt o Kg) antes de registrar movimientos.', 'danger')
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
                # El 0 es la opción "Nuevo proveedor…" del desplegable, que
                # normalmente intercepta proveedores-modal.js para crearlo sin
                # salir de esta pantalla (POST a tecnicos.api_nuevo_proveedor).
                # Llegar acá significa que el JavaScript no corrió; antes se
                # redirigía a tecnicos.new_proveedor, que se eliminó porque su
                # plantilla no existía y respondía 500.
                flash('Para dar de alta un proveedor use la opción "Nuevo '
                      'proveedor…" del desplegable, que abre el formulario en '
                      'esta misma pantalla.', 'warning')
                return render_template('tecnicos/movimientos/form.html',
                                     title='Nuevo Movimiento',
                                     form=form,
                                     laboratorio=laboratorio)
            
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
                flash(f'No hay suficiente stock disponible en este laboratorio. Stock actual: {stock_actual} {producto.unidadMedida}', 'danger')
                return render_template('tecnicos/movimientos/form.html',
                                     title='Nuevo Movimiento',
                                     form=form,
                                     laboratorio=laboratorio)        # Create the movement record
        movimiento = Movimiento(
            idMovimiento=movement_id,
            tipoMovimiento=tipo_movimiento,
            cantidad=form.cantidad.data,
            unidadMedida=producto.unidadMedida,
            idProducto=form.idProducto.data,
            idLaboratorio=lab_id,
            tipoDocumento=tipo_documento,
            urlDocumento=url_documento,
            laboratorioDestino=lab_destino,
            fechaFactura=fecha_factura if tipo_movimiento == 'compra' else None,
            idProveedor=form.idProveedor.data if tipo_movimiento == 'compra' and form.idProveedor.data != 0 else None,
            numeroDocumento=form.numeroDocumento.data if tipo_movimiento == 'compra' else None,
            created_by=current_user.idUsuario if current_user.is_authenticated else None
        )
        db.session.add(movimiento)
        
        # If it's a transfer, create an ingress movement for the destination laboratory
        if tipo_movimiento == 'transferencia' and lab_destino:
            movement_id_dest = 'MOV' + ''.join(random.choices(string.digits, k=6))
            
            movimiento_dest = Movimiento(
                idMovimiento=movement_id_dest,
                tipoMovimiento='ingreso',
                cantidad=form.cantidad.data,
                unidadMedida=producto.unidadMedida,
                idProducto=form.idProducto.data,
                idLaboratorio=lab_destino,
                # We include a reference to the original movement
                tipoDocumento='transferencia',
                laboratorioDestino=lab_id,  # Original lab becomes "source" in this context
                created_by=current_user.idUsuario if current_user.is_authenticated else None
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
    stock_en_lab = get_stock_for_product_in_lab(id, lab_id)
    
    # Obtener los movimientos de este producto en este laboratorio
    movimientos = Movimiento.query.filter_by(
        idProducto=id,
        idLaboratorio=lab_id
    ).order_by(Movimiento.timestamp.desc()).all()
    
    return render_template('tecnicos/productos/view.html',
                          title=f'Detalle de Producto - {producto.nombre}',
                          laboratorio=laboratorio,
                          producto=producto,
                          stock_en_lab=stock_en_lab,
                          movimientos=movimientos)

# Stock visualization for technicians
#
# Las dos pantallas de stock —la global y la local— eran dos funciones de 85 y
# 64 líneas que compartían casi todo: los mismos filtros, el mismo armado de
# diccionarios, la misma paginación a mano. La única diferencia real es contra
# qué saldo se filtra y ordena (el de todos los laboratorios o el de este) y si
# se muestra además el desglose por laboratorio. Eso es un parámetro, no una
# copia del archivo.
def _vista_stock(lab_id, es_global):
    laboratorio = Laboratorio.query.get_or_404(lab_id)

    # Parámetros de paginación
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Parámetros de filtro
    search_query = request.args.get('search', '')
    tipo_filtro = request.args.get('tipo', '')
    stock_filtro = request.args.get('stock', 'all')

    # El saldo que manda: en la vista global, el de todos los laboratorios; en
    # la local, sólo el de este. Es también la columna sobre la que filtra el
    # selector "con stock / sin stock".
    consulta, stock = consulta_productos_con_stock(None if es_global else lab_id)

    if tipo_filtro:
        consulta = consulta.filter(Producto.tipoProducto == tipo_filtro)

    if search_query:
        consulta = consulta.filter(Producto.nombre.ilike(f'%{search_query}%'))

    if stock_filtro == 'inStock':
        consulta = consulta.filter(stock > 0)
    elif stock_filtro == 'outOfStock':
        consulta = consulta.filter(stock <= 0)

    paginado = consulta.paginate(page=page, per_page=per_page, error_out=False)

    # El desglose por laboratorio sólo lo necesita la vista global, y sólo de
    # los productos de esta página: antes se pedía para el catálogo entero.
    reparto_por_producto = {}
    laboratorios = []
    if es_global:
        ids_pagina = [fila.Producto.idProducto for fila in paginado.items]
        if ids_pagina:
            reparto_por_producto = get_stock_by_lab_map(ids_pagina)
        laboratorios = Laboratorio.query.all()

    productos = []
    for fila in paginado.items:
        producto = fila.Producto
        datos = {
            'id': producto.idProducto,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'tipo': producto.tipoProducto,
            'control_sedronar': producto.controlSedronar,
        }

        if es_global:
            reparto = reparto_por_producto.get(producto.idProducto, {})
            # Se recorre la lista de laboratorios y no las claves del reparto
            # para que el orden sea el mismo en todas las filas.
            datos.update(
                stock_global=fila.stock,
                stock_local=reparto.get(lab_id, 0),
                laboratorios_con_stock=[
                    {'nombre': lab.nombre, 'id': lab.idLaboratorio,
                     'stock': reparto[lab.idLaboratorio]}
                    for lab in laboratorios
                    if reparto.get(lab.idLaboratorio, 0) > 0
                ],
            )
        else:
            datos['stock'] = fila.stock

        productos.append(datos)

    return render_template('tecnicos/stock/visualizar.html',
                          title='Stock Global' if es_global
                                else f'Stock - {laboratorio.nombre}',
                          laboratorio=laboratorio,
                          productos=productos,
                          pagination=paginado,
                          total_productos=paginado.total,
                          es_global=es_global)


# Stock visualization for technicians - GLOBAL STOCK
@tecnicos.route('/panel/<string:lab_id>/stock/global')
@login_required
@tecnico_required
@lab_access_required
def visualizar_stock_global(lab_id):
    return _vista_stock(lab_id, es_global=True)

# Stock visualization for technicians - LOCAL STOCK
@tecnicos.route('/panel/<string:lab_id>/stock/local')
@login_required
@tecnico_required
@lab_access_required
def visualizar_stock(lab_id):
    return _vista_stock(lab_id, es_global=False)

# Proveedores management for technicians
@tecnicos.route('/proveedores')
@login_required
@tecnico_required
def list_proveedores():
    # Parámetros de paginación
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Crear la query base ordenada por nombre
    query = Proveedor.query.order_by(Proveedor.nombre)
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    total_proveedores = pagination.total
    proveedores = pagination.items
    
    return render_template('tecnicos/proveedores/list.html', 
                          title='Lista de Proveedores',
                          proveedores=proveedores,
                          pagination=pagination,
                          total_proveedores=total_proveedores)

# API endpoint to create a new provider (for modal)
@tecnicos.route('/api/nuevo_proveedor', methods=['POST'])
@csrf.exempt  # Exempt this route from CSRF protection as we handle it manually
@login_required
@tecnico_required
@log_business_operation("crear proveedor via API")
@audit_user_action("api_supplier_creation")
def api_nuevo_proveedor():
    # Access form data
    nombre = request.form.get('nombre')
    cuit = request.form.get('cuit')
    direccion = request.form.get('direccion', '')
    telefono = request.form.get('telefono', '')
    email = request.form.get('email', '')
    
    # Validar datos
    if not nombre or not cuit:
        return jsonify(success=False, error="Nombre y CUIT son obligatorios")
    
    # Limpiar CUIT (remover guiones) antes de verificar duplicados
    cleaned_cuit = ''.join(filter(str.isdigit, cuit))
    
    # Verificar si ya existe el proveedor
    if Proveedor.query.filter_by(cuit=cleaned_cuit).first():
        return jsonify(success=False, error="Ya existe un proveedor con ese CUIT")
    
    try:
        proveedor = Proveedor(
            nombre=nombre,
            direccion=direccion,
            telefono=telefono,
            email=email,
            cuit=cleaned_cuit
        )
        
        db.session.add(proveedor)
        db.session.commit()
        
        return jsonify(
            success=True, 
            idProveedor=proveedor.idProveedor, 
            nombre=proveedor.nombre, 
            cuit=proveedor.cuit
        )
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error=f"Error al guardar: {str(e)}")