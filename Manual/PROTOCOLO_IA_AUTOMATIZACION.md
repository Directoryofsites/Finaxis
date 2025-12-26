# PROTOCOLO DE AUTOMATIZACIÃ“N E INTEGRACIÃ“N IA (Reportes y Comandos de Voz)

**VersiÃ³n:** 1.0
**Fecha:** 23 de Diciembre de 2025
**Generado por:** Agente Antigravity (Google Deepmind)
**Contexto:** IntegraciÃ³n de comandos de voz (WhatsApp, PDF, Email) sobre reportes existentes en React.

---

## 1. IntroducciÃ³n
Este documento registra las lecciones aprendidas, los obstÃ¡culos tÃ©cnicos ("tropezones") y las soluciones estÃ¡ndar ("Protocolo") para implementar funcionalidades de automatizaciÃ³n controladas por IA en la arquitectura actual de ContaPY2 (Next.js + Python FastAPI).

Cualquier futura implementaciÃ³n de comandos del tipo **"Genera X reporte y envÃ­alo por Y"** debe seguir estas reglas para evitar regresiones.

---

## 2. El DesafÃ­o de la SincronizaciÃ³n (Race Conditions)

### El Problema
Al ejecutar un comando complejo (ej: "Auxiliar de Jhovana Martinez cuenta Caja"), el frontend debe realizar mÃºltiples pasos asÃ­ncronos secuenciales:
1. Cargar la pÃ¡gina.
2. Buscar y seleccionar el Tercero (Jhovana).
3. Esperar que carguen las cuentas de ese tercero.
4. Buscar y seleccionar la Cuenta (Caja).
5. Generar el reporte.
6. Exportar/Enviar (PDF/WhatsApp).

**El error comÃºn:** El sistema intenta realizar el paso 4 o 5 antes de completar el 2 o 3, resultando en reportes vacÃ­os, interfaces congeladas ("Processando..."), o selectores fallidos.

### Protocolo de SoluciÃ³n
1.  **NO limpiar la URL prematuramente**:
    *   *Error:* Hacer `window.history.replaceState` en el primer `useEffect` (carga de tercero).
    *   *Consecuencia:* El segundo `useEffect` (carga de cuentas) intenta leer los parÃ¡metros de la URL, pero ya han sido borrados.
    *   *Regla:* La limpieza de URL debe hacerse **DIFERIDA**, solo despuÃ©s de que el reporte se haya generado exitosamente (generalmente en el evento final de Ã©xito o tras un timeout largo).

2.  **Timeouts Robustos "Triple Armor"**:
    *   Depender solo de `useEffect` ([dep1, dep2]) es frÃ¡gil en formularios complejos.
    *   Usar `setTimeout` con mÃ¡rgenes de seguridad (ej. 1200ms - 1500ms) para simular el click humano una vez los datos estÃ¡n poblados.
    *   *Ejemplo:* `setTimeout(() => document.getElementById('btn-consultar').click(), 1500);`

3.  **Fallback de Robustez (IntenciÃ³n de Usuario)**:
    *   Si la IA solicita una cuenta especÃ­fica (ej. "Caja General") pero esta no existe en la lista del tercero:
    *   **NO** detener el proceso.
    *   **SÃ�** advertir (`toast.warn("Cuenta no encontrada, mostrando todas")`), seleccionar `ALL` (todas), y **EJECUTAR** el reporte de todas formas.
    *   *RazÃ³n:* El usuario prioriza recibir el informe (aunque sea general) a que el sistema se quede esperando correcciones.

---

## 3. Protocolo de Descarga y EnvÃ­o

### Descarga de PDF
*   **Problema:** Los navegadores bloquean `window.open(url)` si no es resultado directo de un click de usuario (popup blocker), o a veces la descarga no inicia en mÃ³viles.
*   **ImplementaciÃ³n Correcta (Backend):**
    *   Endpoint debe incluir header: `Content-Disposition: attachment; filename="reporte.pdf"`.
*   **ImplementaciÃ³n Correcta (Frontend):**
    *   Usar `window.location.href = pdfUrl;` para forzar la navegaciÃ³n/descarga directa en la misma pestaÃ±a. Es mÃ¡s compatible que crear elementos `<a>` invisibles dinÃ¡micos.

### EnvÃ­o por Correo
*   Se creÃ³ un servicio centralizado en Backend (`/api/reports/dispatch-email`).
*   **Estructura:**
    *   Frontend envÃ­a: `{ report_type: 'nombre_reporte', email_to: 'x@y.com', filtros: {...} }`
    *   Backend reutiliza la lÃ³gica de generaciÃ³n de PDF existente (`documento_service`), genera el binario en memoria y lo adjunta al correo usando `EmailService`.
