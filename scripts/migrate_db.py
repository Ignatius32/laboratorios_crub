"""
Script de migración para convertir productos específicos de laboratorio a productos globales
Eliminar la columna idLaboratorio de la tabla productos
"""
from app import create_app
from app.models.models import db, Producto, Laboratorio, Movimiento
import sqlalchemy as sa
from sqlalchemy import text
import sys

def migrate_products():
    print("Iniciando migración de la base de datos...")
    
    # Verificar si la columna idLaboratorio existe en la tabla producto
    inspector = sa.inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('producto')]
    
    if 'idLaboratorio' not in columns:
        print("La columna idLaboratorio ya fue eliminada. No se requiere migración.")
        return
    
    print("Recuperando información actual de productos y sus laboratorios...")
    
    # Recuperar todos los productos con su laboratorio actual
    productos_info = []
    try:
        productos = Producto.query.all()
        for producto in productos:
            lab_id = producto.idLaboratorio
            productos_info.append({
                'id_producto': producto.idProducto,
                'id_laboratorio': lab_id
            })
    except Exception as e:
        print(f"Error al recuperar la información de productos: {str(e)}")
        return
    
    print(f"Se encontraron {len(productos_info)} productos para migrar.")
    
    # Crear movimiento inicial para cada producto en su laboratorio original
    print("Creando movimientos iniciales para mantener el stock en los laboratorios originales...")
    
    for info in productos_info:
        try:
            # Obtener stock actual
            ingresos = db.session.query(sa.func.sum(Movimiento.cantidad)).filter(
                Movimiento.idProducto == info['id_producto'],
                Movimiento.tipoMovimiento == 'ingreso'
            ).scalar() or 0
            
            egresos = db.session.query(sa.func.sum(Movimiento.cantidad)).filter(
                Movimiento.idProducto == info['id_producto'],
                Movimiento.tipoMovimiento == 'egreso'
            ).scalar() or 0
            
            stock_actual = ingresos - egresos
            
            if stock_actual > 0:
                # Crear un movimiento de ingreso inicial con el stock actual
                import random
                import string
                movement_id = 'MIG' + ''.join(random.choices(string.digits, k=6))
                
                nuevo_movimiento = Movimiento(
                    idMovimiento=movement_id,
                    tipoMovimiento='ingreso',
                    cantidad=stock_actual,
                    unidadMedida='unidades',  # Unidad por defecto
                    idProducto=info['id_producto'],
                    idLaboratorio=info['id_laboratorio']
                )
                
                db.session.add(nuevo_movimiento)
                print(f"Creado movimiento inicial para producto {info['id_producto']} en laboratorio {info['id_laboratorio']} con stock {stock_actual}")
        
        except Exception as e:
            print(f"Error al procesar producto {info['id_producto']}: {str(e)}")
    
    try:
        # Confirmar los cambios de los movimientos
        db.session.commit()
        print("Movimientos iniciales creados correctamente.")
    except Exception as e:
        db.session.rollback()
        print(f"Error al crear movimientos iniciales: {str(e)}")
        return
    
    # Eliminar la columna idLaboratorio de la tabla producto
    print("Eliminando la columna idLaboratorio de la tabla producto...")
    
    try:
        # En SQLite, no se puede eliminar una columna directamente, por lo que creamos una nueva tabla
        # y copiamos los datos
        
        # 1. Crear una tabla temporal sin la columna idLaboratorio
        with db.engine.begin() as conn:
            conn.execute(text("""
            CREATE TABLE producto_new (
                idProducto VARCHAR(10) PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                descripcion TEXT,
                tipoProducto VARCHAR(50) NOT NULL,
                estadoFisico VARCHAR(20) NOT NULL,
                controlSedronar BOOLEAN DEFAULT 0,
                urlFichaSeguridad VARCHAR(200)
            )
            """))
            
            # 2. Copiar datos de la tabla original a la nueva
            conn.execute(text("""
            INSERT INTO producto_new 
            SELECT idProducto, nombre, descripcion, tipoProducto, estadoFisico, controlSedronar, urlFichaSeguridad
            FROM producto
            """))
            
            # 3. Eliminar la tabla original
            conn.execute(text("DROP TABLE producto"))
            
            # 4. Renombrar la nueva tabla
            conn.execute(text("ALTER TABLE producto_new RENAME TO producto"))
            
        print("Columna idLaboratorio eliminada correctamente.")
        
    except Exception as e:
        print(f"Error al eliminar la columna idLaboratorio: {str(e)}")
        return
    
    print("Migración completada exitosamente.")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        # Pedir confirmación
        print("ADVERTENCIA: Esta operación modificará la estructura de la base de datos.")
        print("Por favor, haga una copia de seguridad antes de continuar.")
        print("¿Está seguro de que desea continuar? (s/n)")
        
        respuesta = input().strip().lower()
        if respuesta == 's':
            migrate_products()
        else:
            print("Migración cancelada.")