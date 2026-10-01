#!/usr/bin/env python3
"""
Script de testing para verificar la implementación del modal de fichas de seguridad
Verifica que todos los archivos necesarios estén en su lugar y tengan el contenido correcto
"""

import os
import sys
from pathlib import Path

def check_file_exists(file_path, description):
    """Verifica si un archivo existe"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - NO ENCONTRADO")
        return False

def check_content_in_file(file_path, content_check, description):
    """Verifica si cierto contenido existe en un archivo"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if content_check in content:
                print(f"✅ {description}")
                return True
            else:
                print(f"❌ {description} - CONTENIDO NO ENCONTRADO")
                return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    print("🔍 Verificando implementación del Modal de Fichas de Seguridad...")
    print("=" * 60)
    
    base_path = Path(__file__).parent
    all_checks_passed = True
    
    # 1. Verificar archivos CSS
    css_file = base_path / "app" / "static" / "css" / "fichas-seguridad.css"
    if check_file_exists(css_file, "Archivo CSS de fichas de seguridad"):
        all_checks_passed &= check_content_in_file(
            css_file, 
            "#fichasSeguridadModal", 
            "CSS contiene estilos del modal"
        )
    else:
        all_checks_passed = False
    
    # 2. Verificar archivo de ejemplos JavaScript
    js_ejemplos = base_path / "app" / "static" / "js" / "fichas-seguridad-ejemplos.js"
    if check_file_exists(js_ejemplos, "Archivo JavaScript de ejemplos"):
        all_checks_passed &= check_content_in_file(
            js_ejemplos,
            "showFichaSeguridad",
            "JavaScript contiene función de ejemplo"
        )
    else:
        all_checks_passed = False
    
    # 3. Verificar template base
    base_template = base_path / "app" / "templates" / "base.html"
    if check_file_exists(base_template, "Template base"):
        checks = [
            ("fichasSeguridadModal", "Modal HTML incluido en base.html"),
            ("showFichaSeguridad", "Función JavaScript incluida"),
            ("fichas-seguridad.css", "CSS incluido en base.html")
        ]
        
        for content_check, description in checks:
            all_checks_passed &= check_content_in_file(
                base_template, content_check, description
            )
    else:
        all_checks_passed = False
    
    # 4. Verificar template de lista de productos
    list_template = base_path / "app" / "templates" / "tecnicos" / "productos" / "list.html"
    if check_file_exists(list_template, "Template de lista de productos"):
        checks = [
            ("mostrarFichaSeguridadDesdeUrl", "Botón de ficha en lista de productos"),
            ("Ficha Seguridad", "Columna de ficha de seguridad"),
            ("fas fa-shield-alt", "Icono de ficha de seguridad")
        ]
        
        for content_check, description in checks:
            all_checks_passed &= check_content_in_file(
                list_template, content_check, description
            )
    else:
        all_checks_passed = False
    
    # 5. Verificar template de vista de producto
    view_template = base_path / "app" / "templates" / "tecnicos" / "productos" / "view.html"
    if check_file_exists(view_template, "Template de vista de producto"):
        all_checks_passed &= check_content_in_file(
            view_template,
            "mostrarFichaSeguridadDesdeUrl",
            "Botón de ficha en vista de producto"
        )
    else:
        all_checks_passed = False
    
    # 6. Verificar documentación
    docs_file = base_path / "docs" / "FICHAS_SEGURIDAD_MODAL.md"
    if check_file_exists(docs_file, "Documentación del modal"):
        all_checks_passed &= check_content_in_file(
            docs_file,
            "showFichaSeguridad",
            "Documentación completa"
        )
    else:
        all_checks_passed = False
    
    # 7. Verificar modelo de datos
    models_file = base_path / "app" / "models" / "models.py"
    if check_file_exists(models_file, "Modelo de datos"):
        all_checks_passed &= check_content_in_file(
            models_file,
            "urlFichaSeguridad",
            "Campo urlFichaSeguridad en modelo Producto"
        )
    else:
        all_checks_passed = False
    
    print("\n" + "=" * 60)
    
    if all_checks_passed:
        print("🎉 ¡Implementación completada exitosamente!")
        print("\n📋 Pasos siguientes:")
        print("1. Verificar que el endpoint /descargar_archivo_drive/{driveId} esté funcionando")
        print("2. Configurar URLs de fichas de seguridad en la base de datos")
        print("3. Probar con archivos reales de Google Drive")
        print("4. Verificar permisos de acceso a los archivos")
        print("\n💡 Para probar:")
        print("- Incluye el archivo de ejemplos en tu template de testing")
        print("- Usa las funciones ejemploFichaDirecta(), ejemploFichaDesdeUrl(), etc.")
        
    else:
        print("⚠️  Algunos archivos o contenidos están faltando.")
        print("Revisa los elementos marcados con ❌ arriba.")
        
    print("\n🔧 Archivos creados/modificados:")
    print("- app/static/css/fichas-seguridad.css")
    print("- app/static/js/fichas-seguridad-ejemplos.js")
    print("- app/templates/base.html (modificado)")
    print("- app/templates/tecnicos/productos/list.html (modificado)")
    print("- app/templates/tecnicos/productos/view.html (modificado)")
    print("- docs/FICHAS_SEGURIDAD_MODAL.md")
    
    return all_checks_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
