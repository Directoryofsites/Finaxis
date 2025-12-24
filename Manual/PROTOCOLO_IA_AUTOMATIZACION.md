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
