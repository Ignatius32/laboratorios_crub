# Diseño Minimalista para Laboratorios CRUB

Esta actualización implementa un diseño minimalista y amigable para la aplicación de Laboratorios CRUB, siguiendo principios de diseño limpio y simplicidad.

## Características principales

- **Paleta de colores reducida**: Se utiliza una paleta monocromática con el azul grisáceo como color principal
- **Tipografía consistente**: Se mantiene la familia 'Inter' con pesos específicos para mejorar la legibilidad
- **Espaciado generoso**: Mayor espacio en blanco para dar "respiro" a los elementos
- **Bordes y sombras sutiles**: Se eliminaron las sombras pronunciadas y se simplificaron los bordes

## Estructura CSS

La estructura del CSS se ha reorganizado para facilitar el mantenimiento:

- **variables.css**: Contiene todas las variables de diseño (colores, espaciados, radios, etc.)
- **helpers.css**: Clases auxiliares para mantener la consistencia en toda la aplicación
- **datatables-custom.css**: Personalización minimalista para las tablas DataTables
- **style.css**: Estilos generales de la aplicación
- **admin-panel.css**: Estilos específicos para el panel de administración
- **tecnicos.css**: Estilos específicos para la sección de técnicos

## Uso de clases auxiliares

Para mantener la coherencia visual en toda la aplicación, utilice estas clases auxiliares:

### Contenedores
```html
<div class="simple-card">
   <!-- Contenido -->
</div>

<div class="simple-panel">
   <!-- Contenido -->
</div>
```

### Etiquetas
```html
<span class="simple-badge simple-badge-success">Stock normal</span>
<span class="simple-badge simple-badge-warning">Stock bajo</span>
<span class="simple-badge simple-badge-danger">Sin stock</span>
```

### Títulos de sección
```html
<h2 class="section-title">Título de sección</h2>
<p class="section-subtitle">Descripción de la sección</p>
```

## Recomendaciones para mantener el estilo minimalista

1. **Evitar el uso excesivo de colores**: Utilizar la paleta definida en variables.css
2. **Utilizar íconos con moderación**: Preferir íconos pequeños y sutiles
3. **Espaciado consistente**: Usar las variables de espaciado definidas 
4. **Mantener la tipografía coherente**: No agregar nuevas familias de fuentes
5. **Preferir bordes sutiles sobre sombras**: Para delimitar contenido
6. **Usar animaciones con moderación**: Las animaciones deben ser sutiles y rápidas

## Colores principales

- Color primario: #607D8B (Azul grisáceo)
- Color de texto: #455A64
- Color de fondo: #F5F7F8
- Color de borde: #CFD8DC

## Organización del código

Se recomienda seguir una estructura ordenada al agregar nuevos componentes, siguiendo las convenciones establecidas en los archivos CSS existentes.
