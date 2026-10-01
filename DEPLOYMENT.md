# Apache Deployment Guide for Laboratorios CRUB

## Overview

This guide explains how to deploy the Laboratorios CRUB Flask application on an Apache web server using the base URL `/laboratorios-crub`.

## Prerequisites

- Apache web server with mod_wsgi enabled
- Python 3.9 or higher
- Virtual environment support
- Required Apache modules: `wsgi`, `headers`, `expires`

## Quick Deployment

### 1. Run the Deployment Script

```bash
# Make deployment script executable
chmod +x deploy.sh

# Run deployment (requires sudo)
sudo ./deploy.sh
```

### 2. Manual Deployment Steps

If you prefer manual deployment:

#### Step 1: Create Project Directory
```bash
sudo mkdir -p /var/www/laboratorios-crub
sudo mkdir -p /var/www/laboratorios-crub/logs
sudo mkdir -p /var/www/laboratorios-crub/instance
```

#### Step 2: Copy Project Files
```bash
# Copy all files except development artifacts
sudo rsync -av --exclude='__pycache__' \
              --exclude='*.pyc' \
              --exclude='.git' \
              --exclude='instance/laboratorios.db' \
              --exclude='logs/*.log' \
              --exclude='.env' \
              ./ /var/www/laboratorios-crub/
```

#### Step 3: Setup Python Environment
```bash
cd /var/www/laboratorios-crub
sudo python3 -m venv venv
sudo venv/bin/pip install -r requirements.txt
```

#### Step 4: Configure Environment
```bash
# Copy environment template
sudo cp .env.production.template .env

# Edit with your production values
sudo nano .env
```

#### Step 5: Set Permissions
```bash
sudo chown -R www-data:www-data /var/www/laboratorios-crub
sudo chmod -R 755 /var/www/laboratorios-crub
sudo chmod 600 /var/www/laboratorios-crub/.env
```

#### Step 6: Initialize Database
```bash
cd /var/www/laboratorios-crub
source venv/bin/activate
export FLASK_APP=wsgi.py
export FLASK_ENV=production

python -c "
from app import create_app
from config import ProductionConfig
app = create_app(ProductionConfig)
with app.app_context():
    from app.models.models import db
    db.create_all()
"
```

## Apache Configuration

### 1. Enable Required Modules
```bash
sudo a2enmod wsgi
sudo a2enmod headers
sudo a2enmod expires
```

### 2. Add Virtual Host Configuration

Add the following to your Apache virtual host configuration:

```apache
# Include the laboratorios-crub configuration
Include /var/www/laboratorios-crub/apache.conf
```

Or manually add the configuration from `apache.conf` to your virtual host.

### 3. Restart Apache
```bash
sudo systemctl restart apache2
```

## Environment Configuration

### Required Environment Variables

Edit `/var/www/laboratorios-crub/.env`:

```env
# Environment
FLASK_ENV=production
APPLICATION_ROOT=/laboratorios-crub

# Server Configuration
SERVER_NAME=your-domain.com
PREFERRED_URL_SCHEME=https

# Security
SECRET_KEY=your-super-secret-production-key-here

# Database
DATABASE_URI=sqlite:///instance/laboratorios.db

# Quién puede entrar: los DNI habilitados, separados por coma. Keycloak dice si
# la persona es quien dice ser; esta lista dice si además puede usar esta
# aplicación. Se relee en cada ingreso, sin reiniciar el servicio.
# No hay credenciales de administrador acá: no existen contraseñas locales.
USUARIOS_AUTORIZADOS=12345678,23456789

# Sesión y freno a los intentos fallidos
SESION_HORAS=12
INTENTOS_MAX=8
ESPERA_SEGUNDOS=300

# Keycloak Configuration
KEYCLOAK_SERVER_URL=https://your-keycloak-server.com
KEYCLOAK_REALM=CRUB
KEYCLOAK_CLIENT_ID=laboratorios-crub-client
KEYCLOAK_CLIENT_SECRET=your-keycloak-client-secret

# Role Mapping
KEYCLOAK_ADMIN_ROLE=app_admin
KEYCLOAK_TECNICO_ROLE=laboratorista
```

## Testing the Deployment

### 1. Run Deployment Tests
```bash
python scripts/test_deployment.py
```

### 2. Check Application Access
Visit: `https://your-domain.com/laboratorios-crub`

