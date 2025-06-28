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

# Admin Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-admin-password

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
python test_deployment.py
```

### 2. Check Application Access
Visit: `https://your-domain.com/laboratorios-crub`

### 3. Monitor Logs
```bash
# Application logs
tail -f /var/www/laboratorios-crub/logs/app.log

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

- Change default admin password
- Use strong SECRET_KEY
- Enable HTTPS in production
- Regularly update dependencies
- Monitor logs for security issues
- Backup database regularly

## Keycloak Integration

The application supports Keycloak SSO. The redirect URIs are automatically configured based on your domain:

- Redirect URI: `https://your-domain.com/laboratorios-crub/auth/callback`
- Post-logout URI: `https://your-domain.com/laboratorios-crub/`

Configure these URIs in your Keycloak client settings.

## Maintenance

### Updating the Application
1. Backup database and .env file
2. Pull new code to deployment directory
3. Update dependencies if needed
4. Restart Apache
5. Test functionality

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