*   *Nota:* No duplicar lÃ³gica de generaciÃ³n de PDF. El endpoint de correo debe llamar a la misma funciÃ³n que el endpoint de impresiÃ³n.

---

## 4. Checklist para Nuevos Reportes

Si se va a agregar voz a un nuevo reporte, copiar el patrÃ³n de `balance-de-prueba/page.js`:

1.  [ ] **Imports:** Agregar `toast` de `react-toastify`.
2.  [ ] **State:** Agregar `autoPdfTrigger`, `wppNumber`, `emailAddress`, `lastProcessedParams`.
3.  [ ] **URL Parsing:** En el `useEffect` de carga, leer params. **NO BORRAR URL AQUI**.
4.  [ ] **BotÃ³n Simulado:** Usar `setTimeout` para hacer click en el botÃ³n de generar (evita lÃ³gica duplicada de generaciÃ³n).
5.  [ ] **Effect de AutomatizaciÃ³n:** Escuchar cambios en `reportData`. Si `autoPdfTrigger` es true y hay datos:
    *   Llamar `handleExportPDF`.
    *   Si hay wpp, abrir `wa.me`.
    *   Si hay email, llamar `handleSendEmail`.
6.  [ ] **Limpieza:** Solo al final del proceso limpiar variables y URL.

---
*Este documento debe ser consultado antes de realizar modificaciones a la lÃ³gica de reportes.*

## 5. Configuración del Servicio de Correo (SMTP)

### Lecciones Aprendidas (Gmail)
Al configurar el envío de correos con Gmail (smtp.gmail.com), hemos encontrado bloqueos de seguridad que requieren pasos específicos.

1.  **NO usar contraseña normal:** Gmail rechaza (Error 535) las contraseñas de inicio de sesión estándar.
2.  **Usar App Passwords:** Es OBLIGATORIO generar una "Contraseña de aplicación" de 16 caracteres.
    *   *Ruta:* Cuenta Google > Seguridad > Verificación en 2 pasos > Contraseñas de aplicaciones.
    *   *Formato:* bcd efgh ijkl mnop (el sistema debe eliminar los espacios al guardarla).

### Manejo de Variables de Entorno (.env)
1.  **Reinicio Obligatorio:** Python (uvicorn/astapi) carga el archivo .env **solo al iniciar**. Si se actualizan credenciales en el .env, el Backend **DEBE REINICIARSE** manualmente para que los cambios surtan efecto.
2.  **Riesgo de Corrupción (Encoding):**
    *   Al editar .env con comandos de PowerShell (Set-Content), existe riesgo de cambiar la codificación a UTF-16, lo que hace que Python lea variables como None o con caracteres extraños (\x00).
    *   **Solución:** Usar scripts de Python (open(..., encoding='utf-8')) para escribir en el .env de forma segura, o editores de texto plano.
3.  **Diagnóstico:** Si las credenciales parecen correctas pero falla el login, usar un script de diagnóstico (smtplib.SMTP(...).login()) para verificar qué está viendo realmente Python.


## 6. Módulo de Correo Dinámico (SaaS)

Se implementó un sistema para que cada empresa configure su propio servidor SMTP, eliminando la dependencia del archivo .env global.

### Arquitectura
1.  **Seguridad (Fernet):** Las contraseñas se almacenan encriptadas en la tabla empresa_config_email.
    *   Requiere una ENCRYPTION_KEY persistente en el .env. Si esta llave se pierde, los correos configurados deben reingresarse.
2.  **Frontend:** Nuevo menú en *Admin > Herramientas > Configuración Correo* para autogestión del cliente.
3.  **Backend:** EmailService ahora consulta primero la DB usando el ID de la empresa del usuario. Si no encuentra configuración propia, (opcionalmente) hace fallback al .env del servidor.

### Flujo de Usuario
*   El cliente obtiene su **Contraseña de Aplicación** de Google (Requisito ineludible).
*   Ingresa correo y clave en el módulo web.
*   El sistema valida conexión antes de guardar.
*   A partir de ahí, todos los comandos de voz (Envia un pdf...) usan SU cuenta como remitente.

## 7. Protocolo de Definición de Herramientas IA (Backend & Frontend)

Aprendizaje crítico sobre cómo lograr que la IA "entienda" parámetros nuevos y cómo evitar alucinaciones.

