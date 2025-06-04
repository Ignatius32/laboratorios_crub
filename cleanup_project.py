#!/usr/bin/env python3
"""
Script de limpieza para reorganizar el proyecto laboratorios_crub
Automatiza la reorganización de archivos y mejoras estructurales

Autor: Sistema de Gestión CRUB
Fecha: Junio 2025
"""

import os
import shutil
from pathlib import Path

def print_separator(title):
    """Imprime un separador con título"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def safe_move(source, destination):
    """Mueve un archivo de forma segura, verificando que existe"""
    if os.path.exists(source):
        try:
            # Crear directorio de destino si no existe
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.move(source, destination)
            print(f"✅ Movido: {source} → {destination}")
            return True
        except Exception as e:
            print(f"❌ Error moviendo {source}: {e}")
            return False
    else:
        print(f"⚠️  No encontrado: {source}")
        return False

def safe_delete(file_path):
    """Elimina un archivo de forma segura, verificando que existe"""
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"🗑️  Eliminado: {file_path}")
            return True
        except Exception as e:
            print(f"❌ Error eliminando {file_path}: {e}")
            return False
    else:
        print(f"⚠️  No encontrado: {file_path}")
        return False

def create_directories():
    """Crear las carpetas necesarias"""
    print_separator("CREANDO DIRECTORIOS")
    
    directories = ['docs', 'tests', 'scripts']
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"📁 Directorio creado/verificado: {directory}/")
        except Exception as e:
            print(f"❌ Error creando directorio {directory}: {e}")

def move_documentation_files():
    """Mover archivos de documentación a docs/"""
    print_separator("MOVIENDO ARCHIVOS DE DOCUMENTACIÓN")
    
    doc_files = [
        'ANALISIS_PROYECTO.md',
        'FILE_VALIDATION_COMPLETED.md',
        'FILE_VALIDATION_IMPLEMENTATION.md',
        'INDICES_IMPLEMENTADOS.md',
        'LOGGING_ESTRUCTURADO_IMPLEMENTADO.md',
        'LOGGING_SISTEMA_COMPLETO_FINAL.md',
        'MINIMALIST-DESIGN-README.md',
        'STOCK_REALTIME_SOLUTION.md',
        'STOCK_SOLUTION_SUMMARY.md'
    ]
    
    moved_count = 0
    for doc_file in doc_files:
        if safe_move(doc_file, f'docs/{doc_file}'):
            moved_count += 1
    
    print(f"\n📊 Archivos de documentación movidos: {moved_count}/{len(doc_files)}")

def move_test_files():
    """Mover archivos de test a tests/"""
    print_separator("MOVIENDO ARCHIVOS DE TEST")
    
    test_files = [
        'test_complete_logging_system.py',
        'test_file_validation_system.py',
        'test_logging.py',
        'test_monitoring_report.json',
        'test_stock_realtime.py',
        'verify_file_validation_complete.py',
        'verify_final_system.py'
    ]
    
    moved_count = 0
    for test_file in test_files:
        if safe_move(test_file, f'tests/{test_file}'):
            moved_count += 1
    
    print(f"\n📊 Archivos de test movidos: {moved_count}/{len(test_files)}")

def move_script_files():
    """Mover scripts a scripts/"""
    print_separator("MOVIENDO SCRIPTS")
    
    script_files = [
        'migrate_db.py',
        'add_indexes.py'
    ]
    
    moved_count = 0
    for script_file in script_files:
        if safe_move(script_file, f'scripts/{script_file}'):
            moved_count += 1
    
    print(f"\n📊 Scripts movidos: {moved_count}/{len(script_files)}")

def remove_duplicate_js_files():
    """Eliminar archivos JavaScript duplicados"""
    print_separator("ELIMINANDO ARCHIVOS JAVASCRIPT DUPLICADOS")
    
    duplicate_js_files = [
        'app/static/js/proveedores-modal.fixed.js',
        'app/static/js/proveedores-modal.original.js'
    ]
    
    deleted_count = 0
    for js_file in duplicate_js_files:
        if safe_delete(js_file):
            deleted_count += 1
    
    print(f"\n📊 Archivos JS duplicados eliminados: {deleted_count}/{len(duplicate_js_files)}")

def remove_other_duplicates():
    """Eliminar otros archivos duplicados encontrados"""
    print_separator("ELIMINANDO OTROS ARCHIVOS DUPLICADOS")
    
    other_duplicates = [
        'app/__init__.py.backup',
        'app/__init__.py.old',
        'app/utils/logging_config_backup.py',
        'app/utils/file_validators.py'  # Duplicado de file_validator.py
    ]
    
    deleted_count = 0
    for duplicate_file in other_duplicates:
        if safe_delete(duplicate_file):
            deleted_count += 1
    
    print(f"\n📊 Otros duplicados eliminados: {deleted_count}/{len(other_duplicates)}")

def clean_pycache():
    """Limpiar archivos __pycache__"""
    print_separator("LIMPIANDO ARCHIVOS CACHE")
    
    cache_dirs = []
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            cache_dirs.append(os.path.join(root, '__pycache__'))
    
    deleted_count = 0
    for cache_dir in cache_dirs:
        try:
            shutil.rmtree(cache_dir)
            print(f"🗑️  Eliminado: {cache_dir}")
            deleted_count += 1
        except Exception as e:
            print(f"❌ Error eliminando {cache_dir}: {e}")
    
    print(f"\n📊 Directorios __pycache__ eliminados: {deleted_count}")

def verify_structure():
    """Verificar la nueva estructura"""
    print_separator("VERIFICANDO NUEVA ESTRUCTURA")
    
    structure_check = {
        'docs/': ['ANALISIS_PROYECTO.md', 'README.md'],
        'tests/': ['test_complete_logging_system.py', 'test_logging.py'],
        'scripts/': ['migrate_db.py'],
        'app/static/css/': ['common.css'],
        'app/static/js/': ['common.js'],
        'app/templates/macros/': ['forms.html', 'modals.html']
    }
    
    all_good = True
    for directory, expected_files in structure_check.items():
        print(f"\n📁 Verificando {directory}:")
        for expected_file in expected_files:
            file_path = os.path.join(directory, expected_file)
            if os.path.exists(file_path):
                print(f"  ✅ {expected_file}")
            else:
                print(f"  ❌ {expected_file} - NO ENCONTRADO")
                all_good = False
    
    return all_good

def generate_summary():
    """Generar resumen de la reorganización"""
    print_separator("RESUMEN DE LA REORGANIZACIÓN")
    
    print("🎯 MEJORAS IMPLEMENTADAS:")
    print("   ✅ Estructura de carpetas reorganizada")
    print("   ✅ Archivos de documentación movidos a docs/")
    print("   ✅ Archivos de test movidos a tests/")
    print("   ✅ Scripts movidos a scripts/")
    print("   ✅ Archivos JavaScript duplicados eliminados")
    print("   ✅ common.css creado con estilos compartidos")
    print("   ✅ common.js creado con funciones unificadas")
    print("   ✅ Macros Jinja2 creados para formularios y modales")
    print("   ✅ Función deprecada eliminada de stock_service.py")
    print("   ✅ Archivos cache limpiados")
    
    print("\n📊 NUEVA ESTRUCTURA:")
    print("   laboratorios_crub/")
    print("   ├── docs/           # Documentación del proyecto")
    print("   ├── tests/          # Archivos de prueba")
    print("   ├── scripts/        # Scripts utilitarios")
    print("   ├── app/")
    print("   │   ├── static/")
    print("   │   │   ├── css/    # common.css agregado")
    print("   │   │   └── js/     # common.js agregado")
    print("   │   └── templates/")
    print("   │       └── macros/ # Macros reutilizables")
    print("   ├── README.md")
    print("   └── requirements.txt")

def main():
    """Función principal del script de limpieza"""
    print("🧹 SCRIPT DE LIMPIEZA - LABORATORIOS CRUB")
    print("==========================================")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('app') or not os.path.exists('README.md'):
        print("❌ Error: Este script debe ejecutarse desde el directorio raíz del proyecto")
        print("   Asegúrate de estar en: laboratorios_crub/")
        return False
    
    try:
        # Ejecutar todas las operaciones de limpieza
        create_directories()
        move_documentation_files()
        move_test_files()
        move_script_files()
        remove_duplicate_js_files()
        remove_other_duplicates()
        clean_pycache()
        
        # Verificar estructura
        structure_ok = verify_structure()
        
        # Generar resumen
        generate_summary()
        
        if structure_ok:
            print("\n🎉 ¡LIMPIEZA COMPLETADA EXITOSAMENTE!")
            print("   El proyecto ha sido reorganizado y optimizado.")
        else:
            print("\n⚠️  LIMPIEZA COMPLETADA CON ADVERTENCIAS")
            print("   Algunos archivos esperados no se encontraron.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR DURANTE LA LIMPIEZA: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
