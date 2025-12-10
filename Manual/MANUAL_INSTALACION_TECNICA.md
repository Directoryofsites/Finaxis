# Manual Técnico de Instalación y Despliegue - Finaxis

Este documento está dirigido al **Distribuidor / Soporte Técnico**. Explica cómo instalar el sistema, los requerimientos, y responde las dudas estratégicas sobre personalización y seguridad.

---

## 1. Requerimientos del Sistema (Cliente)

Para que Finaxis funcione correctamente en el PC del cliente, se debe cumplir con lo siguiente:

### Hardware Mínimo
*   **Procesador:** Intel Core i3 (8va Gen) o equivalente AMD. Reutilizable i5/i7 recomendado.
*   **Memoria RAM:** 8 GB (Mínimo absoluto). Recomendado 16 GB si va a tener el motor de base de datos local.
*   **Disco Duro:** SSD (Disco de Estado Sólido) es obligatorio para el rendimiento de la base de datos.
*   **Espacio:** 2 GB para el programa + Espacio para Base de Datos (crece con el tiempo).

### Software / Sistema Operativo
*   **Sistema Operativo:** Windows 10 (Build 19041 o superior) o Windows 11. **SOLO 64 BITS**.
    *   *Nota:* NO funciona en Windows 7 ni en versiones de 32 bits.
*   **Motor de Base de Datos:** PostgreSQL 14, 15 o 16.
    *   Debe estar instalado previamente en el equipo (o en un servidor de la red).
*   **Navegador:** Google Chrome, Microsoft Edge o Firefox (Actualizados).

---

## 2. Proceso de Instalación

El instalador actual (`Installer_V1`) es de tipo **PORTABLE**. No "instala" cosas en el registro de Windows, lo cual es excelente para evitar conflictos.

### Pasos:
1.  **Instalar PostgreSQL:** Si el cliente no tiene servidor, instale PostgreSQL en el PC principal.
    *   Cree una base de datos vacía llamada `contapy_db`.
    *   Anote la contraseña del usuario `postgres`.
2.  **Copiar la Carpeta:** Lleve la carpeta `Installer_V1` (puede renombrarla a `Finaxis`) y péguela en el disco `C:\` o `D:\`. Recomendamos rutas cortas y sin espacios (ej: `C:\Finaxis`).
3.  **Configurar Conexión (.env):**
    *   Entre a la carpeta `backend` y abra el archivo `.env`.
    *   Edite la línea `DATABASE_URL` con la clave real del PostgreSQL de ese cliente.
4.  **Iniciar:** Ejecute `INICIAR_SISTEMA.bat`.

---

## 3. Guía Estratégica para el Creador (Usted)

A continuación, respondemos sus dudas críticas sobre seguridad y modelo de negocio.

### A. ¿El instalador es personalizable por cliente?
**Estrategia recomendada: Instalador Genérico + Respaldo Personalizado.**

*   **No re-compile el instalador para cada cliente.** Eso es ineficiente. Use el mismo ejecutable (`FinaxisServer.exe`) para todos.
*   **¿Cómo personalizo la empresa?**
    1.  En su oficina (PC de desarrollo), cree la empresa del cliente, configure sus impuestos, logo y parámetros iniciales.
    2.  Genere un **BACKUP (Respaldo)** de esa base de datos específica.
    3.  En el PC del cliente, instale el programa "vacío" (Genérico).
    4.  **Restaure el Backup** de su oficina en el PC del cliente.
    *   *Resultado:* El cliente abre el programa y ya ve SU empresa con todo configurado, sin que usted haya tenido que programar un instalador distinto.

### B. ¿Debo loguearme con mi clave de Soporte en el PC del cliente?
**RIESGO ALTO.** Si usted digita su clave maestra (`Jh8...`) en un teclado desconocido, un *keylogger* podría robarla.

**Solución:**
Use la estrategia del punto A (Respaldo Personalizado).
1.  Usted hace todo el trabajo "sensible" (crear empresa, asignar cupos) en **SU COMPUTADOR SEGURO**.
2.  Al cliente solo le lleva los **DATOS YA LISTOS** (el backup).
3.  Así, nunca tiene que escribir la clave de Soporte Global en el PC del cliente. El cliente entra directo con su usuario `admin@cliente.com`.

### C. Seguridad contra Hackers
El sistema tiene 3 capas de seguridad:

1.  **Código Compilado:** El backend está en `.exe`. Es difícil (aunque no imposible) de leer para un humano. Protege su lógica de negocio.
2.  **Frontend Ofuscado:** El código React está "minificado". Es ilegible.
3.  **PUNTO DÉBIL ACTUAL (El archivo .env):**
    *   En la carpeta `backend` queda un archivo de texto `.env` con la clave de la base de datos.
    *   **Mitigación:** Configurar el PostgreSQL del cliente para que solo acepte conexiones desde `localhost` (el mismo PC). Así, si roban la clave, no pueden conectarse desde internet.

### D. Cupos y Licencias (Modelo de Negocio)
**Sí, los cupos funcionan nativamente.**
El control de cupos (ej: 1500 registros/mes) está programado dentro del `FinaxisServer.exe`.
*   Cuando usted crea la empresa (en su oficina), le asigna el cupo.
*   Ese dato viaja en el Backup a la base de datos del cliente.
*   El `.exe` lee ese dato y bloquea si se pasan.
*   **¿Pueden hackear el cupo?** Solo si saben entrar a la base de datos PostgreSQL y modificar la tabla `empresas` manualmente. Para protegerse de esto, en el futuro implementaremos "Licencias Firmadas Digitalmente", pero por ahora, el modelo es funcional para distribución local.