### A. Definición de Herramientas (Backend - `ai_agent.py`)
**El Problema:** Si la IA ignora una palabra clave obvia (ej: nombre de producto), casi siempre es porque **la definición de la herramienta (Tool Schema)** no tiene un campo explícito para ello.
**Regla:**
-   **Explicitud:** No asumas que la IA adivinará. Si quieres filtrar por `producto` o `bodega`, agrégalos explícitamente al JSON schema de la herramienta (ej: `generar_reporte_movimientos`).
-   **Descripciones Claras:** Describe qué se espera (ej: "Nombre, código o referencia del producto").

### B. Mapeo y Robustez (Frontend - `RightSidebar / SmartSearch`)
**El Problema:** La IA no siempre usa la llave que esperas (`p.producto`). A veces usa `p.articulo`, `p.referencia` o `p.nombre`.
**Regla:**
-   **Fallback en Cascada:** Al leer los parámetros en el frontend, usa una cadena de fallbacks amplia.
    ```javascript
    const prod = p.producto || p.producto_nombre || p.articulo || p.referencia || p.concepto || p.descripcion;
    ```
-   **Atomicidad de Búsqueda:** Para evitar que la IA "se duerma" en búsquedas consecutivas, agrega siempre un `requestId` o timestamp único a la URL (`router.push(...?trigger=ai_search&requestId=${Date.now()})`). Esto fuerza a React a ejecutar el efecto nuevamente.

### C. Red de Seguridad contra Alucinaciones (Safety Nets)
**El Problema:** Cuando la IA no encuentra un parámetro, a veces "alucina" y coloca el **comando mismo** como valor (ej: Producto = "Movimientos detallados").
**Regla:**
-   **Lista Negra (Frontend):** Implementa siempre una validación que ignore frases genéricas del sistema si aparecen en campos de búsqueda.
    ```javascript
    const invalidPhrases = ['movimientos detallados', 'reporte de inventario', ...];
    if (invalidPhrases.includes(prod)) prod = null;
    ```
-   **Prompt Negativo (Backend):** Instruye explícitamente en el System Prompt: "NO inventes valores. Si no hay producto, déjalo vacío".

## 8. Protocolo de Reportes Unificados (Architecture Shift: Registry & Hooks)

Fecha de Implementación: 24 de Diciembre de 2025

**El Cambio de Paradigma:**
Inicialmente, cada reporte requería lógica manual en 4 puntos (Frontend, Router, Service, AI Tool). Esto escalaba mal (lógica repetida, errores de copia/pega como `generar_pdf_x` vs `generar_x_pdf`).
Se migró a una arquitectura de **"Registry + Hooks"**.

### A. Backend: The Registry Pattern
Ya no se usan `if/else` gigantes en `/dispatch-email`.
1.  **Registry Base:** Existe `app/core/reporting_registry.py` que define `BaseReport`.
2.  **Auto-Registro:** Cada servicio de reporte (ej: `reportes_inventario.py`) se decora con `@ReportRegistry.register`.
3.  **Contrato Único:** Todos deben implementar `generate_pdf(db, empresa_id, filtros)`.
4.  **Router Universal:** El endpoint `/dispatch-email` busca la clave del reporte en el registro y ejecuta ciegamente.

**Regla para Nuevos Reportes Backend:**
-   **NO** tocar `routes.py`.
-   **SÍ** decorar tu clase de servicio con `@ReportRegistry.register`.
-   **SÍ** definir una `key` única.

### B. Frontend: The Unified Hook (`useAutoReport`)
Ya no se parsean manualmente los parámetros `ai_email`, `ai_accion` en cada `page.js`.
1.  **Hook Único:** Se usa `const { triggerAutoDispatch } = useAutoReport('clave_reporte', callbackPdf)`.
2.  **Responsabilidad:** El hook maneja la lectura de URL, la limpieza de filtros (vacíos -> null), la llamada a la API y el manejo de errores (fallback a descarga si falla email).
3.  **Seguridad:** El hook usa `apiService` (autenticado) en lugar de `axios` puro.

**Regla para Nuevos Reportes Frontend:**
-   Importar `useAutoReport`.
-   Llamar `triggerAutoDispatch(filtros)` dentro del `useEffect` cuando `resultados.length > 0`.

## 9. LECCIONES APRENDIDAS Y PROTOCOLO DE ORO (MIGRACIÓN DE REPORTES)

**"Información Oro" para futuras implementaciones:**

