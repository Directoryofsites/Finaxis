# PROTOCOLO DE AUTOMATIZACI√ìN E INTEGRACI√ìN IA (Reportes y Comandos de Voz)

**Versi√≥n:** 1.0
**Fecha:** 23 de Diciembre de 2025
**Generado por:** Agente Antigravity (Google Deepmind)
**Contexto:** Integraci√≥n de comandos de voz (WhatsApp, PDF, Email) sobre reportes existentes en React.

---

## 1. Introducci√≥n
Este documento registra las lecciones aprendidas, los obst√°culos t√©cnicos ("tropezones") y las soluciones est√°ndar ("Protocolo") para implementar funcionalidades de automatizaci√≥n controladas por IA en la arquitectura actual de ContaPY2 (Next.js + Python FastAPI).

Cualquier futura implementaci√≥n de comandos del tipo **"Genera X reporte y env√≠alo por Y"** debe seguir estas reglas para evitar regresiones.

---

## 2. El Desaf√≠o de la Sincronizaci√≥n (Race Conditions)

### El Problema
Al ejecutar un comando complejo (ej: "Auxiliar de Jhovana Martinez cuenta Caja"), el frontend debe realizar m√∫ltiples pasos as√≠ncronos secuenciales:
1. Cargar la p√°gina.
2. Buscar y seleccionar el Tercero (Jhovana).
3. Esperar que carguen las cuentas de ese tercero.
4. Buscar y seleccionar la Cuenta (Caja).
5. Generar el reporte.
6. Exportar/Enviar (PDF/WhatsApp).

**El error com√∫n:** El sistema intenta realizar el paso 4 o 5 antes de completar el 2 o 3, resultando en reportes vac√≠os, interfaces congeladas ("Processando..."), o selectores fallidos.

### Protocolo de Soluci√≥n
1.  **NO limpiar la URL prematuramente**:
    *   *Error:* Hacer `window.history.replaceState` en el primer `useEffect` (carga de tercero).
    *   *Consecuencia:* El segundo `useEffect` (carga de cuentas) intenta leer los par√°metros de la URL, pero ya han sido borrados.
    *   *Regla:* La limpieza de URL debe hacerse **DIFERIDA**, solo despu√©s de que el reporte se haya generado exitosamente (generalmente en el evento final de √©xito o tras un timeout largo).

2.  **Timeouts Robustos "Triple Armor"**:
    *   Depender solo de `useEffect` ([dep1, dep2]) es fr√°gil en formularios complejos.
    *   Usar `setTimeout` con m√°rgenes de seguridad (ej. 1200ms - 1500ms) para simular el click humano una vez los datos est√°n poblados.
    *   *Ejemplo:* `setTimeout(() => document.getElementById('btn-consultar').click(), 1500);`

3.  **Fallback de Robustez (Intenci√≥n de Usuario)**:
    *   Si la IA solicita una cuenta espec√≠fica (ej. "Caja General") pero esta no existe en la lista del tercero:
    *   **NO** detener el proceso.
    *   **S√ç** advertir (`toast.warn("Cuenta no encontrada, mostrando todas")`), seleccionar `ALL` (todas), y **EJECUTAR** el reporte de todas formas.
    *   *Raz√≥n:* El usuario prioriza recibir el informe (aunque sea general) a que el sistema se quede esperando correcciones.

---

## 3. Protocolo de Descarga y Env√≠o

### Descarga de PDF
*   **Problema:** Los navegadores bloquean `window.open(url)` si no es resultado directo de un click de usuario (popup blocker), o a veces la descarga no inicia en m√≥viles.
*   **Implementaci√≥n Correcta (Backend):**
    *   Endpoint debe incluir header: `Content-Disposition: attachment; filename="reporte.pdf"`.
*   **Implementaci√≥n Correcta (Frontend):**
    *   Usar `window.location.href = pdfUrl;` para forzar la navegaci√≥n/descarga directa en la misma pesta√±a. Es m√°s compatible que crear elementos `<a>` invisibles din√°micos.

### Env√≠o por Correo
*   Se cre√≥ un servicio centralizado en Backend (`/api/reports/dispatch-email`).
*   **Estructura:**
    *   Frontend env√≠a: `{ report_type: 'nombre_reporte', email_to: 'x@y.com', filtros: {...} }`
    *   Backend reutiliza la l√≥gica de generaci√≥n de PDF existente (`documento_service`), genera el binario en memoria y lo adjunta al correo usando `EmailService`.
