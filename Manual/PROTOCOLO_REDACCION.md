# PROTOCOLO DE REDACCIÓN DE MANUALES (ContaPY)

> **OBJETIVO:** Crear manuales que expliquen la **Lógica de Negocio** y el "Cerebro" del sistema, no solo la interfaz gráfica. El usuario debe entender qué está "programando" cuando llena un formulario.

---

## FASE 1: INVESTIGACIÓN PROFUNDA (CÓDIGO ANTES QUE TEXTO)
**PROHIBIDO** escribir una sola línea del manual sin antes haber ejecutado esta auditoría técnica:

1.  **Rastreo del Modelo de Datos (`backend/app/models`):**
    *   Identificar columnas "Banderas" (Booleans, Enums). *Ej: `afecta_inventario`, `es_servicio`.*
    *   Identificar Claves Foráneas críticas. *Ej: `cuenta_caja_id`.*

2.  **Rastreo de la Lógica de Servicio (`backend/app/services`):**
    *   Buscar dónde se usan esas "Banderas". ¿Qué `if` activan?
    *   **Pregunta Clave:** "¿Qué proceso se detiene o cambia si este campo está vacío o en falso?"
    *   *Ejemplo descubierto:* `if funcion_especial == 'VENTAS' and cuenta_cxc_id: activar_cartera()`.

3.  **Rastreo del Frontend (`frontend/app`):**
    *   Buscar validaciones ocultas o campos que aparecen/desaparecen.
    *   Identificar qué datos son obligatorios por código aunque no parezcan obvios.

---

## FASE 2: ESTRATEGIA DE CONTENIDO (REVELAR LA CAJA NEGRA)
Al redactar, transformar los hallazgos técnicos en explicaciones funcionales:

*   **No decir:** "Marque la casilla X".
*   **Decir:** "La casilla X actúa como un interruptor que obliga al sistema a..."

*   **Concepto de "Sinergia":**
    Explicar explícitamente cuando dos campos deben trabajar juntos.
    *   *Ej: "Para que funcione el Módulo Y, necesita configurar A + B."*

*   **Consecuencias del Error:**
    Advertir qué pasa si se configura mal.
    *   *Ej: "Si olvida este campo, el sistema no le permitirá cruzar facturas más adelante."*

---

## FASE 3: ESTRUCTURA OBLIGATORIA
Usar siempre la `PLANTILLA_MAESTRA.md`, pero enriqueciendo las secciones:

1.  **Introducción:** ¿Qué "poderes" otorga este módulo al usuario?
2.  **Lógica de Negocio (NUEVA SECCIÓN CRÍTICA):**
    *   Tablas de "Causa y Efecto".
    *   Diagramas mentales de flujo (escritos).
    *   Explicación de automatizaciones invisibles.
3.  **Diccionario de Campos:** Tabla detallada de cada input.
4.  **FAQ / Troubleshooting:** Basado en las restricciones de código encontradas en la Fase 1.

---

## PROMPT GENÉRICO PARA LA IA (Copiar y Pegar)
*"Vas a redactar el manual para el módulo [NOMBRE MÓDULO]. Antes de escribir, tu tarea obligatoria es leer los archivos `models/[archivo].py`, `services/[archivo].py` y `frontend/[archivo].js`. Debes encontrar la lógica oculta, los disparadores automáticos y las dependencias entre campos. No quiero una descripción de la pantalla; quiero que me expliques cómo piensa el software y cómo mis inputs afectan la contabilidad, el inventario y otros módulos. Usa el `PROTOCOLO_REDACCION.md` como ley suprema."*
