# Manual Técnico y de Usuario: Configuración Maestra de Parámetros Tributarios

## 1. Introducción y Alcance
Este documento detalla el funcionamiento, operación y lógica del módulo de **Parámetros de Impuestos** dentro del ecosistema ContaPY. Este módulo es el "cerebro" de la gestión tributaria, ya que define las reglas, tasas y periodicidades que el sistema utilizará automáticamente para calcular impuestos en facturas, compras y declaraciones.

**Importancia Crítica:** Una configuración errónea en este módulo resultará en cálculos incorrectos en toda la contabilidad. Se recomienda que esta sección sea administrada únicamente por el Contador General o el Director Financiero.

---

## 2. Interfaz de Usuario: Desglose Componente por Componente

La interfaz ha sido diseñada para ser intuitiva pero rigurosa. A continuación, se explica cada elemento visible en la pantalla:

### A. Encabezado y Herramientas
*   **Título del Impuesto:** Indica claramente qué impuesto se está configurando (ej. "Configuración de IVA").
*   **Botón "Ver Manual de Configuración":** Acceso directo a este documento. Úselo siempre que tenga dudas sobre un campo específico.

### B. Panel de Tarifas (Tabla Principal)
Este es el corazón de la configuración. Aquí se listan todas las variantes de tarifas que su empresa maneja para el impuesto seleccionado.

*   **Columna "Concepto":** Nombre descriptivo de la tarifa. Ejemplos: "Tarifa General", "Bienes Exentos", "Servicios al 5%". Este nombre aparecerá en los selectores al momento de crear facturas.
*   **Columna "Valor":** El número base para el cálculo matemático.
*   **Columna "Unidad":** Define cómo se interpreta el valor:
    *   **% (Porcentaje):** El uso más común. El sistema multiplicará la base gravable por este porcentaje (ej. Base * 0.19).
    *   **UVT (Unidad de Valor Tributario):** Usado para topes o sanciones. El sistema multiplicará este valor por la UVT vigente del año.
    *   **COP (Pesos):** Valores fijos absolutos.
*   **Columna "Acciones":** Contiene el botón de **Papelera** para eliminar tarifas obsoletas.

### C. Panel de Periodicidad
Define el ciclo fiscal de la obligación.
*   **Bimestral:** Ene-Feb, Mar-Abr, etc. (Común para Grandes Contribuyentes).
*   **Cuatrimestral:** Ene-Abr, May-Ago, Sep-Dic.
*   **Anual:** Ene-Dic (Común para Renta o Régimen Simple).

### D. Botón "Guardar Cambios"
Ubicado en la parte inferior derecha. **Es el botón más importante.** Si usted agrega tarifas o cambia la periodicidad pero sale de la página sin presionar este botón, **LOS CAMBIOS SE PERDERÁN**. Al presionarlo, el sistema guarda la configuración en la memoria persistente del navegador (y posteriormente en la base de datos).

---

## 3. Procedimientos Paso a Paso

### 3.1. Cómo Agregar una Nueva Tarifa
Siga estos pasos rigurosamente para crear una nueva regla de impuesto:

1.  Ubique el botón **"Agregar"** (azul claro con icono de cruz) en la esquina superior derecha de la tabla de tarifas.
2.  Se desplegará una ventana modal (Pop-up) llamada "Nueva Tarifa".
3.  **Campo Concepto:** Escriba un nombre claro y único.
    *   *Correcto:* "IVA Servicios Hoteleros"
    *   *Incorrecto:* "Tarifa 2" (No es descriptivo).
4.  **Campo Valor:** Ingrese solo el número. No use símbolos de porcentaje ni comas para miles. Use punto (.) para decimales si es necesario.
    *   *Ejemplo:* Para 19%, escriba `19`. Para 2.5%, escriba `2.5`.
5.  **Campo Unidad:** Seleccione `%` para la mayoría de impuestos. Seleccione `UVT` o `COP` solo si la normativa específica lo exige.
6.  Haga clic en el botón azul **"Agregar"** dentro de la ventana modal.
7.  Verifique que la nueva fila apareció inmediatamente en la tabla de fondo.
8.  **FINALIZAR:** Haga clic en el botón verde **"Guardar Cambios"** en la pantalla principal.

### 3.2. Cómo Eliminar una Tarifa Obsoleta
Si una tarifa ya no está vigente (ej. una reforma tributaria eliminó el IVA del 5% para cierto sector):

1.  Identifique la fila exacta en la tabla.
2.  Haga clic en el icono rojo de **Papelera** (Basura).
3.  El sistema le pedirá confirmación: "¿Está seguro de eliminar esta tarifa?".
4.  Acepte la confirmación.
5.  **FINALIZAR:** Haga clic en el botón verde **"Guardar Cambios"** para hacer permanente la eliminación.

### 3.3. Cómo Cambiar la Periodicidad
Si su empresa cambió de régimen (ej. pasó de responsable anual a bimestral por aumento de ingresos):

1.  Diríjase al panel inferior "Periodicidad".
2.  Haga clic sobre el círculo (radio button) de la nueva periodicidad deseada.
3.  Verifique que el punto azul se haya movido a la nueva opción.
4.  **FINALIZAR:** Haga clic en el botón verde **"Guardar Cambios"**.
    *   *Nota:* Esto recalculará automáticamente las fechas de vencimiento en el módulo de Calendario.

---

## 4. Solución de Problemas Frecuentes (Troubleshooting)

**P: Hice cambios, salí de la página y al volver no están.**
**R:** Usted olvidó presionar el botón verde "Guardar Cambios". El sistema no guarda automáticamente por seguridad, para evitar cambios accidentales en parámetros delicados. Debe repetir el proceso y guardar.

**P: No puedo eliminar una tarifa.**
**R:** Verifique si la tarifa está siendo usada en documentos históricos. Por integridad de datos, el sistema podría bloquear la eliminación de tarifas que ya tienen movimientos contables asociados. En ese caso, se recomienda renombrarla a "OBSOLETA - [Nombre]" en lugar de borrarla.

**P: El botón "Agregar" no hace nada.**
**R:** Asegúrese de haber llenado todos los campos en la ventana modal. Si el campo "Valor" está vacío o tiene letras, el sistema impedirá la creación para evitar errores matemáticos.

**P: ¿Cómo configuro retenciones en la fuente con bases mínimas?**
**R:** Para Retención en la Fuente, el módulo habilita columnas adicionales para "Base Mínima en UVT" y "Base Mínima en Pesos". Asegúrese de estar en la pestaña de "Retención en la Fuente" para ver estas opciones específicas.

---

## 5. Glosario Técnico
*   **UVT:** Unidad de Valor Tributario. Valor reajustado anualmente por la DIAN.
*   **Base Gravable:** Valor sobre el cual se aplica la tarifa.
*   **Tarifa:** Porcentaje o valor fijo definido por la ley.
*   **Persistencia:** Capacidad del sistema de recordar la información después de cerrar el navegador.

---
*Documento generado automáticamente por el Sistema de Asistencia ContaPY. Última actualización: Diciembre 2025.*
