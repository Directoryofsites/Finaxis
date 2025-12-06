# 🎨 Guía de Estilo Visual: Manual de Usuario ContaPY

Este documento define los estándares de diseño, tipografía y maquetación para el Manual de Usuario en Línea de ContaPY. El objetivo es mantener una consistencia visual impecable, profesional y altamente legible en todos los capítulos.

---

## 1. Filosofía de Diseño
*   **Legibilidad ante todo:** El contenido debe ser fácil de escanear y leer.
*   **Jerarquía Clara:** Diferenciación obvia entre títulos, subtítulos y cuerpo.
*   **Espaciado Generoso:** El uso de espacio en blanco ("aire") es vital para evitar la fatiga visual.
*   **Minimalismo Profesional:** Evitar decoraciones innecesarias; cada elemento tiene un propósito.

---

## 2. Paleta de Colores

| Elemento | Color Hex | Tailwind Class | Uso |
| :--- | :--- | :--- | :--- |
| **Fondo General** | `#F9FAFB` | `bg-gray-50` | Fondo de la pantalla (fuera de la tarjeta). |
| **Fondo Tarjeta** | `#FFFFFF` | `bg-white` | Fondo del área de lectura. |
| **Texto Principal** | `#1E1E1E` | `text-[#1E1E1E]` | Títulos Principales (H1). |
| **Texto Secundario** | `#2B2B2B` | `text-[#2B2B2B]` | Subtítulos (H2, H3) y Párrafos. |
| **Acento / Marca** | `#4F46E5` | `text-indigo-600` | Enlaces, Iconos, Bordes de énfasis. |
| **Bordes Suaves** | `#E5E7EB` | `border-gray-200` | Líneas divisorias, bordes de tablas. |

---

## 3. Tipografía y Jerarquía

La fuente base es **Sans-Serif** (Inter, Roboto o System UI).

### 3.1. Título Principal (H1)
*   **Tamaño:** 36px (`text-4xl`).
*   **Peso:** Extra Bold (`font-extrabold`).
*   **Color:** `#1E1E1E`.
*   **Espaciado:**
    *   Margen Superior: `3rem` (48px).
    *   Margen Inferior: `2rem` (32px).
*   **Estilo:** Lleva una línea divisoria inferior suave (`border-b`).

### 3.2. Subtítulo de Sección (H2)
*   **Tamaño:** 24px (`text-2xl`).
*   **Peso:** Bold (`font-bold`).
*   **Color:** `#2B2B2B`.
*   **Espaciado:**
    *   Margen Superior: `4rem` (64px) -> *Clave para separar temas*.
    *   Margen Inferior: `1.5rem` (24px).

### 3.3. Sub-sección (H3)
*   **Tamaño:** 20px (`text-xl`).
*   **Peso:** SemiBold (`font-semibold`).
*   **Color:** `#2B2B2B`.
*   **Espaciado:**
    *   Margen Superior: `2.5rem` (40px).
    *   Margen Inferior: `1rem` (16px).

### 3.4. Cuerpo de Texto (Párrafos)
*   **Tamaño:** 18px (`text-lg`).
*   **Color:** `#2B2B2B`.
*   **Interlineado:** 1.625 (`leading-relaxed`) -> *Muy importante para lectura cómoda*.
*   **Margen Inferior:** `1.5rem` (24px).

---

## 4. Componentes UI

### A. Listas (Bullets y Numeradas)
*   **Tamaño de texto:** 18px (`text-lg`).
*   **Ubicación:** Margen izquierdo de 1.5rem (`ml-6`).
*   **Espaciado entre ítems:** `0.75rem` (12px) (`space-y-3`).
*   **Margen Inferior:** `2rem` (32px).

### B. Citas y Notas (Blockquotes)
Se usan para resaltar información importante, advertencias o ejemplos.
*   **Estilo:** Contenedor con fondo gris muy suave (`bg-gray-50`).
*   **Borde:** Borde izquierdo grueso (4px) color Índigo (`border-indigo-400`).
*   **Relleno:** Padding interno de `1.5rem` (24px).
*   **Texto:** Itálica, color gris oscuro (`text-gray-700`).

### C. Tablas
*   **Contenedor:** Bordes redondeados y sombra suave.
*   **Cabecera:** Fondo gris claro (`bg-gray-50`), texto en mayúsculas, negrita y pequeño (`text-xs`).
*   **Celdas:** Padding generoso (`px-6 py-4`), bordes inferiores suaves.

### D. Imágenes
*   **Estilo:** Bordes redondeados (`rounded-xl`).
*   **Efecto:** Sombra media (`shadow-md`) y borde fino (`border-gray-100`).
*   **Ubicación:** Centradas, con margen vertical amplio (`my-8`).

---

## 5. Reglas de Implementación Técnica (React/Next.js)

Para replicar este diseño en código, **NO** use las clases por defecto de `prose`. Debe utilizar componentes personalizados en `ReactMarkdown` como se muestra a continuación:

```javascript
const MarkdownComponents = {
    h1: ({node, ...props}) => <h1 className="text-4xl font-extrabold text-[#1E1E1E] mt-12 mb-8 border-b border-gray-200 pb-4" {...props} />,
    h2: ({node, ...props}) => <h2 className="text-2xl font-bold text-[#2B2B2B] mt-16 mb-6" {...props} />,
    p: ({node, ...props}) => <p className="text-lg text-[#2B2B2B] leading-relaxed mb-6" {...props} />,
    // ... otros componentes definidos en frontend/app/manual/page.js
};
```

---

**Fin de la Guía de Estilo**
