# ESTUDIO TÉCNICO: Parametrización de Correo por Cliente (SMTP Dinámico)

**Fecha:** 23 de Diciembre de 2025
**Objetivo:** Permitir que cada empresa/cliente configure su propia cuenta de correo ("Remitente") desde el software, eliminando la dependencia del archivo `.env` del servidor.

---

## 1. Situación Actual vs. Deseada

### Actual (Estático)
*   Las credenciales (`GMAIL_USER`, `GMAIL_PASSWORD`) están escritas en un archivo de texto (`.env`) en el servidor.
*   **Problema:** Si tienes 10 clientes usando el mismo software, todos envían correos desde la misma cuenta (la del dueño del software). O si es instalado en local, el usuario debe editar archivos técnicos, lo cual es propenso a errores.
*   **Reinicio:** Requiere apagar y prender el servidor para cambios.

### Deseada (Dinámico)
*   **Interfaz Gráfica:** El gerente entra a *Configuración > Correo*, pone su Gmail y su Clave de Aplicación.
*   **Base de Datos:** Esa información se guarda (encriptada) en la base de datos de su empresa.
*   **Ejecución:** Cuando Jhovana o un auxiliar envían un PDF, el sistema busca "¿Qué correo tiene configurada esta empresa?", lo desencripta y lo usa para enviar.

---

## 2. Arquitectura de la Solución

Para lograr esto, necesitamos modificar 3 capas del sistema:

### A. Base de Datos (Seguridad Crítica)
No podemos guardar la contraseña como texto plano (cualquier técnico de base de datos la vería).
*   **Tabla:** `configuracion_empresa` (o nueva tabla `configuracion_smtp`).
*   **Campos:**
    *   `smtp_email`: varchar (ej: `gerencia@cliente.com`)
    *   `smtp_password_encrypted`: bytea/text (La clave encriptada)
    *   `smtp_host`: default `smtp.gmail.com`
    *   `smtp_port`: default `587`
*   **Cifrado:** Usar una librería de criptografía simétrica (como `Fernet` de Python). El servidor tiene una "llave maestra" interna para abrir y cerrar estos secretos.

### B. Backend (Python/FastAPI)
Refactorizar `EmailService`. Actualmente "nace" con las credenciales del `.env`.
*   **Nuevo flujo:**
    1.  Recibe petición: "Enviar reporte X".
    2.  Identifica al usuario -> Obtiene su `empresa_id`.
    3.  Consulta DB -> Trae credenciales SMTP de esa empresa.
    4.  Desencripta clave.
    5.  Abre conexión SMTP temporal (`server.login(usuario_db, clave_db)`).
    6.  Envía y cierra.

### C. Frontend (React)
Nuevo Módulo: **Configuración de Servidor de Correo**.
*   Formulario con campos: Correo, Contraseña (tipo password).
*   **Botón vital: "PROBAR CONEXIÓN"**.
    *   El usuario no debe poder guardar si la prueba falla. Esto evita que guarden claves erróneas y luego los reportes fallen silenciosamente.
*   **Guía Visual:** Debe incluír un link directo o tutorial pequeño sobre cómo sacar la "App Password" de Gmail, ya que este requisito de Google NO desaparece.

---

## 3. Análisis de Riesgos y "Tropezones" Esperados

1.  **El Factor Humano (App Passwords):**
    *   Aunque el software permita configurar el correo, el usuario **seguirá necesitando crear la Contraseña de Aplicación en Google**. El software no puede saltarse esa seguridad de Google.
    *   *Mitigación:* Poner el link directo a `myaccount.google.com/apppasswords` en la pantalla de configuración.

2.  **Bloqueos de Seguridad:**
    *   Si el usuario cambia su clave de Gmail normal, a veces Google revoca las App Passwords. El sistema dejará de enviar correos repentinamente.
    *   *Mitigación:* Dashboard de "Estado del Sistema" que alerte si los correos están rebotando.

3.  **Lentitud (Performance):**
    *   Conectar al SMTP de Gmail toma tiempo (1-3 segundos). Si hacemos esto en tiempo real, el usuario verá el spinner girando.
    *   *Mitigación:* Usar "Colas de Tareas" (Background Tasks). El usuario recibe "Su correo se está enviando..." inmediatamente, y el servidor lo procesa en segundo plano. Si falla, se le notifica después.

---

## 4. Conclusión del Experto
Es una mejora **altamente recomendable y necesaria** para un software multi-cliente (SaaS) o para profesionalizar la entrega.

**Nivel de Esfuerzo:** Medio-Alto.
*   Requiere migraciones de base de datos.
*   Requiere manejo de encriptación (delicado).
*   Requiere nueva UI.

**Beneficio:**
*   Autonomía total del cliente.
*   Marca blanca (los correos salen con SU nombre, no el del proveedor).
*   Centralización (el gerente configura una vez, y todos los auxiliares usan esa cuenta automáticamente).