### A. La Trampa del `async/await` en Interceptores
*   **Problema:** Al agregar lógica a `RightSidebar.js` o cualquier componente de ruta, es fácil copiar código que usa `await` (ej: `await fetch`) dentro de un bloque `if` sin verificar si la función padre es `async`.
*   **Síntoma:** "Build Error: await isn't allowed in non-async function".
*   **Solución:** Verificar siempre que `const executeClientAction = async (data) => { ... }` tenga la palabra clave `async`. Y tener CUIDADO EXTREMO al cerrar llaves `}`. Un cierre prematuro saca el código del scope de la función async.

### B. Mapeo de "Magic Strings" de IA (Logic Glue)
*   **Caso "TODOS":** La IA suele enviar `grupos: "all"` o `grupos: "todos"`. El Backend espera una lista de IDs `[1, 2, 3]`.
*   **Solución (Frontend Page):**
    *   No confiar en que la IA adivine los IDs.
    *   En el `useEffect` que procesa `ai_grupo`, detectar la cadena mágica "all".
    *   Si es "all", inyectar manualmente la opción de UI `{ label: "Seleccionar Todo", value: "all" }` Y la lista completa de opciones reales cargadas.
    *   *Código Oro:* `if (pAiGrupo === 'all') newFiltros.grupo_ids = [allOption, ...loadedGrupos];`

### C. La Trampa de Validación Pydantic (Backend)
*   **Problema:** El frontend envía campos vacíos como strings vacíos `""`. Pydantic (Backend) lanza error si el campo espera `Optional[int]`.
*   **Error:** `value is not a valid integer`.
*   **Solución (Hook `useAutoReport`):** El hook DEBE sanitizar antes de enviar.
    ```javascript
    Object.keys(filters).forEach(key => {
        if (filters[key] === '') clean[key] = null; // GOLD FIX
    });
    ```

### D. Definición de Herramientas IA (Agent)
*   **Lección:** No intentar forzar a `generar_reporte_movimientos` para que haga todo.
*   **Regla:** Si el reporte tiene filtros únicos (ej: "Grupos", "Rentabilidad", "Margen"), **CREAR UNA NUEVA TOOL** en `ai_agent.py` (ej: `generar_reporte_rentabilidad`). Es más barato y preciso que un prompt complejo.

## 10. PROTOCOLO DE CONTEXTO Y AMBIGÜEDAD (INTENT RECOGNITION)

**Reglas de Oro para evitar "Alucinaciones de Módulo":**

### A. Jerarquía de Prioridad (Módulo > Palabra Clave)
*   **SUPER EXCEPCIÓN:** Si el usuario pide explícitamente "Super Informe", "Auditoría" o "Buscador Global" -> USAR `consultar_documento`. Prioridad absoluta sobre reglas de cuentas.
*   **Problema:** El usuario dice "Auxiliar de cuenta *inventarios*". La IA ve la palabra "inventarios" y erróneamente asume que debe buscar en el módulo de inventario (Kardex).
*   **Solución:** Implementar **Prioridad de Módulo Explícito** en el `SYSTEM_PROMPT`.
    1.  Si el prompt empieza con *"Por Contabilidad"*, *"En el módulo contable"*, *"Desde contabilidad"*:
    2.  **IGNORAR** palabras clave de otros módulos.
    3.  FORZAR el uso de herramientas de contabilidad (`generar_reporte_movimientos`).
*   **Ejemplo:** *"Por contabilidad dame el auxiliar de inventarios"* -> Debe ir a Contabilidad, no a Inventarios.

### B. Ambigüedad Semántica (Diccionario de Sinónimos Estricto)
*   La IA tiende a confundir términos similares. Se debe "quemar" un diccionario en el prompt:
    *   **"Auxiliar", "Libro Auxiliar", "Auxiliar Contable":** SIEMPRE = `generar_reporte_movimientos` (Contabilidad).
    *   **"Kardex", "Existencias", "Movimientos de Stock":** SIEMPRE = `consultar_documento` o `super_informe` (Inventario).
    *   **"Ver movimiento", "Buscar factura":** = `consultar_documento` (Búsqueda General).

### C. Protocolo de Fechas por Defecto (Zero Friction)
*   **Problema:** El usuario dice *"Dame el auxiliar de caja"* (sin fechas). La IA suele preguntar "¿De qué fechas?" o fallar.
*   **Regla:** NO interrumpir al usuario para preguntar fechas obvias.
*   **Solución:** Asumir un rango generoso por defecto.
    *   `fecha_inicio`: **1 de Enero del año en curso** (o inicio de la empresa).
    *   `fecha_fin`: **Hoy**.
    *   *Filosofía:* Es mejor dar un reporte con *demasiada* información (que el usuario puede filtrar después) a no dar nada.

