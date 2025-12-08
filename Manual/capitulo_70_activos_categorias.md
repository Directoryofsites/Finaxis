# Manual de Usuario: Categorías de Activos Fijos (El Cerebro Contable)

## 1. Introducción
Antes de registrar cualquier activo (una silla, un computador, un carro), el sistema necesita saber las "Reglas del Juego".
El módulo de **Categorías** es donde usted define esas reglas. Aquí le dice al software:
*"Todos los computadores se deprecian a 3 años, pero los edificios a 45 años".*

**¿Por qué es importante?**
Si configura bien esto una sola vez, el sistema hará toda la contabilidad automática por usted el resto del año.

---

## 2. ¿Cómo acceder?
Menú Principal > **Activos Fijos** > Botón **Categorías y Vidas Útiles**.

---

## 3. Guía Paso a Paso para Crear una Categoría

Haga clic en el botón azul **[+ Nueva Categoría]** y complete:

### A. Nombre Descriptivo
Use nombres claros que agrupen bienes similares.
*   *Ejemplo:* "Equipo de Computo y Comunicación"
*   *Ejemplo:* "Flota y Equipo de Transporte"
*   *Ejemplo:* "Muebles y Enseres de Oficina"

### B. Vidas Útiles (El corazón de la NIIF)
Aquí definimos en **cuántos meses** se gastará el bien. El sistema permite manejar dos realidades paralelas:

1.  **Vida Útil NIIF (Realidad Financiera):**
    *   Es el tiempo que usted *realmente* espera usar el activo.
    *   *Ejemplo:* Un portátil nromalmente dura **36 meses** (3 años).
    
2.  **Vida Útil Fiscal (Regla DIAN):**
    *   Es el tiempo mínimo que exige la ley para descontar el gasto.
    *   *Ejemplo:* La ley tributaria puede exigir deprecialo a **60 meses** (5 años).

> **El Sistema es Dual:** Calculará ambos valores simultáneamente para que usted tenga el reporte de "Diferencia Fiscal" listo para su declaración de renta.

### C. Método de Depreciación
Por ahora, el estándar mundial es **Línea Recta** (El activo pierde valor igual todos los meses). Déjelo seleccionado a menos que su contador indique lo contrario.

---

## 4. Cuestionario de Autoevaluación (FAQ)

**P1: ¿Qué pasa si me equivoco en la vida útil y ya registré activos?**
**R:** Los activos nuevos tomarán la corrección. Los antiguos mantendrán la regla con la que nacieron (histórico). Para corregir antiguos, debe hacer un "Avalúo" o re-estimación (Fase avanzada).

**P2: ¿Puedo tener una categoría "No Depreciable"?**
**R:** ¡Sí! Use esto para **Terrenos**. Los terrenos no se gastan con el tiempo, al contrario, suelen subir de precio. Ponga 0 meses o método "No Depreciar".

**P3: ¿Las cuentas contables se ponen aquí?**
**R:** Internamente sí. El sistema ya sabe que la cuenta de activos empieza por 15 y la de gasto por 51. En esta versión simplificada, el software asigna las cuentas estándar automáticamente.

**P4: ¿Cuántas categorías debo crear?**
**R:** Las recomendadas son entre 5 y 10:
1. Edificaciones
2. Maquinaria y Equipo
3. Equipo de Oficina
4. Equipo de Cómputo
5. Flota y Transporte
6. Terrenos
