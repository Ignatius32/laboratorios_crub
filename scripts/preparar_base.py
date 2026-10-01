#!/usr/bin/env python3
"""Lleva una base que ya está en uso al esquema que espera esta versión.

`flask db upgrade` a secas no alcanza en el servidor, por dos motivos:

  * Parte del esquema no pasó por alembic. created_by y created_at se agregaron
    con un script suelto (migrations/add_audit_fields.py), y las tablas mismas
    las crea db.create_all() al arrancar. La tabla alembic_version puede no
    existir, o decir una revisión que no refleja lo que hay.
  * db.create_all() crea tablas que faltan, pero no agrega columnas ni índices
    a las que ya existen.

Así que primero se empareja lo que hay con los modelos (columnas e índices que
falten), después se le dice a alembic desde dónde seguir, y recién ahí corren
las migraciones nuevas. Se puede correr más de una vez: lo que ya está hecho se
saltea.

No hace respaldo. Eso es de scripts/actualizar_servidor.sh, que lo toma antes
de llamar a este script y lo repone si algo falla.

    venv/bin/python scripts/preparar_base.py
"""

import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
os.chdir(RAIZ)  # flask-migrate busca migrations/ en el directorio actual
sys.path.insert(0, str(RAIZ))

from flask_migrate import stamp, upgrade
from sqlalchemy import inspect, text

# Por wsgi y no por create_app: así se usa el mismo .env y la misma clase de
# configuración que Apache, y por lo tanto la misma base.
from wsgi import application as app
from app.models.models import db

# La última revisión anterior a esta versión. Emparejadas las columnas y los
# índices, la base queda equivalente a este punto de la cadena.
REVISION_BASE = 'dc2584637bea'
REVISIONES_NUEVAS = {'b7c41a9e5d02', 'c93f8a1d4e77', 'e1a5c7d2f404'}

TABLAS_CON_DATOS = ('usuario', 'laboratorio', 'proveedor', 'producto',
                    'movimiento', 'user_laboratorio')


def contar_filas(conn):
    existentes = set(inspect(conn).get_table_names())
    return {t: conn.execute(text(f'SELECT COUNT(*) FROM "{t}"')).scalar()
            for t in TABLAS_CON_DATOS if t in existentes}


def emparejar_con_modelos(conn):
    """Agrega las columnas y los índices que los modelos tienen y la base no."""
    insp = inspect(conn)
    for tabla in db.metadata.sorted_tables:
        presentes = {c['name'] for c in insp.get_columns(tabla.name)}
        for columna in tabla.columns:
            if columna.name in presentes:
                continue
            if not columna.nullable:
                # No hay con qué llenar las filas que ya existen.
                sys.exit(f'ERROR: falta la columna obligatoria '
                         f'{tabla.name}.{columna.name} y no se puede agregar '
                         f'sola. No se modificó nada más.')
            tipo = columna.type.compile(dialect=conn.dialect)
            conn.execute(text(
                f'ALTER TABLE "{tabla.name}" ADD COLUMN "{columna.name}" {tipo}'))
            print(f'  + columna {tabla.name}.{columna.name}')

        indices = {i['name'] for i in inspect(conn).get_indexes(tabla.name)}
        for indice in tabla.indexes:
            if indice.name not in indices:
                indice.create(conn)
                print(f'  + índice {indice.name}')


def revision_actual(conn):
    if 'alembic_version' not in inspect(conn).get_table_names():
        return None
    fila = conn.execute(text('SELECT version_num FROM alembic_version')).first()
    return fila[0] if fila else None


def main():
    with app.app_context():
        print(f'Base: {db.engine.url.render_as_string(hide_password=True)}')

        with db.engine.begin() as conn:
            antes = contar_filas(conn)
            print(f'Filas antes: {antes}')
            if not antes.get('producto') and not antes.get('movimiento'):
                # Una base recién creada por create_all en el lugar equivocado
                # se ve exactamente así. Mejor avisar que migrar la que no es.
                print('AVISO: la base no tiene productos ni movimientos. Si '
                      'el servidor ya tenía datos, DATABASE_URI apunta a otro '
                      'archivo.')
            emparejar_con_modelos(conn)
            actual = revision_actual(conn)

        print(f'Revisión de alembic: {actual or "ninguna"}')
        if actual not in REVISIONES_NUEVAS:
            stamp(revision=REVISION_BASE, purge=True)
        upgrade()

        with db.engine.connect() as conn:
            despues = contar_filas(conn)
            insp = inspect(conn)
            columnas_usuario = {c['name'] for c in insp.get_columns('usuario')}
            problemas = []
            if despues != antes:
                problemas.append(f'cambió la cantidad de filas: {antes} -> {despues}')
            if 'password_hash' in columnas_usuario:
                problemas.append('usuario.password_hash sigue existiendo')
            if 'stock' in insp.get_table_names():
                problemas.append('la tabla stock sigue existiendo')
            print(f'Filas después: {despues}')
            print(f'Revisión de alembic: {revision_actual(conn)}')

        if problemas:
            sys.exit('ERROR: ' + '; '.join(problemas))
        print('Base lista.')


if __name__ == '__main__':
    main()
