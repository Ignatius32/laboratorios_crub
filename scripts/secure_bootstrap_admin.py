#!/usr/bin/env python3
"""
Neutraliza la contraseña local de la cuenta administradora de arranque.

La cuenta semilla ADMIN001 se creaba con el valor de ADMIN_PASSWORD, que durante
mucho tiempo fue `admin123` y estuvo publicado en el repositorio. Aunque el atajo
de login por variables de entorno ya no existe, el hash sigue en la base y
permite entrar por el formulario local. Este script le asigna una contraseña
aleatoria imposible de adivinar.

Uso:
    python scripts/secure_bootstrap_admin.py            # informa qué haría
    python scripts/secure_bootstrap_admin.py --aplicar  # aplica los cambios

Ejecutarlo también en el servidor de producción, apuntando a su base.
"""
import argparse
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from werkzeug.security import check_password_hash  # noqa: E402

from app import create_app  # noqa: E402
from app.models.models import Usuario, db  # noqa: E402
from config import Config, DevelopmentConfig, ProductionConfig  # noqa: E402

# Contraseñas que estuvieron en el repositorio o como valor por defecto.
CONTRASENAS_COMPROMETIDAS = ['admin123', 'password123', 'admin']


def elegir_config():
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        return ProductionConfig
    if env == 'development':
        return DevelopmentConfig
    return Config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--aplicar', action='store_true',
                        help='Aplica los cambios (sin esta bandera solo informa)')
    args = parser.parse_args()

    app = create_app(elegir_config())

    with app.app_context():
        usuarios = Usuario.query.all()
        afectados = []

        for usuario in usuarios:
            if not usuario.password_hash:
                continue
            for debil in CONTRASENAS_COMPROMETIDAS:
                if check_password_hash(usuario.password_hash, debil):
                    afectados.append((usuario, debil))
                    break

        if not afectados:
            print(f'Revisados {len(usuarios)} usuarios: ninguno usa una contraseña comprometida.')
            return 0

        print(f'Usuarios con contraseña comprometida ({len(afectados)} de {len(usuarios)}):')
        for usuario, debil in afectados:
            print(f'  - {usuario.idUsuario} <{usuario.email}> rol={usuario.rol} contraseña="{debil}"')

        if not args.aplicar:
            print('\nModo informe. Volvé a ejecutar con --aplicar para asignarles '
                  'una contraseña aleatoria.')
            return 1

        for usuario, _ in afectados:
            usuario.set_password(secrets.token_urlsafe(64))
        db.session.commit()

        print(f'\nListo: {len(afectados)} cuenta(s) con contraseña aleatoria. '
              'El acceso local por formulario ya no es posible para esas cuentas; '
              'usá Keycloak o el flujo de recuperación de contraseña.')
        return 0


if __name__ == '__main__':
    sys.exit(main())
