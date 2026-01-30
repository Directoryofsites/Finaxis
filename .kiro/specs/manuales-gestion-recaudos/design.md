# Documento de Diseño - Manuales de Gestión de Recaudos

## Visión General

Este diseño especifica la creación de un sistema completo de documentación para el módulo de Gestión de Recaudos, incluyendo manuales HTML detallados y la integración de botones de acceso en cada página funcional del sistema.

## Arquitectura

### Estructura de Archivos
```
Manual/ph/
├── dashboard.html                    # Manual del dashboard principal
├── unidades.html                     # Manual de gestión de unidades
├── propietarios.html                 # Manual de directorio de propietarios
├── conceptos.html                    # Manual de conceptos de cobro
├── facturacion.html                  # Manual de facturación masiva
├── pagos.html                        # Manual de registro de pagos
├── estado-cuenta.html                # Manual de estado de cuenta
├── reportes.html                     # Manual de reportes generales
├── reportes-edades.html              # Manual de cartera por edades
├── reportes-saldos.html              # Manual de balance de cartera
├── presupuestos.html                 # Manual de gestión de presupuestos
├── reportes-ejecucion.html           # Manual de ejecución presupuestal
├── configuracion.html                # Manual de configuración
└── assets/
    ├── css/
    │   └── manual-styles.css         # Estilos compartidos
    ├── images/
    │   └── screenshots/              # Capturas de pantalla
    └── js/
        └── manual-navigation.js      # Funcionalidad de navegación
```

### Integración Frontend
Los botones de manual se integrarán en cada página mediante:
- Componente React reutilizable `ManualButton`
- Posicionamiento consistente en el header de cada página
- Modal o nueva ventana para mostrar el contenido del manual

## Componentes y Interfaces

### Componente ManualButton
```jsx
interface ManualButtonProps {
  manualPath: string;    // Ruta al archivo HTML del manual
  title: string;         // Título descriptivo del manual
  position?: 'header' | 'sidebar' | 'floating';
}
```

### Servicio de Manuales
```javascript
class ManualService {
  openManual(manualPath: string): void;
  getManualContent(manualPath: string): Promise<string>;
  checkManualExists(manualPath: string): boolean;
}
```

## Modelos de Datos

### Estructura de Manual
```typescript
interface Manual {
  id: string;
  title: string;
  description: string;
  filePath: string;
  lastUpdated: Date;
  sections: ManualSection[];
}

interface ManualSection {
  id: string;
  title: string;
  content: string;
  order: number;
  subsections?: ManualSection[];
}
```

### Configuración de Páginas
```typescript
interface PageManualConfig {
  pagePath: string;
  manualFile: string;
  buttonPosition: 'header' | 'sidebar';
  buttonText: string;
}
```

## Propiedades de Corrección

*Una propiedad es una característica o comportamiento que debe mantenerse verdadero en todas las ejecuciones válidas de un sistema - esencialmente, una declaración formal sobre lo que el sistema debe hacer. Las propiedades sirven como puente entre especificaciones legibles por humanos y garantías de corrección verificables por máquina.*

### Reflexión de Propiedades

Después de analizar todos los criterios de aceptación testeable, se identificaron las siguientes redundancias:
- Los criterios 4.1-4.7 son todos ejemplos específicos de existencia de manuales que pueden consolidarse en una propiedad general
- Los criterios sobre consistencia visual (3.1, 3.2) pueden combinarse en una propiedad de consistencia de UI
- Los criterios sobre estructura de contenido (2.1, 2.2, 5.1, 5.3, 5.4) pueden consolidarse en propiedades de estructura HTML

### Propiedades Consolidadas

**Propiedad 1: Presencia universal de botones de manual**
*Para cualquier* página del módulo de recaudos, debe existir exactamente un botón de manual visible y accesible en el DOM
**Valida: Requisitos 1.1**

**Propiedad 2: Funcionalidad de apertura de manuales**
*Para cualquier* botón de manual en el sistema, hacer clic debe abrir el contenido del manual correspondiente
**Valida: Requisitos 1.2**

**Propiedad 3: Nomenclatura consistente de archivos**
*Para cualquier* archivo de manual creado, debe seguir el patrón de nomenclatura establecido y ubicarse en la ruta correcta
**Valida: Requisitos 1.3**

**Propiedad 4: Estructura HTML válida de manuales**
*Para cualquier* manual HTML, debe contener elementos estructurales válidos como encabezados, secciones y navegación
**Valida: Requisitos 1.4, 2.1, 5.1, 5.3**

