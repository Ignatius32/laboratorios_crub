// Script para limpiar el estado guardado de DataTables que puede estar causando conflictos
// Ejecuta este script en la consola del navegador (F12) si sigues teniendo problemas

console.log('Limpiando estado guardado de DataTables...');

// Limpiar localStorage relacionado con DataTables
for (let i = localStorage.length - 1; i >= 0; i--) {
    const key = localStorage.key(i);
    if (key && (key.includes('DataTables') || key.includes('movimientos') || key.includes('producto'))) {
        localStorage.removeItem(key);
        console.log('Eliminado de localStorage:', key);
    }
}

// Limpiar sessionStorage relacionado con DataTables
for (let i = sessionStorage.length - 1; i >= 0; i--) {
    const key = sessionStorage.key(i);
    if (key && (key.includes('DataTables') || key.includes('movimientos') || key.includes('producto'))) {
        sessionStorage.removeItem(key);
        console.log('Eliminado de sessionStorage:', key);
    }
}

// Limpiar cualquier evento o instancia de DataTable que pueda estar activa
if (typeof $ !== 'undefined' && $.fn.DataTable) {
    $('.dataTable').each(function() {
        if ($.fn.DataTable.isDataTable(this)) {
            $(this).DataTable().destroy();
            console.log('Destruida tabla DataTable existente');
        }
    });
}

console.log('Limpieza completada. Recarga la página para ver los cambios.');
