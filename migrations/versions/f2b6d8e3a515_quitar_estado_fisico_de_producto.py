"""Quitar el estado físico del producto

Sólido, líquido o gaseoso era un dato que no usaba nadie: no entraba en el
stock ni en los reportes, y lo único que parecía depender de él —en qué unidad
se mide el producto— ahora es un campo propio (unidadMedida).

Va después de e1a5c7d2f404 a propósito: esa migración todavía lo lee para
asignar la unidad a los productos que no pudo resolver de otra forma.

El downgrade devuelve la columna vacía: los valores no se guardan en ningún
otro lado.

Revision ID: f2b6d8e3a515
Revises: e1a5c7d2f404
Create Date: 2026-10-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f2b6d8e3a515'
down_revision = 'e1a5c7d2f404'
branch_labels = None
depends_on = None


def upgrade():
    # Puede no existir: las bases creadas con create_all después de quitar el
    # campo del modelo no la tienen.
    columnas = {c['name'] for c in sa.inspect(op.get_bind()).get_columns('producto')}
    if 'estadoFisico' not in columnas:
        return
    # batch_alter_table porque SQLite no sabe borrar columnas: alembic rehace
    # la tabla y copia los datos.
    with op.batch_alter_table('producto', schema=None) as batch_op:
        batch_op.drop_column('estadoFisico')


def downgrade():
    with op.batch_alter_table('producto', schema=None) as batch_op:
        # nullable=True aunque antes era obligatoria: no hay con qué llenarla.
        batch_op.add_column(sa.Column('estadoFisico', sa.String(length=20), nullable=True))
