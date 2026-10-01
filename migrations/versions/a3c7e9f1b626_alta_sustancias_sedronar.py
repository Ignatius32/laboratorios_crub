"""Alta de sustancias controladas por Sedronar

Da de alta en el catálogo las sustancias de la lista que pasó el laboratorio,
todas de tipo droguero y con control Sedronar, cada una con su unidad. El ID se
asigna correlativo, igual que en el formulario (P0001, P0002, ...).

Se puede correr más de una vez: un producto que ya existe con ese nombre (sin
distinguir mayúsculas ni acentos) no se vuelve a crear ni se modifica.
'Metiletilcetona' tampoco se crea si ya está cargada como 'Metil Etil Cetona',
que es la misma sustancia.

Dos nombres de la lista pasan de 100 caracteres, así que antes se ensancha
producto.nombre a 200.

El downgrade sólo devuelve el ancho de la columna. Los productos no se borran:
para entonces pueden tener movimientos.

Revision ID: a3c7e9f1b626
Revises: f2b6d8e3a515
Create Date: 2026-10-01

"""
import unicodedata
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3c7e9f1b626'
down_revision = 'f2b6d8e3a515'
branch_labels = None
depends_on = None


SUSTANCIAS = [
    ('Cornezuelo de centeno', 'Kg'),
    ('Fósforo rojo', 'Kg'),
    ('Óleum (ácido sulfúrico fumante)', 'Lt'),
    ('Ácido yodhídrico', 'Lt'),
    ('Nitroetano', 'Lt'),
    ('Nitrometano', 'Lt'),
    ('Metiletilcetona', 'Lt'),
    ('1-Fenil-2-propanona y sus derivados y analogos', 'Lt'),
    ('Ácido fenilacético, sus sales y sus ésteres', 'Lt'),
    ('Alfa-Fenilacetoacetato de metilo (MAPA) y sus isómeros ópticos', 'Kg'),
    ('Metilamina y sus sales', 'Kg'),
    ('Monoetilamina y sus sales', 'Kg'),
    ('Ácido N-acetilantranílico y sus sales', 'Kg'),
    ('Alfa-Fenilacetoacetamida (APAA) y sus isómeros ópticos', 'Kg'),
    ('Alfa-Fenilacetoacetonitrilo (APAAN) y sus isómeros ópticos', 'Kg'),
    ('Isosafrol y sus isómeros geométricos', 'Lt'),
    ('3,4-Metilenodioxifenil-2-propanona', 'Lt'),
    ('Piperonal', 'Kg'),
    ('Safrol', 'Lt'),
    ('3,4-MDP-2-P glicidato de metilo', 'Kg'),
    ('Ácido 3,4-MDP-2-P metilglicídico, sus sales y sus ésteres (metil-, etil-, propil-, '
     'isopropil-, butil-, isobutil-, secbutil- y terbutil-)', 'Kg'),
    ('Alfa-Metil-3,4-metilendioxifenil- propionamida (MMDPPA)', 'Kg'),
    ('4-Anilino-N-fenetilpiperidina (ANPP)', 'Kg'),
    ('N-Fenetil-4-piperidona (NPP)', 'Kg'),
    ('4-(fenilamino)piperidina-1-carboxilato de tert-butilo (1-boc-4- AP)', 'Kg'),
    ('N-fenil-4-piperidinamina (4-AP) y sus sales, amidas, carbamatos y haluros', 'Kg'),
    ('Norfentanilo', 'Kg'),
    ('Efedrina, sus sales, isómeros ópticos y sales de sus isómeros ópticos', 'Kg'),
    ('Seudoefedrina, sus sales, isómeros ópticos y sales de sus isómeros ópticos', 'Kg'),
    ('Fenilpropanolamina, sus sales, isómeros ópticos y sales de sus isómeros ópticos', 'Kg'),
    ('Ergometrina y sus sales', 'Kg'),
    ('Ergotamina y sus sales', 'Kg'),
    ('Ácido Lisérgico y sus sales', 'Kg'),
    ('Ergocristina, sus sales, sus derivados y sales de sus derivados', 'Kg'),
    ('Cloroefedrina, sus sales, isómeros ópticos y sales de sus isómeros ópticos', 'Kg'),
    ('Cloroseudoefedrina, sus sales, isómeros ópticos y sales de sus isómeros ópticos', 'Kg'),
    ('Ácido P-2-P metilglicídico y sus ésteres (metil-, etil-, propil-, isopropil-, butil-, '
     'isobutil-, secbutil- y terbutil-)', 'Kg'),
    ('4-Piperidona', 'Kg'),
    ('1-boc-4-piperidona', 'Kg'),
    ('2-(3,4-metilendioxifenil)acetil Malonato de Isopropilideno (IMDPAM)', 'Kg'),
    ('Alfa-Fenilacetoacetato de etilo (EAPA)', 'Kg'),
    ('1-Bromo-2,4-dinitrobenceno', 'Lt'),
    ('1-Cloro-2,4-dinitrobenceno', 'Lt'),
    ('1-Fluor-2,4-dinitrobenceno', 'Lt'),
    ('1-Bromo-2-nitrobenceno', 'Lt'),
    ('1-Cloro-2-nitrobenceno', 'Lt'),
    ('1-Fluor-2-nitrobenceno', 'Lt'),
    ('Hidroxilimina', 'Kg'),
    ('2-Clorofenil ciclopentil cetona', 'Lt'),
    ('Beta-Fenilacetoacetato de metilo', 'Kg'),
    ('1,4-Butanodiol', 'Lt'),
    ('Orto-Metil-4-AP', 'Kg'),
    ('Metilisobutilcetona', 'Lt'),
    ('Ácido o-aminobenzoico y sus sales', 'Kg'),
]

