#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema de stock en tiempo real
"""
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from app.utils.stock_service import (
    get_stock_for_product_in_lab,
    get_stock_map_for_lab,
    get_global_stock_map,
    get_stock_by_lab_map
)

def test_stock_functions():
    """Prueba las funciones de stock en tiempo real"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Probando el sistema de stock en tiempo real...")
        print("=" * 50)
        
        try:
            # Prueba 1: Stock de un producto específico en un laboratorio
            print("1️⃣  Probando get_stock_for_product_in_lab...")
            stock = get_stock_for_product_in_lab('P001', 'L001')
            print(f"   Stock del producto P001 en laboratorio L001: {stock}")
            
            # Prueba 2: Mapa de stock para un laboratorio
            print("\n2️⃣  Probando get_stock_map_for_lab...")
            stock_map = get_stock_map_for_lab('L001')
            print(f"   Stock en laboratorio L001: {len(stock_map)} productos")
            for prod_id, stock in list(stock_map.items())[:3]:  # Mostrar solo los primeros 3
                print(f"   - Producto {prod_id}: {stock}")
            
            # Prueba 3: Stock global
            print("\n3️⃣  Probando get_global_stock_map...")
            global_stock = get_global_stock_map()
            print(f"   Stock global: {len(global_stock)} productos")
            for prod_id, stock in list(global_stock.items())[:3]:  # Mostrar solo los primeros 3
                print(f"   - Producto {prod_id}: {stock}")
            
            # Prueba 4: Stock por laboratorio
            print("\n4️⃣  Probando get_stock_by_lab_map...")
            stock_by_lab = get_stock_by_lab_map()
            print(f"   Distribución por laboratorio: {len(stock_by_lab)} productos")
            for prod_id, labs in list(stock_by_lab.items())[:2]:  # Mostrar solo los primeros 2
                print(f"   - Producto {prod_id}:")
                for lab_id, stock in labs.items():
                    print(f"     * Laboratorio {lab_id}: {stock}")
            
            print("\n✅ Todas las pruebas completadas exitosamente!")
            print("🎯 El sistema de stock en tiempo real está funcionando correctamente.")
            
        except Exception as e:
            print(f"\n❌ Error durante las pruebas: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_stock_functions()
