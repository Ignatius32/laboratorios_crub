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
    
    # Relationship with laboratories - many-to-many
    laboratorios = db.relationship('Laboratorio', secondary=user_laboratorio, 
                                   backref=db.backref('usuarios', lazy='dynamic'))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return self.idUsuario

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
    productos = db.relationship('Producto', backref='laboratorio', lazy=True)
    movimientos = db.relationship('Movimiento', backref='laboratorio', lazy=True)

class Producto(db.Model):
    __tablename__ = 'producto'
    idProducto = db.Column(db.String(10), primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    tipoProducto = db.Column(db.String(50), nullable=False)
    estadoFisico = db.Column(db.String(20), nullable=False)
    controlSedronar = db.Column(db.Boolean, default=False)
    urlFichaSeguridad = db.Column(db.String(200), nullable=True)
    
    # Foreign key
    idLaboratorio = db.Column(db.String(10), db.ForeignKey('laboratorio.idLaboratorio'), nullable=False)
    
    # Relationships
    movimientos = db.relationship('Movimiento', backref='producto', lazy=True)
    
    # Calculate current stock based on movements
    @property
    def stock_actual(self):
        ingresos = sum(m.cantidad for m in self.movimientos if m.tipoMovimiento == 'ingreso')
        egresos = sum(m.cantidad for m in self.movimientos if m.tipoMovimiento == 'egreso')
        return ingresos - egresos

class Movimiento(db.Model):
    __tablename__ = 'movimiento'
    idMovimiento = db.Column(db.String(10), primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    tipoMovimiento = db.Column(db.String(20), nullable=False)  # 'ingreso' or 'egreso'
    cantidad = db.Column(db.Float, nullable=False)
    unidadMedida = db.Column(db.String(10), nullable=False)
    
    # Foreign keys
    idProducto = db.Column(db.String(10), db.ForeignKey('producto.idProducto'), nullable=False)
    idLaboratorio = db.Column(db.String(10), db.ForeignKey('laboratorio.idLaboratorio'), nullable=False)