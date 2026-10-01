"""Quitar las credenciales locales de la tabla usuario

La aplicación ya no valida contraseñas: la única forma de entrar es contra el
Keycloak del CRUB. Las columnas password_hash, password_reset_token y
password_reset_expiration quedaron sin uso y guardaban hashes que nadie va a
verificar, así que se van.

El downgrade las devuelve vacías: los hashes no se pueden recuperar, y hacen
falta las pantallas de contraseña que también se quitaron para volver a
llenarlas.

Revision ID: b7c41a9e5d02
Revises: dc2584637bea
Create Date: 2026-08-26

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7c41a9e5d02'
down_revision = 'dc2584637bea'
branch_labels = None
depends_on = None


def upgrade():
    # batch_alter_table porque SQLite no sabe borrar columnas: alembic rehace
    # la tabla y copia los datos.
    #
    # Sólo las que existan: password_reset_token y password_reset_expiration no
    # las agregó ninguna migración, así que una base más vieja que esas pantallas
    # no las tiene y borrarlas a ciegas hacía fallar la actualización.
    presentes = {c['name'] for c in sa.inspect(op.get_bind()).get_columns('usuario')}
    sobran = [c for c in ('password_hash', 'password_reset_token',
                          'password_reset_expiration') if c in presentes]
    if not sobran:
        return
    with op.batch_alter_table('usuario', schema=None) as batch_op:
        for columna in sobran:
            batch_op.drop_column(columna)


def downgrade():
    with op.batch_alter_table('usuario', schema=None) as batch_op:
        # nullable=True aunque el modelo viejo la tenía obligatoria: en las
        # filas que ya existen no hay ningún hash con qué llenarla.
        batch_op.add_column(sa.Column('password_hash', sa.String(length=256), nullable=True))
        batch_op.add_column(sa.Column('password_reset_token', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('password_reset_expiration', sa.DateTime(), nullable=True))
