#!/usr/bin/env python3
"""Verifica que el entorno tenga instalado lo que declara requirements.txt.

La lista NO se escribe acá: se lee de requirements.txt. La versión anterior
llevaba una lista a mano de seis paquetes de la época del flujo OIDC, y con el
tiempo quedó al revés de la realidad: exigía `authlib`, que se eliminó junto con
ese flujo, y no miraba pandas, numpy, openpyxl, xlsxwriter ni SQLAlchemy, que sí
hacen falta. O sea que en un entorno correcto reportaba un fallo inventado, y en
uno al que le faltaba de verdad una dependencia decía que estaba todo bien.

Además compara la versión instalada contra el pin, porque un entorno viejo con
los paquetes correctos pero en otra versión es exactamente el problema que hay
que detectar: se prueba una cosa y se despliega otra.
"""

import re
import sys
from importlib import metadata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REQUISITOS = RAIZ / 'requirements.txt'


def leer_requisitos(ruta=REQUISITOS):
    """Devuelve [(paquete, version_pinada)] a partir de requirements.txt."""
    if not ruta.exists():
        return []
    paquetes = []
    for linea in ruta.read_text(encoding='utf-8').splitlines():
        linea = linea.split('#', 1)[0].strip()
        if not linea:
            continue
        m = re.match(r'^([A-Za-z0-9._-]+)\s*==\s*([^\s;]+)', linea)
        if m:
            paquetes.append((m.group(1), m.group(2)))
    return paquetes


def check_dependencies():
    print('=' * 60)
    print('DEPENDENCIAS  (contra requirements.txt)')
    print('=' * 60)

    requisitos = leer_requisitos()
    if not requisitos:
        print(f'No se pudo leer {REQUISITOS}')
        return False

    faltantes, desalineados = [], []
    for paquete, pin in requisitos:
        try:
            instalada = metadata.version(paquete)
        except metadata.PackageNotFoundError:
            print(f'  FALTA      {paquete:22} (requirements pide {pin})')
            faltantes.append(f'{paquete}=={pin}')
            continue

        if instalada == pin:
            print(f'  ok         {paquete:22} {instalada}')
        else:
            print(f'  DISTINTA   {paquete:22} instalada {instalada}, '
                  f'requirements pide {pin}')
            desalineados.append((paquete, instalada, pin))

    print('\n' + '=' * 60)
    if not faltantes and not desalineados:
        print(f'Entorno alineado con requirements.txt ({len(requisitos)} paquetes).')
        return True

    if faltantes:
        print(f'{len(faltantes)} sin instalar. Para instalarlas:')
        print(f'  pip install {" ".join(faltantes)}')
    if desalineados:
        print(f'{len(desalineados)} en una versión distinta de la declarada.')
        print('  El despliegue arma el entorno desde requirements.txt, así que')
        print('  lo que se prueba acá no es lo que va a correr en producción.')
        print('  Para alinearlo:  pip install -r requirements.txt')
    return False


if __name__ == '__main__':
    sys.exit(0 if check_dependencies() else 1)