### 3. Monitor Logs
```bash
# Application logs (una linea JSON por evento; con jq se leen comodos)
tail -f /var/www/laboratorios-crub/logs/app_structured.log

# Solo el mensaje y el nivel, si no hace falta el contexto completo:
tail -f /var/www/laboratorios-crub/logs/app_structured.log | jq -r '"\(.level) \(.message)"'

# Rastro de auditoria (quien hizo que) y eventos de seguridad:
tail -f /var/www/laboratorios-crub/logs/audit_structured.log
tail -f /var/www/laboratorios-crub/logs/security_structured.log

# Apache error logs
tail -f /var/log/apache2/error.log

# Apache access logs
tail -f /var/log/apache2/access.log
```

## Troubleshooting

### Common Issues

1. **Permission Denied Errors**
   ```bash
   sudo chown -R www-data:www-data /var/www/laboratorios-crub
   sudo chmod -R 755 /var/www/laboratorios-crub
   ```

2. **Module Import Errors**
   ```bash
   cd /var/www/laboratorios-crub
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Database Connection Issues**
   - Check DATABASE_URI in .env
   - Ensure database file permissions are correct
   - Verify database initialization

4. **Static Files Not Loading**
   - Check Apache Alias configuration
   - Verify static file permissions
   - Clear browser cache

### Log Locations
- Application logs: `/var/www/laboratorios-crub/logs/`
- Apache logs: `/var/log/apache2/`
- Python errors: Check Apache error log

## Security Considerations

- Use strong SECRET_KEY (la app se niega a arrancar en producción con un placeholder)
- Mantener `USUARIOS_AUTORIZADOS` al día: sacar a quien ya no corresponda
- Enable HTTPS in production
- Regularly update dependencies
- Monitor logs for security issues
- Backup database regularly

No hay contraseña de administrador que cambiar: la aplicación no guarda ninguna
credencial. Todo el acceso pasa por Keycloak.

## Keycloak Integration

La aplicación pide usuario y contraseña en su propio formulario y los cambia por
un token en Keycloak (`grant_type=password`), igual que Reportes DAE. **No hay
flujo de redirección OIDC**, así que no hay que configurar redirect URIs ni
post-logout URIs en el cliente de Keycloak.

Lo que sí tiene que estar en el cliente del realm:

- **Direct access grants** habilitado (es el `grant_type=password`).
- El `KEYCLOAK_CLIENT_SECRET` correspondiente, si el cliente es confidencial.
- Los roles `app_admin` y `laboratorista` asignados a quien corresponda: el rol
  del realm es el que decide si alguien entra como administrador o como técnico.
  Quien no tenga ninguno de los dos entra como técnico.

Dar acceso son dos pasos: que la persona tenga cuenta en el realm del CRUB, y
que su DNI esté en `USUARIOS_AUTORIZADOS`.

Las contraseñas no se administran acá. Quien la olvidó la restablece en las
pantallas de cuenta de Huayca (`URL_RESET_PASSWORD`).

## Maintenance

### Updating the Application

`deploy.sh` es para instalar de cero. Sobre una instalación que ya tiene datos
se usa `scripts/actualizar_servidor.sh`, desde un clon del repositorio en el
servidor (no desde `/var/www/laboratorios-crub`):

```bash
git clone -b feature/prod https://github.com/Ignatius32/laboratorios_crub.git
cd laboratorios_crub          # las veces siguientes: git pull
sudo bash scripts/actualizar_servidor.sh --verificar   # no cambia nada
sudo bash scripts/actualizar_servidor.sh
```

Qué hace, en orden:

1. Comprueba el `.env` del servidor (`SECRET_KEY`, `USUARIOS_AUTORIZADOS`,
   Keycloak) y que las dependencias existan para el Python del servidor. Si algo
   falta, se detiene sin haber tocado nada.
2. Respalda el código, el `.env` y la base en `/var/backups/laboratorios-crub/`.
3. Copia el código, arma un venv nuevo y migra la base
   (`scripts/preparar_base.py`).
4. Recarga sólo esta aplicación (`touch wsgi.py`), sin reiniciar Apache, y
   consulta la pantalla de ingreso.

Si algo falla a partir del paso 3, repone solo la versión anterior con la base
como estaba.

### Database Backups
```bash
# Backup SQLite database
cp /var/www/laboratorios-crub/instance/laboratorios.db /backup/location/

# Or use the application's built-in backup if available
```

## Support

For deployment issues:
1. Check logs first
2. Verify environment configuration
3. Test with deployment script
4. Review Apache configuration
5. Check file permissions

The application includes comprehensive logging to help diagnose issues.