# La misma sustancia, escrita de otra forma en el catálogo que ya existía.
YA_CARGADA_COMO = {
    'Metiletilcetona': 'Metil Etil Cetona',
}


def _normalizar(texto):
    sin_acentos = ''.join(c for c in unicodedata.normalize('NFD', texto or '')
                          if unicodedata.category(c) != 'Mn')
    return ' '.join(sin_acentos.lower().split())


def upgrade():
    conn = op.get_bind()

    with op.batch_alter_table('producto', schema=None) as batch_op:
        batch_op.alter_column('nombre', existing_type=sa.String(length=100),
                              type_=sa.String(length=200), existing_nullable=False)

    filas = conn.execute(sa.text('SELECT "idProducto", nombre FROM producto')).fetchall()
    existentes = {_normalizar(nombre) for _id, nombre in filas}
    mayor = 0
    for id_producto, _nombre in filas:
        resto = id_producto[1:] if id_producto[:1] in ('P', 'p') else ''
        if resto.isdigit():
            mayor = max(mayor, int(resto))

    creados = 0
    for nombre, unidad in SUSTANCIAS:
        otro_nombre = YA_CARGADA_COMO.get(nombre)
        if _normalizar(nombre) in existentes or (
                otro_nombre and _normalizar(otro_nombre) in existentes):
            print(f'  ya estaba: {nombre}')
            continue
        mayor += 1
        id_producto = f'P{mayor:04d}'
        conn.execute(sa.text(
            'INSERT INTO producto ("idProducto", nombre, "tipoProducto", "unidadMedida", '
            '"controlSedronar", "stockMinimo", created_at) '
            'VALUES (:id, :nombre, \'droguero\', :unidad, 1, 0, :ahora)'),
            {'id': id_producto, 'nombre': nombre, 'unidad': unidad, 'ahora': datetime.utcnow()})
        existentes.add(_normalizar(nombre))
        creados += 1
        print(f'  + {id_producto}  {unidad}  {nombre}')

    print(f'  {creados} sustancia(s) dada(s) de alta, {len(SUSTANCIAS) - creados} ya estaba(n)')


def downgrade():
    with op.batch_alter_table('producto', schema=None) as batch_op:
        batch_op.alter_column('nombre', existing_type=sa.String(length=200),
                              type_=sa.String(length=100), existing_nullable=False)