**Propiedad 5: Presencia de elementos visuales**
*Para cualquier* manual que documente procesos con interfaz, debe incluir elementos de imagen para capturas de pantalla
**Valida: Requisitos 2.3**

**Propiedad 6: Estructura secuencial de procesos**
*Para cualquier* sección de manual que describa un proceso, debe usar listas ordenadas (ol) para presentar los pasos
**Valida: Requisitos 2.2**

**Propiedad 7: Consistencia de posicionamiento de botones**
*Para cualquier* botón de manual implementado, debe usar las mismas clases CSS y posicionamiento relativo
**Valida: Requisitos 3.1, 3.2**

**Propiedad 8: Elementos requeridos en botones**
*Para cualquier* botón de manual renderizado, debe contener tanto un icono como texto descriptivo
**Valida: Requisitos 3.3**

**Propiedad 9: Funcionalidad persistente entre páginas**
*Para cualquier* navegación entre páginas del módulo, los botones de manual deben mantener su funcionalidad
**Valida: Requisitos 3.4**

**Propiedad 10: Consistencia de estilos HTML**
*Para cualquier* manual HTML, debe usar las mismas clases CSS y estructura de estilos que otros manuales
**Valida: Requisitos 5.4**

## Manejo de Errores

### Casos de Error Identificados
1. **Manual no encontrado**: Cuando un botón intenta abrir un manual inexistente
2. **Archivo corrupto**: Cuando un manual HTML tiene sintaxis inválida
3. **Permisos de archivo**: Cuando no se puede acceder al archivo de manual
4. **Contenido vacío**: Cuando un manual existe pero no tiene contenido

### Estrategias de Manejo
- Validación de existencia de archivos antes de mostrar botones
- Fallback a mensaje de error amigable si el manual no está disponible
- Logging de errores para debugging
- Interfaz de usuario que degrada graciosamente

## Estrategia de Pruebas

### Enfoque Dual de Pruebas

El sistema utilizará tanto pruebas unitarias como pruebas basadas en propiedades para garantizar cobertura completa:

**Pruebas Unitarias:**
- Verificarán ejemplos específicos de funcionalidad de botones
- Probarán casos de error conocidos
- Validarán integración entre componentes
- Cubrirán puntos de integración específicos

**Pruebas Basadas en Propiedades:**
- Utilizarán la biblioteca **Jest** con **fast-check** para JavaScript/React
- Cada prueba basada en propiedades ejecutará un mínimo de 100 iteraciones
- Verificarán propiedades universales que deben mantenerse en todas las entradas
- Cada prueba será etiquetada con el formato: '**Feature: manuales-gestion-recaudos, Property {number}: {property_text}**'

**Requisitos de Etiquetado:**
- Cada propiedad de corrección debe implementarse mediante UNA SOLA prueba basada en propiedades
- Las pruebas deben referenciar explícitamente la propiedad de corrección del documento de diseño
- El formato de etiquetado debe seguirse exactamente para trazabilidad

**Cobertura de Pruebas:**
- Las pruebas unitarias capturan errores concretos y casos específicos
- Las pruebas de propiedades verifican corrección general en múltiples entradas
- Juntas proporcionan cobertura integral: pruebas unitarias para casos específicos, pruebas de propiedades para garantías generales

## Consideraciones de Implementación

### Tecnologías Utilizadas
- **Frontend**: React/Next.js para componentes de botones
- **Estilos**: Tailwind CSS para consistencia visual
- **Manuales**: HTML5 con CSS3 y JavaScript vanilla
- **Iconografía**: React Icons (Font Awesome)

### Patrones de Diseño
- **Componente Reutilizable**: ManualButton como componente React
- **Servicio Singleton**: ManualService para gestión centralizada
- **Observer Pattern**: Para actualizaciones de contenido de manuales
- **Factory Pattern**: Para creación de diferentes tipos de manuales

### Consideraciones de Rendimiento
- Lazy loading de contenido de manuales
- Caché de manuales frecuentemente accedidos
- Optimización de imágenes en capturas de pantalla
- Minificación de archivos CSS y JS

### Accesibilidad
- Botones con etiquetas ARIA apropiadas
- Navegación por teclado en manuales
- Contraste de colores adecuado
- Texto alternativo para imágenes

### Mantenibilidad
- Estructura modular de archivos
- Documentación inline en código
- Convenciones de nomenclatura claras
- Separación de responsabilidades entre componentes