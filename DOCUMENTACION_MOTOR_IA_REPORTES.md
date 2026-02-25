# Implementación de Reportes Financieros Controlados por Inteligencia Artificial y Function Calling

## Objetivo
Optimizar la precisión y consistencia del Agente IA en la plataforma Finaxis y a través de WhatsApp, minimizando respuestas incorrectas, alucinaciones de cuentas, y errores de límite de caracteres al enviar grandes volúmenes de datos. Estructurar un sistema escalable y estandarizado de reportes de terceros, cuentas y cruces.

## Fase 1: Transición hacia Arquitectura Paramétrica
- Mover el sistema basado en inyecciones de un prompt de texto (`System Prompt`) a un modelo estricto de **OpenAI Function Calling**.
- Definir las funciones disponibles (Reportes y Auxiliares) utilizando JSON Schemas para que la IA solo extraiga parámetros (Cuenta, Fecha_Inicio, Fecha_Fin, Formato, Tercero).
- Desconectar la responsabilidad de la IA de calcular fechas o montos, asignándole la única tarea de clasificar la intención del usuario.

## Fase 2: Control de Contexto "Fallback"
- Crear un servicio intermedio (`ai_context_helper`) en Python.
- Si la IA encuentra que el usuario no suministró una fecha específica (Ej: "Dame el pyG"), la IA devolverá `null`. 
- El `context_helper` interceptará este `null` y, apoyándose en la base de datos (modelo `Empresa`), inyectará inteligentemente la `fecha_inicio_operaciones`, asegurando que el reporte compile correctamente.

## Fase 3: Reformulación de la Salida en Aplicación Móvil (WhatsApp)
- Identificar y remover el código que trunca erróneamente listas de datos que exceden el tamaño máximo del prompt.
- Enrutar todos los reportes solicitados por mensajería hacia una función unificada que iteré el cuerpo de la data para construir totales.
- Retornar a la IA únicamente un cuadro resumen (Ej: Total Pasivo, Total Devoluciones, etc.) e instruirla para redactar mensajes concisos y precisos de carácter ejecutivo, dirigiendo al usuario a la web para el desglose.

## Fase 4: Estandarización Global de Terceros y Cuentas (NUEVO)
Procedimiento riguroso para la lectura inteligente de cuentas y sus cruces con terceros a gran escala.

### 4.1. La Matriz de Simbiosis (Movimiento + Tercero + Cuenta)
El corazón del enrutamiento NO será ambiguo ni buscará "Cualquier saldo o cartera". El sistema responderá obedeciendo una combinatoria booleana estricta (presencia/ausencia de palabras) para evitar que la IA enloquezca en bases de múltiples cuentas:

*   **ESCENARIO A (`Tercero` + `Cuenta` + Palabra Clave `Movimiento`):**
    *   **Prioriza el Tercero:** (Ej: *"Movimientos del tercero Pedro y sus cuentas"*). El motor sabe que hay `Tercero`, hay `Cuentas` y pide `Movimiento`. Va exclusivamente al Módulo Terceros -> **Auxiliar de Terceros** (Vista Agrupada por Tercero).
    *   **Prioriza la Cuenta:** (Ej: *"Movimiento de Donaciones y sus terceros"*). Hay `Cuenta`, hay `Tercero` y pide `Movimiento`. Va exclusivamente al Módulo Terceros -> **Auxiliar de Terceros** (Vista Agrupada por Cuenta).

*   **ESCENARIO B (`Tercero` + `Cuenta` + Omitida la palabra `Movimiento`):**
    *   **Variante Pura de Saldos:** (Ej: *"Terceros de Arrendamientos"* o *"Sandra y sus cuentas"*). El motor asume incondicionalmente SALDOS. No va a Inventario, ni a Cartera Abstracta. Va única y exclusivamente a Módulo Terceros -> **Relación de Saldos (de Terceros)**.

*   **ESCENARIO C (Palabra Clave `Movimiento` + Omitida la palabra `Tercero`):**
    *   **Auxiliar Puro:** (Ej: *"Movimiento de Caja Menor"*). Hay `Movimiento` y una `Cuenta`, pero no dice nada de terceros. Va al Módulo Contabilidad -> **Auxiliar de Cuenta**.

### 4.2. Nivel de Profundidad de la Cuenta
*   La IA y el motor buscarán de forma prioritaria la coincidencia del término de consulta del usuario (Ej: `donaciones`) **únicamente** en cuentas de detalle financiero "Ejecutables" o vinculables (Niveles 4 o 5, es decir subclases, auxiliares directos o cuentas mayores de 6 dígitos con movimiento contable real). 
*   Se ignorarán las cuentas agrupadoras (Nivel 1 al 3) para evitar resultados abstractos o errores de consulta DB en consultas específicas.
*   En caso de homonimia verbal (La palabra existe en Ingresos 4xxx y Gastos 5xxx), la instrucción natural del usuario (`Pago`, `Cancelación` vs `Recaudado`, `Venta`) inclinará paramétricamente la báscula de búsqueda.

### 4.2.1 Simbiosis Inversa Cruzada (Defensa Anti-Ambigüedad)
*   Existen entidades ambiguas ("Parqueadero") que pueden ser tanto Cuentas Ejecutables como Terceros reales. 
*   **Regla de Descarte Absoluto:** Si el usuario declara una de las palabras y le suma un sufijo de propiedad cruzada (`"... y sus terceros"`, `"... y sus cuentas"`), el motor de Intercepción obligará a reconvertir la entidad a su opuesto lógico.
    *   *"{Entidad Ambigua} y sus cuentas"* -> Obliga a que la entidad se busque exclusivamente como **Tercero**.
    *   *"{Entidad Ambigua} y sus terceros"* -> Obliga a que la entidad se busque exclusivamente como **Cuenta Ejecutable**.

### 4.3. Algoritmo de Enrutamiento de Vistas (Matrices Tercero-Cuenta)
Se define el esquema base de cuatro (4) dimensiones para consultas mixtas:

1.  **{Cuenta Clave} + {Terceros} + {Movimiento}**: => Vista Auxiliar Inversa *(Pantalla Auxiliares - Iniciar agrupando por la Cuenta Principal y desglosando todos sus Terceros internos).*
2.  **{Tercero Clave} + {Cuentas} + {Movimiento}**: => Vista Auxiliar Directa *(Pantalla Auxiliares - Iniciar agrupando por el Tercero y desglosando todas las cuentas en las que participó).*
3.  **{Cuenta Clave} + {Terceros} + {SIN Movimiento}**: => Vista Relación de Saldos Inversa *(Pantalla Saldos Básicos).*
4.  **{Tercero Clave} + {Cuentas} + {SIN Movimiento}**: => Vista Relación de Saldos Directa *(Pantalla Saldos Básicos).*

### 4.4 Rango de Dinamismo Fechal
- Periodos con rangos cerrados (Ej: "febrero de 2026") se parametrizarán strictamente en start y end date.
- Omisión de temporalidad cargará desde la apertura de sistema.

### 4.5. Automatización y Forzado de Descarga PDF (Regla de Oro)
- Todos los reportes procesados mediante la interfaz natural (o por intercesores de WhatsApp) deberán forzosamente, al cargar en el Frontend, accionar la generación inmediata y descarga de un archivo PDF estático. 
- Esto garantiza el historial físico de la interacción para revisión o distribución futura del usuario y obvia el clic manual posterior.
