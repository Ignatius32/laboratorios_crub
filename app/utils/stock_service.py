"""
Servicio para gestionar las operaciones de stock
"""
from app.models.models import db, Stock, Movimiento, Producto

def actualizar_stock_por_movimiento(movimiento):
    """
    Actualiza o crea un registro de stock basado en un movimiento
    
    Args:
        movimiento: El objeto Movimiento que se acaba de registrar
    """
    # Buscar registro de stock existente para este producto y laboratorio
    stock = Stock.query.filter_by(
        idProducto=movimiento.idProducto,
        idLaboratorio=movimiento.idLaboratorio
    ).first()
    
    # Si no existe, crear uno nuevo
    if not stock:
        stock = Stock(
            idProducto=movimiento.idProducto,
            idLaboratorio=movimiento.idLaboratorio,
            cantidad=0
        )
        db.session.add(stock)
    
    # Actualizar stock según el tipo de movimiento
    if movimiento.tipoMovimiento.lower() in ['ingreso', 'compra']:
        stock.cantidad += movimiento.cantidad
    elif movimiento.tipoMovimiento.lower() in ['egreso', 'uso', 'transferencia']:
        stock.cantidad -= movimiento.cantidad
    
    # En caso de transferencia, actualizar también el destino
    if movimiento.tipoMovimiento.lower() == 'transferencia' and movimiento.laboratorioDestino:
        # Buscar o crear stock en laboratorio destino
        stock_destino = Stock.query.filter_by(
            idProducto=movimiento.idProducto,
            idLaboratorio=movimiento.laboratorioDestino
        ).first()
        
        if not stock_destino:
            stock_destino = Stock(
                idProducto=movimiento.idProducto,
                idLaboratorio=movimiento.laboratorioDestino,
                cantidad=0
            )
            db.session.add(stock_destino)
        
        # Aumentar el stock en el destino
        stock_destino.cantidad += movimiento.cantidad
    
    # Los cambios se guardarán con el commit que se hará después de llamar a esta función
