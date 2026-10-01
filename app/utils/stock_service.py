"""
Cálculo de stock.

El stock no se guarda en ninguna parte: se deriva de los movimientos cada vez
que se pide. Un ingreso o una compra suman; un uso, un egreso, una salida o una
transferencia restan. La ventaja es que nunca puede quedar desincronizado del
historial; el costo es una agregación por consulta, que para el volumen de esta
aplicación es irrelevante.

Hay cuatro operaciones, y una sola forma de nombrar cada una:

    get_stock_for_product_in_lab(producto, lab)  -> float
    get_stock_map_for_lab(lab, [productos])      -> {producto: stock}
    get_global_stock_map([productos])            -> {producto: stock}
    get_stock_by_lab_map([productos])            -> {producto: {lab: stock}}

Las cuatro devuelven valores ya calculados, así que sirven cuando ya se sabe de
qué productos se habla —típicamente los de la página que se está mostrando—.
Cuando en cambio hay que filtrar u ordenar POR stock, calcularlo primero obliga
a traer el catálogo entero y recortarlo en Python. Para eso está la quinta:

    consulta_productos_con_stock(lab)            -> (Query de (Producto, stock), stock)

que expone el saldo como una columna de SQL, de modo que el filtro, el orden y
la paginación los resuelve la base.

Antes había doce nombres públicos para estos cuatro comportamientos: los
canónicos, una tanda de alias "de compatibilidad" y otra de alias "real_time",
todos delegando en los mismos cuatro. Cada sitio de llamada usaba el que le
tocó, así que leer el código no dejaba claro si dos llamadas hacían lo mismo.
"""

from sqlalchemy import case, func

from app.models.models import Movimiento, Producto, db

# Los tipos que suman y los que restan. Un tipo desconocido no altera el stock.
# 'egreso' y 'salida' no los emite la aplicación actual, pero quedan por los
# movimientos históricos que ya están cargados con esos nombres.
TIPOS_QUE_SUMAN = ['ingreso', 'compra']
TIPOS_QUE_RESTAN = ['egreso', 'uso', 'salida', 'transferencia']


def _saldo():
    """La expresión SQL que convierte un movimiento en su efecto sobre el stock."""
    return func.coalesce(
        func.sum(
            case(
                (Movimiento.tipoMovimiento.in_(TIPOS_QUE_SUMAN), Movimiento.cantidad),
                (Movimiento.tipoMovimiento.in_(TIPOS_QUE_RESTAN), -Movimiento.cantidad),
                else_=0,
            )
        ),
        0,
    )


def get_stock_for_product_in_lab(product_id, lab_id):
    """El stock de un producto en un laboratorio.

    Returns:
        float: 0.0 si no hay ningún movimiento.
    """
    resultado = db.session.query(_saldo()).filter(
        Movimiento.idProducto == product_id,
        Movimiento.idLaboratorio == lab_id,
    ).scalar()
    return float(resultado or 0)


def get_stock_map_for_lab(lab_id, product_ids=None):
    """El stock de todos los productos de un laboratorio, en una sola consulta.

    Args:
        lab_id: laboratorio a consultar.
        product_ids: si se pasa, limita el cálculo a esos productos.

    Returns:
        dict: {idProducto: stock}. Los productos sin movimientos en ese
        laboratorio no aparecen; quien consulte debe usar .get(id, 0).
    """
    consulta = (db.session.query(Movimiento.idProducto, _saldo().label('stock'))
                .filter(Movimiento.idLaboratorio == lab_id))
    if product_ids:
        consulta = consulta.filter(Movimiento.idProducto.in_(product_ids))
    consulta = consulta.group_by(Movimiento.idProducto)

    return {fila.idProducto: float(fila.stock or 0) for fila in consulta}


def get_global_stock_map(product_ids=None):
    """El stock de cada producto sumando todos los laboratorios.

    Returns:
        dict: {idProducto: stock}. Ver la nota de get_stock_map_for_lab sobre
        los productos ausentes.
    """
    consulta = db.session.query(Movimiento.idProducto, _saldo().label('stock'))
    if product_ids:
        consulta = consulta.filter(Movimiento.idProducto.in_(product_ids))
    consulta = consulta.group_by(Movimiento.idProducto)

    return {fila.idProducto: float(fila.stock or 0) for fila in consulta}


def get_stock_by_lab_map(product_ids=None):
    """La distribución de cada producto entre laboratorios.

    Returns:
        dict: {idProducto: {idLaboratorio: stock}}
    """
    consulta = db.session.query(
        Movimiento.idProducto,
        Movimiento.idLaboratorio,
        _saldo().label('stock'),
    )
    if product_ids:
        consulta = consulta.filter(Movimiento.idProducto.in_(product_ids))
    consulta = consulta.group_by(Movimiento.idProducto, Movimiento.idLaboratorio)

    resultado = {}
    for fila in consulta:
        resultado.setdefault(fila.idProducto, {})[fila.idLaboratorio] = float(fila.stock or 0)
    return resultado


def _subconsulta_saldo(lab_id=None):
    """El saldo por producto como subconsulta, lista para unir contra Producto.

    Con lab_id se restringe a ese laboratorio; sin él suma todos.
    """
    consulta = db.session.query(
        Movimiento.idProducto.label('idProducto'),
        _saldo().label('stock'),
    )
    if lab_id is not None:
        consulta = consulta.filter(Movimiento.idLaboratorio == lab_id)
    return consulta.group_by(Movimiento.idProducto).subquery()


def consulta_productos_con_stock(lab_id=None):
    """Productos junto a su stock, como una sola consulta filtrable y paginable.

    Devuelve la tupla (consulta, stock):

    - `consulta` produce filas (Producto, stock) y admite los .filter(),
      .order_by() y .paginate() de siempre.
    - `stock` es la expresión SQL de la columna, para poder escribir
      `consulta.filter(stock > 0)` u `consulta.order_by(stock.desc())`.

    Es un LEFT JOIN contra el saldo agregado, con COALESCE a 0: los productos
    sin ningún movimiento aparecen con stock 0 en vez de desaparecer.

    Existe porque filtrar por stock era lo único que obligaba a romper la
    paginación: no habiendo forma de expresar "stock > 0" en SQL, las vistas
    traían Producto.query.all(), calculaban el saldo de todo el catálogo en
    memoria, descartaban y recién ahí cortaban una página con slicing. El costo
    crecía con el catálogo entero en lugar de con la página.
    """
    sq = _subconsulta_saldo(lab_id)
    stock = func.coalesce(sq.c.stock, 0.0)
    consulta = (db.session.query(Producto, stock.label('stock'))
                .outerjoin(sq, Producto.idProducto == sq.c.idProducto))
    return consulta, stock
