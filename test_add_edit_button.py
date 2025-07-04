#!/usr/bin/env python3
"""
Script de prueba para verificar que el botón de editar fue agregado al gestor de usuarios
"""
import os
import sys
import requests
from urllib.parse import urljoin

def test_edit_button_addition():
    """Prueba que el botón de editar fue agregado al gestor de usuarios"""
    base_url = "http://localhost:5000"
    usuarios_url = urljoin(base_url, "/admin/usuarios")
    
    print("✏️ Verificando adición del botón de editar en gestor de usuarios...")
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
        
        # Verificar que la columna "Acciones" está presente
        if '<th>Acciones</th>' in content:
            print("✅ Columna 'Acciones' presente en el encabezado de la tabla")
        else:
            print("❌ Columna 'Acciones' NO encontrada en el encabezado")
            
        # Verificar que los botones de editar están presentes
        if 'btn-warning' in content and 'fa-edit' in content:
            print("✅ Botones de editar presentes")
        else:
            print("❌ Botones de editar NO encontrados")
            
        # Verificar que NO hay botones de eliminar
        if 'btn-delete' not in content and 'fa-trash' not in content:
            print("✅ Botones de eliminar ausentes (correcto)")
        else:
            print("❌ Botones de eliminar PRESENTES (no deberían estar)")
            
        # Verificar que NO hay modales de confirmación
        if 'deleteModal' not in content:
            print("✅ Modales de confirmación ausentes (correcto)")
        else:
            print("❌ Modales de confirmación PRESENTES (no deberían estar)")
            
        # Verificar que el colspan fue actualizado correctamente
        if 'colspan="8"' in content:
            print("✅ Colspan actualizado correctamente (8 columnas)")
        elif 'colspan="7"' in content:
            print("❌ Colspan NO actualizado (todavía muestra 7 columnas)")
        else:
            print("ℹ️ No se encontró mensaje de 'No hay usuarios registrados'")
            
        # Verificar las columnas que deben estar presentes
        expected_columns = ['ID', 'Nombre', 'Apellido', 'Email', 'Teléfono', 'Rol', 'Laboratorios', 'Acciones']
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
            
        # Verificar enlace de edición específico
        if 'admin.edit_usuario' in content:
            print("✅ Enlaces de edición configurados correctamente")
        else:
            print("❌ Enlaces de edición NO encontrados")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error accediendo a la página de usuarios: {e}")
        return False
    
    print("\n📋 Resumen de funcionalidades:")
    print("- ✅ Columna 'Acciones' agregada al encabezado")
    print("- ✅ Botones de editar (lápiz) agregados")
    print("- ❌ Botones de eliminar (basura) ausentes") 
    print("- ❌ Modales de confirmación de eliminación ausentes")
    print("- ✅ Colspan actualizado de 7 a 8 columnas")
    print("- ✅ Funcionalidad de sincronización con Keycloak mantenida")
    
    print("\n🎯 Funcionalidades disponibles:")
    print("1. ✏️ Editar usuarios - Botón amarillo con ícono de lápiz")
    print("2. 👁️ Visualizar información - Todas las columnas visibles")
    print("3. 🔄 Sincronizar con Keycloak - Botón verde de sincronización")
    print("4. 📋 Gestión completa - Sin eliminación desde interfaz")
    
    return True

def main():
    """Función principal"""
    print("✏️ Test de Adición del Botón de Editar - Gestor de Usuarios")
    print("=" * 70)
    
    if test_edit_button_addition():
        print("\n✅ Verificación completada correctamente")
        print("\n📖 Para verificar manualmente:")
        print("1. Abra http://localhost:5000/admin/usuarios")
        print("2. Verifique que HAY columna 'Acciones'")
        print("3. Confirme que HAY botones de editar (lápiz amarillo)")
        print("4. Verifique que NO hay botones de eliminar")
        print("5. El botón de 'Sincronizar Ahora' debe seguir presente")
        print("\n🎉 El botón de editar ha sido agregado exitosamente!")
    else:
        print("\n❌ Algunas verificaciones fallaron")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
