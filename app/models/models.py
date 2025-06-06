from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# Association table for the many-to-many relationship between users and laboratories
user_laboratorio = db.Table('user_laboratorio',
    db.Column('usuario_id', db.String(10), db.ForeignKey('usuario.idUsuario'), primary_key=True),
    db.Column('laboratorio_id', db.String(10), db.ForeignKey('laboratorio.idLaboratorio'), primary_key=True)
)

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'
    idUsuario = db.Column(db.String(10), primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefono = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='tecnico')  # 'admin' or 'tecnico'
    password_reset_token = db.Column(db.String(100), nullable=True)
    password_reset_expiration = db.Column(db.DateTime, nullable=True)
    
    # Relationship with laboratories - many-to-many
    laboratorios = db.relationship('Laboratorio', secondary=user_laboratorio, 
                                   backref=db.backref('usuarios', lazy='dynamic'))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        # Clear any reset tokens after password set
        self.password_reset_token = None
        self.password_reset_expiration = None
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return self.idUsuario
        
    def generate_reset_token(self):
        """Generate a unique token for password reset"""
        import secrets
        import datetime
        
        # Generate a secure token
        token = secrets.token_urlsafe(32)
        self.password_reset_token = token
        
        # Set expiration to 24 hours from now
        self.password_reset_expiration = datetime.datetime.now() + datetime.timedelta(hours=24)
        
        return token
        
    def is_reset_token_valid(self, token):
        """Check if the reset token is valid"""
        import datetime
        
        if not self.password_reset_token or self.password_reset_token != token:
            return False
            
        if not self.password_reset_expiration or self.password_reset_expiration < datetime.datetime.now():
            return False
            
        return True

class Laboratorio(db.Model):
    __tablename__ = 'laboratorio'
    idLaboratorio = db.Column(db.String(10), primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    laboratorio_folder_id = db.Column(db.String(100), nullable=True)
    movimiento_folder_id = db.Column(db.String(100), nullable=True)
    
    # Relationships
    movimientos = db.relationship('Movimiento', backref='laboratorio', lazy=True)    # Método para obtener el stock de un producto específico en este laboratorio (en tiempo real)
    def get_stock_producto(self, id_producto):
        from app.utils.stock_service import get_stock_for_product_in_lab
        return get_stock_for_product_in_lab(id_producto, self.idLaboratorio)

class Proveedor(db.Model):
    __tablename__ = 'proveedor'
    idProveedor = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200), nullable=True)
    telefono = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    cuit = db.Column(db.String(13), unique=True, nullable=False)
    
    # Relación con movimientos
    movimientos = db.relationship('Movimiento', backref='proveedor', lazy=True)
    
    def __repr__(self):
        return f'<Proveedor {self.nombre} ({self.cuit})>'

class Producto(db.Model):
    __tablename__ = 'producto'
    idProducto = db.Column(db.String(10), primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    tipoProducto = db.Column(db.String(50), nullable=False)
    estadoFisico = db.Column(db.String(20), nullable=False)
    controlSedronar = db.Column(db.Boolean, default=False)
    urlFichaSeguridad = db.Column(db.String(200), nullable=True)
    stockMinimo = db.Column(db.Float, nullable=True, default=0)
    marca = db.Column(db.String(100), nullable=True)
    
    # Relationships
    movimientos = db.relationship('Movimiento', backref='producto', lazy=True)    # Calcular el stock total en todos los laboratorios (en tiempo real)
    @property
    def stock_total(self):
        from app.utils.stock_service import get_global_stock_map
        stock_map = get_global_stock_map([self.idProducto])
        return stock_map.get(self.idProducto, 0)
    
    # Calcular el stock por laboratorio (en tiempo real)
    def stock_en_laboratorio(self, lab_id):
        from app.utils.stock_service import get_stock_for_product_in_lab
        return get_stock_for_product_in_lab(self.idProducto, lab_id)

class Movimiento(db.Model):
    __tablename__ = 'movimiento'
    idMovimiento = db.Column(db.String(10), primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    tipoMovimiento = db.Column(db.String(20), nullable=False)  # 'ingreso', 'compra', 'uso', 'transferencia'
    cantidad = db.Column(db.Float, nullable=False)
    unidadMedida = db.Column(db.String(10), nullable=False)
      # New fields for the specialized movement types
    tipoDocumento = db.Column(db.String(20), nullable=True)  # 'factura' or 'remito' for 'compra' type
    numeroDocumento = db.Column(db.String(50), nullable=True)  # Number of the invoice or receipt
    urlDocumento = db.Column(db.String(255), nullable=True)  # URL to the stored document in Google Drive
    laboratorioDestino = db.Column(db.String(10), nullable=True)  # For 'transferencia' type
    fechaFactura = db.Column(db.Date, nullable=True)  # Date of the invoice for 'compra' type
    cuitProveedor = db.Column(db.String(13), nullable=True)  # Legacy field, kept for compatibility    # Foreign keys with indexes for better performance
    idProducto = db.Column(db.String(10), db.ForeignKey('producto.idProducto'), nullable=False, index=True)
    idLaboratorio = db.Column(db.String(10), db.ForeignKey('laboratorio.idLaboratorio'), nullable=False, index=True)
    idProveedor = db.Column(db.Integer, db.ForeignKey('proveedor.idProveedor'), nullable=True, index=True)

    # Composite indexes for common queries
    __table_args__ = (
        db.Index('idx_movimiento_lab_producto', 'idLaboratorio', 'idProducto'),
        db.Index('idx_movimiento_lab_timestamp', 'idLaboratorio', 'timestamp'),
        db.Index('idx_movimiento_producto_timestamp', 'idProducto', 'timestamp'),
        db.Index('idx_movimiento_tipo_timestamp', 'tipoMovimiento', 'timestamp'),
    )

class Stock(db.Model):
    __tablename__ = 'stock'
    idStock = db.Column(db.Integer, primary_key=True)
    idProducto = db.Column(db.String(10), db.ForeignKey('producto.idProducto'), nullable=False, index=True)
    idLaboratorio = db.Column(db.String(10), db.ForeignKey('laboratorio.idLaboratorio'), nullable=False, index=True)
    cantidad = db.Column(db.Float, nullable=False)
    
    producto = db.relationship('Producto', backref='stocks')
    laboratorio = db.relationship('Laboratorio', backref='stocks')
    
    # Composite index for common queries
    __table_args__ = (
        db.Index('idx_stock_lab_producto', 'idLaboratorio', 'idProducto'),
        # Unique constraint to prevent duplicate stock entries
        db.UniqueConstraint('idProducto', 'idLaboratorio', name='unique_producto_laboratorio'),
    )