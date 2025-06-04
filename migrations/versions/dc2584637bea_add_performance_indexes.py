"""add_performance_indexes

Revision ID: dc2584637bea
Revises: 1d53e0a71220
Create Date: 2025-05-29 09:55:45.429289

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dc2584637bea'
down_revision = '1d53e0a71220'
branch_labels = None
depends_on = None


def upgrade():
    # Crear índices individuales en Movimiento
    op.create_index('idx_movimiento_timestamp', 'movimiento', ['timestamp'])
    op.create_index('idx_movimiento_laboratorio', 'movimiento', ['idLaboratorio'])
    op.create_index('idx_movimiento_producto', 'movimiento', ['idProducto'])
    op.create_index('idx_movimiento_proveedor', 'movimiento', ['idProveedor'])
    op.create_index('idx_movimiento_tipo', 'movimiento', ['tipoMovimiento'])
    
    # Crear índices compuestos para consultas comunes
    op.create_index('idx_movimiento_lab_producto', 'movimiento', ['idLaboratorio', 'idProducto'])
    op.create_index('idx_movimiento_lab_timestamp', 'movimiento', ['idLaboratorio', 'timestamp'])
    op.create_index('idx_movimiento_producto_timestamp', 'movimiento', ['idProducto', 'timestamp'])
    op.create_index('idx_movimiento_tipo_timestamp', 'movimiento', ['tipoMovimiento', 'timestamp'])
    
    # Crear índices en tabla Stock
    op.create_index('idx_stock_laboratorio', 'stock', ['idLaboratorio'])
    op.create_index('idx_stock_producto', 'stock', ['idProducto'])
    op.create_index('idx_stock_lab_producto', 'stock', ['idLaboratorio', 'idProducto'])
    
    # Crear índices en tabla Usuario
    op.create_index('idx_usuario_email', 'usuario', ['email'])
    op.create_index('idx_usuario_rol', 'usuario', ['rol'])
    
    # Crear índices en tabla Proveedor
    op.create_index('idx_proveedor_cuit', 'proveedor', ['cuit'])
    op.create_index('idx_proveedor_nombre', 'proveedor', ['nombre'])


def downgrade():
    # Eliminar índices en orden inverso
    op.drop_index('idx_proveedor_nombre', 'proveedor')
    op.drop_index('idx_proveedor_cuit', 'proveedor')
    op.drop_index('idx_usuario_rol', 'usuario')
    op.drop_index('idx_usuario_email', 'usuario')
    op.drop_index('idx_stock_lab_producto', 'stock')
    op.drop_index('idx_stock_producto', 'stock')
    op.drop_index('idx_stock_laboratorio', 'stock')
    op.drop_index('idx_movimiento_tipo_timestamp', 'movimiento')
    op.drop_index('idx_movimiento_producto_timestamp', 'movimiento')
    op.drop_index('idx_movimiento_lab_timestamp', 'movimiento')
    op.drop_index('idx_movimiento_lab_producto', 'movimiento')
    op.drop_index('idx_movimiento_tipo', 'movimiento')
    op.drop_index('idx_movimiento_proveedor', 'movimiento')
    op.drop_index('idx_movimiento_producto', 'movimiento')
    op.drop_index('idx_movimiento_laboratorio', 'movimiento')
    op.drop_index('idx_movimiento_timestamp', 'movimiento')