### D. La Trampa del Interceptor Frontend (Highjacking)
*   **Problema:** Aunque la IA elija correctamente la herramienta de Contabilidad (`generar_reporte_movimientos`), el Frontend (`RightSidebar.js`) puede tener un *interceptor* que detecta la palabra "inventario" y redirige forzosamente al módulo de Inventarios.
*   **Solución:** Los interceptores deben ser **Exclusivos**.
    *   *Código:* `const isInventario = query.includes('inventario') && !query.includes('contabilidad') && !query.includes('cuenta');`
    *   Si el usuario dice "Cuenta Inventarios" -> Es Contabilidad. NO interceptar.

### E. Búsqueda Difusa, Fonética y Desempate (Account Matching)
*   **Problema:** Al buscar "Inventarios exentos" o "Inventarios Grabados", el sistema suele fallar por ortografía ("Gravados") o seleccionar el Grupo "14 - Inventarios" en lugar de la cuenta auxiliar.
*   **Solución "Triple Capa" (Page.js):**

    1.  **Normalización Fonética (Super Tolerante):**
        *   Convertir todo a minúsculas y quitar tildes.
        *   **Reemplazos Clave:** `v -> b`, `z -> s`, `c -> s`.
        *   *Resultado:* "Grabados" empata perfectamente con "Gravados" (+100 Puntos).

    2.  **Prioridad de Hojas (Leaf Boosting):**
        *   Si la cuenta es un **Auxiliar** (no tiene hijos), sumar **+25 Puntos**.
        *   *Efecto:* Entre el Grupo (14) y la Cuenta (143505), la cuenta empieza ganando.

    3.  **Desempate por Longitud (Tie-Breaker):**
        *   Si hay empate final en puntos (ej: ambos coinciden con la palabra "Inventarios"), el sistema elige la cadena de texto **MÁS LARGA**.
        *   *Lógica:* Los nombres cortos suelen ser títulos de grupo ("Inventarios"). Los nombres largos suelen ser cuentas específicas ("Inventarios de Mercancías Gravados").
        *   *Resultado:* Gana la cuenta específica.

## 11. PROTOCOLO DE CONTROL POR VOZ EN FORMULARIOS (AUTO-FILL)

**Objetivo:** Permitir que la IA diligencie formularios complejos (como Captura Rápida) basándose en comandos naturales, incluyendo lógica de guardado automático.

### A. Estrategia de "Auto-Fill" Diferido (The 3-Stage Rocket)
El formulario de Captura Rápida nos enseñó que no se puede hacer todo en un solo `useEffect` debido al problema de "Stale Closures" (variables no actualizadas). Se debe dividir en fases:

1.  **Fase 1 (Matching):** 
    *   Detecta `ai_plantilla` y `ai_tercero`.
    *   Ejecuta la búsqueda fuzzy y selecciona los IDs.
    *   **NO** intenta poner el valor todavía (porque los movimientos no se han renderizado).

2.  **Fase 2 (Value Injection):**
    *   Escucha cambios en `movimientos`.
    *   Si `ai_valor` existe en la URL y los movimientos ya cargaron -> Aplica el valor.
    *   **LIMPIEZA:** Inmediatamente borra los parámetros de la URL (`window.history.replaceState`) para evitar bucles infinitos.

3.  **Fase 3 (Auto-Save):**
    *   Escucha si el formulario está `balanceado` y si hay un valor total.
    *   Usa un `setTimeout` de seguridad (ej: 2 segundos) para dar feedback visual al usuario.
    *   Simula el click físico: `document.getElementById('btn-guardar').click()`.

### B. Lección: "El Portero Ciego" (RightSidebar)
**El Problema:** La IA enviaba correctamente `{'valor': '35000'}`, pero el Frontend no lo leía.
**La Causa:** `RightSidebar.js` tenía una lista blanca muy estricta (`p.debito || p.credito`).
**La Solución:** Ampliar la "visión" del portero para aceptar sinónimos paramétricos:
```javascript
const val = p.valor || p.monto || p.debito || p.credito || p.importe;
```

### C. Feedback de Usuario
*   Es vital mostrar **Toasts** informativos progresivos:
    1. "IA: Plantilla detectada..."
    2. "IA: Beneficiario asignado..."
    3. "IA: Valor asignado..."
    4. "IA: Todo listo. Guardando automáticamente... 💾"
*   Esto convierte una caja negra en una experiencia mágica y transparente.

