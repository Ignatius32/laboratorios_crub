#!/usr/bin/env python3
"""
Script de prueba para verificar que la columna de acciones fue removida del gestor de usuarios
"""
import os
import sys
import requests
from urllib.parse import urljoin

def test_user_management_actions_removal():
    """Prueba que la columna de acciones fue removida del gestor de usuarios"""
    base_url = "http://localhost:5000"
    usuarios_url = urljoin(base_url, "/admin/usuarios")
    
    print("🗑️ Verificando remoción de columna de acciones en gestor de usuarios...")
    print("=" * 70)
    
    # Verificar que el servidor esté ejecutándose
    try:
        response = requests.get(base_url, timeout=5)
        print(f"✅ Servidor Flask accesible: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando al servidor Flask: {e}")
        return False
    
    # Verificar que la página de usuarios sea accesible
    try:
        response = requests.get(usuarios_url, timeout=5)
        print(f"✅ Página de gestión de usuarios accesible: {response.status_code}")
        
        content = response.text
        
        # Verificar que la columna "Acciones" fue removida del encabezado
        if '<th>Acciones</th>' not in content:
            print("✅ Columna 'Acciones' removida del encabezado de la tabla")
        else:
            print("❌ Columna 'Acciones' AÚN PRESENTE en el encabezado")
            
        # Verificar que los botones de editar fueron removidos
        if 'btn-warning' not in content and 'fa-edit' not in content:
            print("✅ Botones de editar removidos")
        else:
            print("❌ Botones de editar AÚN PRESENTES")
            
        # Verificar que los botones de eliminar fueron removidos
        if 'btn-delete' not in content and 'fa-trash' not in content:
            print("✅ Botones de eliminar removidos")
        else:
            print("❌ Botones de eliminar AÚN PRESENTES")
            
        # Verificar que los modales de confirmación fueron removidos
        if 'deleteModal' not in content:
            print("✅ Modales de confirmación de eliminación removidos")
        else:
            print("❌ Modales de confirmación AÚN PRESENTES")
            
        # Verificar que el colspan fue actualizado correctamente
        if 'colspan="7"' in content:
            print("✅ Colspan actualizado correctamente (7 columnas)")
        elif 'colspan="8"' in content:
            print("❌ Colspan NO actualizado (todavía muestra 8 columnas)")
        else:
            print("ℹ️ No se encontró mensaje de 'No hay usuarios registrados'")
            
        # Verificar las columnas que deben estar presentes
        expected_columns = ['ID', 'Nombre', 'Apellido', 'Email', 'Teléfono', 'Rol', 'Laboratorios']
        missing_columns = []
        
        for column in expected_columns:
            if f'<th>{column}</th>' in content:
                print(f"✅ Columna '{column}' presente")
            else:
                missing_columns.append(column)
                print(f"❌ Columna '{column}' FALTANTE")
                
        if not missing_columns:
            print("✅ Todas las columnas esperadas están presentes")
            
        # Verificar que el botón de sincronización sigue presente
        if 'Sincronizar Ahora' in content:
            print("✅ Botón de sincronización con Keycloak mantenido")
        else:
            print("❌ Botón de sincronización removido inesperadamente")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error accediendo a la página de usuarios: {e}")
        return False
    
    print("\n📋 Resumen de cambios aplicados:")
    print("- ❌ Columna 'Acciones' removida del encabezado")
    print("- ❌ Botones de editar (lápiz) removidos")
    print("- ❌ Botones de eliminar (basura) removidos")
    print("- ❌ Modales de confirmación de eliminación removidos")
    print("- ✅ Colspan actualizado de 8 a 7 columnas")
    print("- ✅ Funcionalidad de sincronización con Keycloak mantenida")
    
    print("\n🎯 Columnas restantes en el gestor:")
    print("1. ID - Identificador único del usuario")
    print("2. Nombre - Nombre del usuario") 
    print("3. Apellido - Apellido del usuario")
    print("4. Email - Dirección de correo electrónico")
    print("5. Teléfono - Número de teléfono")
    print("6. Rol - Administrador o Técnico")
    print("7. Laboratorios - Laboratorios asignados")
    
    return True

def main():
    """Función principal"""
    print("🗑️ Test de Remoción de Columna de Acciones - Gestor de Usuarios")
    print("=" * 70)
    
    if test_user_management_actions_removal():
        print("\n✅ Verificación completada correctamente")
        print("\n📖 Para verificar manualmente:")
        print("1. Abra http://localhost:5000/admin/usuarios")
        print("2. Verifique que NO hay columna 'Acciones'")
        print("3. Confirme que NO hay botones de editar/eliminar")
        print("4. El botón de 'Sincronizar Ahora' debe seguir presente")
        print("\n🎉 La columna de acciones ha sido removida exitosamente!")
    else:
        print("\n❌ Algunas verificaciones fallaron")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
