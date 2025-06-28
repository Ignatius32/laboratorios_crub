#!/bin/bash
"""
Deployment script for Laboratorios CRUB on Apache
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying Laboratorios CRUB to Apache${NC}"

# Configuration
PROJECT_NAME="laboratorios-crub"
APACHE_DIR="/var/www/${PROJECT_NAME}"
VENV_DIR="${APACHE_DIR}/venv"
SERVICE_USER="www-data"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${YELLOW}📁 Creating project directory...${NC}"
mkdir -p ${APACHE_DIR}
mkdir -p ${APACHE_DIR}/logs
mkdir -p ${APACHE_DIR}/instance

echo -e "${YELLOW}📦 Copying project files...${NC}"
# Copy all files except development-specific ones
rsync -av --exclude='__pycache__' \
          --exclude='*.pyc' \
          --exclude='.git' \
          --exclude='instance/laboratorios.db' \
          --exclude='logs/*.log' \
          --exclude='.env' \
          ./ ${APACHE_DIR}/

echo -e "${YELLOW}🐍 Setting up Python virtual environment...${NC}"
python3 -m venv ${VENV_DIR}
source ${VENV_DIR}/bin/activate
pip install --upgrade pip
pip install -r ${APACHE_DIR}/requirements.txt

echo -e "${YELLOW}⚙️ Setting up environment configuration...${NC}"
if [ ! -f "${APACHE_DIR}/.env" ]; then
    cp ${APACHE_DIR}/.env.production.template ${APACHE_DIR}/.env
    echo -e "${YELLOW}📝 Please edit ${APACHE_DIR}/.env with your production values${NC}"
fi

echo -e "${YELLOW}🔐 Setting permissions...${NC}"
chown -R ${SERVICE_USER}:${SERVICE_USER} ${APACHE_DIR}
chmod -R 755 ${APACHE_DIR}
chmod 644 ${APACHE_DIR}/wsgi.py
chmod 600 ${APACHE_DIR}/.env
chmod 755 ${APACHE_DIR}/logs
chmod 755 ${APACHE_DIR}/instance

echo -e "${YELLOW}🗄️ Setting up database...${NC}"
cd ${APACHE_DIR}
source ${VENV_DIR}/bin/activate
export FLASK_APP=wsgi.py
export FLASK_ENV=production

# Initialize database
python -c "
from app import create_app
from config import ProductionConfig
app = create_app(ProductionConfig)
with app.app_context():
    from app.models.models import db
    db.create_all()
    print('Database initialized successfully')
"

echo -e "${GREEN}✅ Deployment completed!${NC}"
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Edit ${APACHE_DIR}/.env with your production configuration"
echo "2. Add the Apache configuration to your virtual host:"
echo "   Include ${APACHE_DIR}/apache.conf"
echo "3. Enable required Apache modules:"
echo "   sudo a2enmod wsgi headers expires"
echo "4. Restart Apache:"
echo "   sudo systemctl restart apache2"
echo "5. Check logs for any issues:"
echo "   tail -f ${APACHE_DIR}/logs/app.log"
echo "   tail -f /var/log/apache2/error.log"

echo -e "${GREEN}🎉 Your application will be available at: https://your-domain.com/laboratorios-crub${NC}"
