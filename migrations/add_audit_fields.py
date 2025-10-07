"""
Script de migración para agregar campos de auditoría
Agrega created_by y created_at a las tablas producto y movimiento
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models.models import db
from config import DevelopmentConfig
from sqlalchemy import text

def add_audit_fields():
    app = create_app(DevelopmentConfig)
    
    with app.app_context():
        try:
            print("Agregando campos de auditoría...")
            
            # Agregar campos a la tabla producto
            print("\n1. Agregando campos a la tabla 'producto'...")
            try:
                db.session.execute(text("""
                    ALTER TABLE producto 
                    ADD COLUMN created_by VARCHAR(10);
                """))
                print("   ✓ Campo created_by agregado a producto")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("   → Campo created_by ya existe en producto")
                else:
                    raise
            
            try:
                db.session.execute(text("""
                    ALTER TABLE producto 
                    ADD COLUMN created_at DATETIME;
                """))
                print("   ✓ Campo created_at agregado a producto")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("   → Campo created_at ya existe en producto")
                else:
                    raise
            
            # Agregar campo a la tabla movimiento
            print("\n2. Agregando campo a la tabla 'movimiento'...")
            try:
                db.session.execute(text("""
                    ALTER TABLE movimiento 
                    ADD COLUMN created_by VARCHAR(10);
                """))
                print("   ✓ Campo created_by agregado a movimiento")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("   → Campo created_by ya existe en movimiento")
                else:
                    raise
            
            # Agregar foreign keys (SQLite no soporta ALTER para agregar FK, así que solo comentamos)
            print("\n3. Configurando relaciones...")
            print("   → Las foreign keys se configuran a través del ORM de SQLAlchemy")
            
            db.session.commit()
            print("\n✅ Migración completada exitosamente!")
            print("\nNota: Los registros existentes tendrán created_by = NULL")
            print("Los nuevos registros se crearán con el usuario actual.")
            
        except Exception as e:
            print(f"\n❌ Error durante la migración: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    add_audit_fields()