*   *Nota:* No duplicar l√≥gica de generaci√≥n de PDF. El endpoint de correo debe llamar a la misma funci√≥n que el endpoint de impresi√≥n.

---

## 4. Checklist para Nuevos Reportes

Si se va a agregar voz a un nuevo reporte, copiar el patr√≥n de `balance-de-prueba/page.js`:

1.  [ ] **Imports:** Agregar `toast` de `react-toastify`.
2.  [ ] **State:** Agregar `autoPdfTrigger`, `wppNumber`, `emailAddress`, `lastProcessedParams`.
3.  [ ] **URL Parsing:** En el `useEffect` de carga, leer params. **NO BORRAR URL AQUI**.
4.  [ ] **Bot√≥n Simulado:** Usar `setTimeout` para hacer click en el bot√≥n de generar (evita l√≥gica duplicada de generaci√≥n).
5.  [ ] **Effect de Automatizaci√≥n:** Escuchar cambios en `reportData`. Si `autoPdfTrigger` es true y hay datos:
    *   Llamar `handleExportPDF`.
    *   Si hay wpp, abrir `wa.me`.
    *   Si hay email, llamar `handleSendEmail`.
6.  [ ] **Limpieza:** Solo al final del proceso limpiar variables y URL.

---
*Este documento debe ser consultado antes de realizar modificaciones a la l√≥gica de reportes.*

## 5. ConfiguraciÛn del Servicio de Correo (SMTP)

### Lecciones Aprendidas (Gmail)
Al configurar el envÌo de correos con Gmail (smtp.gmail.com), hemos encontrado bloqueos de seguridad que requieren pasos especÌficos.

1.  **NO usar contraseÒa normal:** Gmail rechaza (Error 535) las contraseÒas de inicio de sesiÛn est·ndar.
2.  **Usar App Passwords:** Es OBLIGATORIO generar una "ContraseÒa de aplicaciÛn" de 16 caracteres.
    *   *Ruta:* Cuenta Google > Seguridad > VerificaciÛn en 2 pasos > ContraseÒas de aplicaciones.
    *   *Formato:* bcd efgh ijkl mnop (el sistema debe eliminar los espacios al guardarla).

### Manejo de Variables de Entorno (.env)
1.  **Reinicio Obligatorio:** Python (uvicorn/astapi) carga el archivo .env **solo al iniciar**. Si se actualizan credenciales en el .env, el Backend **DEBE REINICIARSE** manualmente para que los cambios surtan efecto.
2.  **Riesgo de CorrupciÛn (Encoding):**
    *   Al editar .env con comandos de PowerShell (Set-Content), existe riesgo de cambiar la codificaciÛn a UTF-16, lo que hace que Python lea variables como None o con caracteres extraÒos (\x00).
    *   **SoluciÛn:** Usar scripts de Python (open(..., encoding='utf-8')) para escribir en el .env de forma segura, o editores de texto plano.
3.  **DiagnÛstico:** Si las credenciales parecen correctas pero falla el login, usar un script de diagnÛstico (smtplib.SMTP(...).login()) para verificar quÈ est· viendo realmente Python.


## 6. MÛdulo de Correo Din·mico (SaaS)

Se implementÛ un sistema para que cada empresa configure su propio servidor SMTP, eliminando la dependencia del archivo .env global.

### Arquitectura
1.  **Seguridad (Fernet):** Las contraseÒas se almacenan encriptadas en la tabla empresa_config_email.
    *   Requiere una ENCRYPTION_KEY persistente en el .env. Si esta llave se pierde, los correos configurados deben reingresarse.
2.  **Frontend:** Nuevo men˙ en *Admin > Herramientas > ConfiguraciÛn Correo* para autogestiÛn del cliente.
3.  **Backend:** EmailService ahora consulta primero la DB usando el ID de la empresa del usuario. Si no encuentra configuraciÛn propia, (opcionalmente) hace fallback al .env del servidor.

### Flujo de Usuario
*   El cliente obtiene su **ContraseÒa de AplicaciÛn** de Google (Requisito ineludible).
*   Ingresa correo y clave en el mÛdulo web.
*   El sistema valida conexiÛn antes de guardar.
*   A partir de ahÌ, todos los comandos de voz (Envia un pdf...) usan SU cuenta como remitente.
