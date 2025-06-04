"""
Servicio para gestionar las operaciones de stock
Cálculos de stock en tiempo real sin cache - Solución simplificada
"""
from app.models.models import db, Stock, Movimiento, Producto
from sqlalchemy import func, case

# FUNCIONES PRINCIPALES PARA CÁLCULO DE STOCK EN TIEMPO REAL (SIN CACHE)

def get_stock_for_product_in_lab(product_id, lab_id):
    """
    Calcula el stock actual de un producto en un laboratorio específico
    basándose directamente en los movimientos. FUNCIÓN PRINCIPAL.
    
    Args:
        product_id: ID del producto
        lab_id: ID del laboratorio
    
    Returns:
        float: Stock actual calculado en tiempo real
    """
    result = db.session.query(
        func.coalesce(
            func.sum(
                case(
                    (Movimiento.tipoMovimiento.in_(['ingreso', 'compra']), Movimiento.cantidad),
                    (Movimiento.tipoMovimiento.in_(['egreso', 'uso', 'salida', 'transferencia']), -Movimiento.cantidad),
                    else_=0
                )
            ), 
            0
        ).label('stock_actual')
    ).filter(
        Movimiento.idProducto == product_id,
        Movimiento.idLaboratorio == lab_id
    ).scalar()
    
    return float(result or 0)

def get_stock_map_for_lab(lab_id, product_ids=None):
    """
    Obtiene un mapa de stock en tiempo real para productos en un laboratorio específico.
    FUNCIÓN PRINCIPAL OPTIMIZADA.
    
    Args:
        lab_id: ID del laboratorio
        product_ids: Lista opcional de IDs de productos
    
    Returns:
        dict: {product_id: stock_actual}
    """
    query = db.session.query(
        Movimiento.idProducto,
        func.coalesce(
            func.sum(
                case(
                    (Movimiento.tipoMovimiento.in_(['ingreso', 'compra']), Movimiento.cantidad),
                    (Movimiento.tipoMovimiento.in_(['egreso', 'uso', 'salida', 'transferencia']), -Movimiento.cantidad),
                    else_=0
                )
            ), 
            0
        ).label('stock_actual')
    ).filter(
        Movimiento.idLaboratorio == lab_id
    )
    
    if product_ids:
        query = query.filter(Movimiento.idProducto.in_(product_ids))
    
    query = query.group_by(Movimiento.idProducto)
    
    result = {}
    for row in query:
        result[row.idProducto] = float(row.stock_actual or 0)
    
    return result

def get_global_stock_map(product_ids=None):
    """
    Obtiene un mapa de stock global (todos los laboratorios) en tiempo real.
    FUNCIÓN PRINCIPAL PARA STOCK GLOBAL.
    
    Args:
        product_ids: Lista opcional de IDs de productos
    
    Returns:
        dict: {product_id: stock_total_global}
    """
    query = db.session.query(
        Movimiento.idProducto,
        func.coalesce(
            func.sum(
                case(
                    (Movimiento.tipoMovimiento.in_(['ingreso', 'compra']), Movimiento.cantidad),
                    (Movimiento.tipoMovimiento.in_(['egreso', 'uso', 'salida', 'transferencia']), -Movimiento.cantidad),
                    else_=0
                )
            ), 
            0
        ).label('stock_global')
    )
    
    if product_ids:
        query = query.filter(Movimiento.idProducto.in_(product_ids))
    
    query = query.group_by(Movimiento.idProducto)
    
    result = {}
    for row in query:
        result[row.idProducto] = float(row.stock_global or 0)
    
    return result

def get_stock_by_lab_map(product_ids=None):
    """
    Obtiene un mapa completo de stock por laboratorio en tiempo real.
    FUNCIÓN PRINCIPAL PARA DISTRIBUCIÓN POR LABORATORIO.
    
    Args:
        product_ids: Lista opcional de IDs de productos
    
    Returns:
        dict: {product_id: {lab_id: stock_en_lab}}
    """
    query = db.session.query(
        Movimiento.idProducto,
        Movimiento.idLaboratorio,
        func.coalesce(
            func.sum(
                case(
                    (Movimiento.tipoMovimiento.in_(['ingreso', 'compra']), Movimiento.cantidad),
                    (Movimiento.tipoMovimiento.in_(['egreso', 'uso', 'salida', 'transferencia']), -Movimiento.cantidad),
                    else_=0
                )
            ), 
            0
        ).label('stock_actual')
    )
    
    if product_ids:
        query = query.filter(Movimiento.idProducto.in_(product_ids))
    
    query = query.group_by(Movimiento.idProducto, Movimiento.idLaboratorio)
    
    result = {}
    for row in query:
        if row.idProducto not in result:
            result[row.idProducto] = {}
        result[row.idProducto][row.idLaboratorio] = float(row.stock_actual or 0)
    
    return result

# FUNCIONES DE COMPATIBILIDAD (REDIRIGEN A LAS FUNCIONES PRINCIPALES)
# Mantenemos los nombres antiguos para no romper el código existente

def get_stock_map_for_laboratory(lab_id, product_ids=None):
    """Función de compatibilidad - usa cálculo en tiempo real"""
    return get_stock_map_for_lab(lab_id, product_ids)

def get_stock_for_product_in_laboratory(product_id, lab_id):
    """Función de compatibilidad - usa cálculo en tiempo real"""
    return get_stock_for_product_in_lab(product_id, lab_id)

def get_global_stock_for_products(product_ids=None):
    """Función de compatibilidad - usa cálculo en tiempo real"""
    return get_global_stock_map(product_ids)

def get_stock_map_for_all_laboratories(product_ids=None):
    """Función de compatibilidad - usa cálculo en tiempo real"""
    return get_stock_by_lab_map(product_ids)

# FUNCIONES ANTIGUAS CONSERVADAS PARA REFERENCIAS
# Estas son las funciones que ya estaban implementadas pero con nombres más largos

def get_real_time_stock_for_product_in_lab(product_id, lab_id):
    """Función legacy - usa la función principal"""
    return get_stock_for_product_in_lab(product_id, lab_id)

def get_real_time_stock_map_for_lab(lab_id, product_ids=None):
    """Función legacy - usa la función principal"""
    return get_stock_map_for_lab(lab_id, product_ids)

def get_real_time_global_stock_map(product_ids=None):
    """Función legacy - usa la función principal"""
    return get_global_stock_map(product_ids)

def get_real_time_stock_by_lab_map(product_ids=None):
    """Función legacy - usa la función principal"""
    return get_stock_by_lab_map(product_ids)

# FUNCIONES UTILITARIAS (OPCIONALES - PARA MIGRACIÓN O CORRECCIÓN)

def recalculate_stock_from_movements(product_id=None, lab_id=None):
    """
    DEPRECADA: Ya no es necesaria porque calculamos en tiempo real.
    Se mantiene para compatibilidad pero no hace nada útil en el nuevo sistema.
    """
    print("⚠️  ADVERTENCIA: recalculate_stock_from_movements está deprecada.")
    print("   El nuevo sistema calcula stock en tiempo real, no necesita recálculo.")
    return True
    