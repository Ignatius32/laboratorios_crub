"""La unidad de medida pasa a ser del producto

Hasta acá la unidad se elegía en cada movimiento, así que un mismo producto
podía tener movimientos en Lt y en Kg, y el alta de producto desde el panel de
técnicos dejaba un movimiento inicial en 'unidades'. El stock suma cantidades
sin mirar la unidad, de modo que esas mezclas daban totales sin sentido.

Ahora cada producto tiene su unidad (Lt o Kg) y los movimientos la heredan.

Para los productos que ya existen la unidad sale, en este orden:

  1. De la lista de sustancias que definió el laboratorio, por nombre (sin
     distinguir mayúsculas ni acentos).
  2. De la unidad más usada en los movimientos del producto, si es Lt o Kg.
  3. Del estado físico: sólido en Kg, el resto en Lt. Es sólo un punto de
     partida para lo que no se pudo resolver de otra forma: la migración lista
     qué regla usó en cada producto para que se revise, y la unidad se corrige
     desde el formulario del producto.

Después se alinea la unidad de todos los movimientos con la de su producto.
Las cantidades no se tocan.

El downgrade quita la columna. La unidad original de cada movimiento no se
puede reponer.

Revision ID: e1a5c7d2f404
Revises: c93f8a1d4e77
Create Date: 2026-10-01

"""
import unicodedata

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1a5c7d2f404'
down_revision = 'c93f8a1d4e77'
branch_labels = None
depends_on = None


UNIDAD_POR_NOMBRE = {
    'Acetona': 'Lt',
    'Acido clorhídrico': 'Lt',
    'Acido sulfúrico': 'Lt',
    'Anhídrido acético': 'Lt',
    'Eter etílico': 'Lt',
    'Permanganato de potasio': 'Kg',
    'Acetato etílico': 'Lt',
    'Acido acético': 'Lt',
    'Amoníaco en disolución 28%': 'Lt',
    'Benceno': 'Lt',
    'Cloruro de metileno': 'Lt',
    'Hexano': 'Lt',
    'Piperidina': 'Lt',
    'Tolueno': 'Lt',
    'Xileno': 'Lt',
    'Benzaldehído': 'Lt',
    'Carbonato de potasio': 'Kg',
    'Carbonato de sodio': 'Kg',
    'Hidróxido de potasio': 'Kg',
    'Hidróxido de sodio': 'Kg',
    'Sulfato de sodio': 'Kg',
    'Metil Etil Cetona': 'Lt',
    'Cloroformo': 'Lt',
    'Bicarbonato de sodio': 'Kg',
    'Cianuro de potasio': 'Kg',
}


def _normalizar(texto):
    sin_acentos = ''.join(c for c in unicodedata.normalize('NFD', texto or '')
                          if unicodedata.category(c) != 'Mn')
    return ' '.join(sin_acentos.lower().split())


def _unidad_de_la_lista(nombre):
    """La unidad de la lista para este nombre, o None.

    Coincidencia exacta primero; si no, que el nombre empiece con uno de la
    lista seguido de un espacio ('Acido clorhídrico 37%'). Entre varios
    candidatos gana el más largo.
    """
    lista = {_normalizar(n): u for n, u in UNIDAD_POR_NOMBRE.items()}
    nombre = _normalizar(nombre)
    if nombre in lista:
        return lista[nombre]
    candidatos = [n for n in lista if nombre.startswith(n + ' ')]
    return lista[max(candidatos, key=len)] if candidatos else None


def upgrade():
    conn = op.get_bind()

    # Puede existir ya: scripts/preparar_base.py agrega las columnas que el
    # modelo tiene y la base no antes de correr las migraciones.
    columnas = {c['name'] for c in sa.inspect(conn).get_columns('producto')}
    if 'unidadMedida' not in columnas:
        op.add_column('producto', sa.Column('unidadMedida', sa.String(length=10), nullable=True))

    # estadoFisico se quita en la migración siguiente, y una base creada
    # después con create_all ya no lo tiene: sin él, la tercera regla no corre.
    estado = '"estadoFisico"' if 'estadoFisico' in columnas else 'NULL'
    productos = conn.execute(sa.text(
        f'SELECT "idProducto", nombre, {estado} FROM producto '
        'WHERE "unidadMedida" IS NULL ORDER BY nombre')).fetchall()

    for id_producto, nombre, estado in productos:
        unidad, regla = _unidad_de_la_lista(nombre), 'lista'
        if not unidad:
            fila = conn.execute(sa.text(
                'SELECT "unidadMedida" FROM movimiento '
                'WHERE "idProducto" = :id AND "unidadMedida" IN (\'Lt\', \'Kg\') '
                'GROUP BY "unidadMedida" ORDER BY COUNT(*) DESC, "unidadMedida" DESC LIMIT 1'),
                {'id': id_producto}).first()
            if fila:
                unidad, regla = fila[0], 'movimientos'
            elif estado:
                unidad, regla = ('Kg' if estado == 'solido' else 'Lt'), 'estado físico'
            else:
                print(f'  SIN UNIDAD: {id_producto}  {nombre} (cargarla desde el formulario del producto)')
                continue
        conn.execute(sa.text('UPDATE producto SET "unidadMedida" = :u WHERE "idProducto" = :id'),
                     {'u': unidad, 'id': id_producto})
        print(f'  unidad {unidad}  ({regla:<13})  {id_producto}  {nombre}')

    cambiados = conn.execute(sa.text(
        'SELECT m."idMovimiento", m."unidadMedida", p."unidadMedida", m.cantidad, p.nombre '
        'FROM movimiento m JOIN producto p ON p."idProducto" = m."idProducto" '
        'WHERE m."unidadMedida" <> p."unidadMedida"')).fetchall()
    for id_mov, antes, ahora, cantidad, nombre in cambiados:
        print(f'  movimiento {id_mov}: {cantidad:g} {antes} -> {ahora}  ({nombre})')
    conn.execute(sa.text(
        'UPDATE movimiento SET "unidadMedida" = ('
        '  SELECT p."unidadMedida" FROM producto p WHERE p."idProducto" = movimiento."idProducto") '
        'WHERE "unidadMedida" <> ('
        '  SELECT p."unidadMedida" FROM producto p WHERE p."idProducto" = movimiento."idProducto")'))
    print(f'  {len(productos)} producto(s) con unidad asignada, '
          f'{len(cambiados)} movimiento(s) con la unidad corregida')


def downgrade():
    with op.batch_alter_table('producto', schema=None) as batch_op:
        batch_op.drop_column('unidadMedida')
