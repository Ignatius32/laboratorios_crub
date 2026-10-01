"""Eliminar la tabla stock, que nunca se usó

El stock se calcula a partir de los movimientos en cada consulta
(app/utils/stock_service.py). La tabla `stock` era un espejo que ninguna parte
del código leía ni escribía: quedaba siempre vacía y confundía a quien leyera
el esquema.

El downgrade la vuelve a crear, vacía. No hay datos que restaurar porque nunca
los hubo, y de necesitarse se reconstruye sumando los movimientos.

Revision ID: c93f8a1d4e77
Revises: b7c41a9e5d02
Create Date: 2026-08-26

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c93f8a1d4e77'
down_revision = 'b7c41a9e5d02'
branch_labels = None
depends_on = None


def upgrade():
    # Puede no existir: las bases creadas con create_all después de quitar el
    # modelo no la tienen, y hacer fallar la migración por eso no ayuda a nadie.
    if 'stock' in sa.inspect(op.get_bind()).get_table_names():
        op.drop_table('stock')


def downgrade():
    op.create_table(
        'stock',
        sa.Column('idStock', sa.Integer(), nullable=False),
        sa.Column('idProducto', sa.String(length=10), nullable=False),
        sa.Column('idLaboratorio', sa.String(length=10), nullable=False),
        sa.Column('cantidad', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['idLaboratorio'], ['laboratorio.idLaboratorio']),
        sa.ForeignKeyConstraint(['idProducto'], ['producto.idProducto']),
        sa.PrimaryKeyConstraint('idStock'),
        sa.UniqueConstraint('idProducto', 'idLaboratorio', name='unique_producto_laboratorio'),
    )
    with op.batch_alter_table('stock', schema=None) as batch_op:
        batch_op.create_index('idx_stock_lab_producto', ['idLaboratorio', 'idProducto'])
        batch_op.create_index(batch_op.f('ix_stock_idLaboratorio'), ['idLaboratorio'])
        batch_op.create_index(batch_op.f('ix_stock_idProducto'), ['idProducto'])
