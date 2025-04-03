# Sistema de Gestión de Laboratorios CRUB

Sistema web para la gestión de inventarios y control de stock en los laboratorios del Centro Regional Universitario Bariloche (CRUB) de la Universidad Nacional del Comahue.

## Descripción

Esta aplicación web permite administrar los laboratorios de la institución, los productos químicos y materiales que contienen, y registrar los movimientos de entrada y salida para mantener un control de inventario actualizado en tiempo real.

El sistema se ha desarrollado con un enfoque en la usabilidad y la seguridad, permitiendo la gestión de múltiples laboratorios con diferentes técnicos asignados, y proporcionando diferentes niveles de acceso según el rol del usuario.

## Características principales

- **Gestión de usuarios**: Administradores y técnicos con diferentes niveles de acceso
- **Administración de laboratorios**: Creación y gestión de múltiples laboratorios
- **Inventario de productos**: Registro detallado de reactivos y materiales
- **Control de stock**: Cálculo automático de existencias basado en movimientos
- **Seguimiento de movimientos**: Registro de entradas y salidas de productos
- **Fichas de seguridad**: Acceso a información de seguridad de productos químicos
- **Control SEDRONAR**: Marcado especial para productos controlados
- **Integración con Google Drive**: Almacenamiento de archivos asociados a cada laboratorio

## Tecnologías utilizadas

- **Backend**: Flask (Python)
- **ORM**: SQLAlchemy
- **Autenticación**: Flask-Login
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Base de datos**: SQLite (desarrollo) / configurable para producción
- **Integración**: Google Apps Script API para almacenamiento de archivos

## Requisitos

- Python 3.9 o superior
- Pip (gestor de paquetes de Python)
- Navegador web moderno
- Conexión a Internet (para algunas características como la integración con Google Drive)

## Instalación

1. Clonar el repositorio:
```bash
git clone [URL_DEL_REPOSITORIO]
cd laboratorios_crub
```

2. Crear un entorno virtual e instalar las dependencias:
```bash
python -m venv venv
# En Windows
venv\Scripts\activate
# En Linux/Mac
source venv/bin/activate
pip install -r requirements.txt
```

3. Configurar las variables de entorno:
Crear un archivo `.env` en la raíz del proyecto con el siguiente contenido:
```
SECRET_KEY=tu_clave_secreta
ADMIN_USERNAME=admin
ADMIN_PASSWORD=contraseña_segura
GOOGLE_SCRIPT_URL=url_de_tu_script_de_google
GOOGLE_DRIVE_SECURE_TOKEN=tu_token_seguro
```

4. Inicializar la base de datos:
```bash
flask db init
flask db migrate -m "Inicialización de la base de datos"
flask db upgrade
```

5. Ejecutar la aplicación:
```bash
python run.py
```

La aplicación estará disponible en `http://localhost:5000`

## Estructura de usuarios y permisos

El sistema tiene dos tipos de usuarios:

- **Administradores**: Acceso completo a todas las funcionalidades del sistema, incluyendo la gestión de usuarios y laboratorios.
- **Técnicos**: Acceso limitado a los laboratorios asignados, pueden gestionar productos y movimientos.

## Integración con Google Drive

La aplicación integra con Google Drive para la gestión de archivos asociados a cada laboratorio. Esta integración se realiza a través de Google Apps Script, que se despliega como un servicio web.

Para configurar esta integración:

1. Implementar el script `app.gs` como una Aplicación Web en Google Apps Script
2. Configurar el servicio con acceso de ejecución como "Cualquier persona, incluso anónima"
3. Copiar la URL de implementación y el token seguro en el archivo `.env`

## Contribución

Para contribuir a este proyecto:

1. Hacer fork del repositorio
2. Crear una nueva rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Realizar los cambios y commitear (`git commit -am 'Añade nueva funcionalidad'`)
4. Hacer push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear un Pull Request

## Licencia

Este proyecto está licenciado bajo [Insertar tipo de licencia aquí]

## Contacto

Para más información o soporte, contactar a [tu-email@ejemplo.com]