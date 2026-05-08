# 📓 BITÁCORA MAESTRA DE DESARROLLO - FINAXIS

Este archivo contiene el historial técnico y la "sustancia" del proyecto, protegido contra los recortes del sistema de logs.

---

## 📜 PROTOCOLO DE DESARROLLO Y REGLAS DE ORO

Para garantizar la estabilidad del sistema (especialmente en Render/Producción), seguiremos estas reglas estrictas:

### 1. Gestión de Base de Datos (Doble Garantía)
Cuando se realicen cambios en el esquema de la BD, **SIEMPRE**:
1.  **Modificar el Modelo:** Actualizar el archivo correspondiente en `app/models/` (ej: `concepto.py`).
2.  **Doble Registro:** 
    *   Registrar el cambio en **Alembic** (para el historial formal de migraciones).
    *   Registrar la columna en `app/core/auto_migrate.py` (para que Render/Producción la aplique inmediatamente al reiniciar).
3.  **Migración Explícita:** Crear una migración formal (`flask db migrate`). **No depender exclusivamente de la magia del auto-migrate para producción.**
4.  **Sincronización:** Subir a GitHub el **Código + La Migración** en el mismo commit/push.

### 2. Flujo de Despliegue en Producción (Render)
Para evitar errores de "columna no encontrada" al arrancar el código nuevo:
1.  **Ejecutar Migración Primero:** Correr `flask db upgrade` en el entorno de producción.
2.  **Verificar:** Comprobar con `psql` o logs que las columnas existen.
3.  **Desplegar Código:** Una vez confirmada la BD, proceder a servir/reiniciar la aplicación con el código nuevo.

---


## 🏁 Estado Actual (6 de mayo de 2026)

### 1. Sistema de Facturación (PH) - CORREGIDO ✅
- **Problema:** Los conceptos se debitaban a cuentas de banco en lugar de cartera.
- **Solución:** Se limpió la base de datos (script `fix_ph_conceptos.py`) y se validó en el backend que la cuenta de cartera sea siempre clase 13.
- **Cambio Clave:** Se agregaron campos de "Cuenta de Cartera" e "Intereses" en el modal de conceptos del frontend.

### 2. Infraestructura del Instalador - LISTO ✅
- **Arquitectura:** Modo `standalone` (Node.js portátil + Backend Python).
- **Herramientas:** PyInstaller para el ejecutable y Inno Setup 6 para el instalador `.exe`.
- **Ubicación:** `dist/instalador/FinaxisSetup_v1.0.exe`.
- **Comando de Build:** `build_instalador.bat` (ejecuta todo el proceso).

### 3. Seguridad y Licenciamiento - IMPLEMENTADO ✅
- **Ofuscación:** PyArmor (Trial) para archivos críticos (`licencia.py`, `security.py`).
- **Lógica:** Límite de 200 registros mensuales en modo Demo; activación mediante llave firmada.

### 4. Sistema de Exportación de Chat - MEJORADO ✅
- **Scripts:** `scratch/export_chat.py` (individual) y `export_all_chats.py` (masivo).
- **Mejora:** Ahora capturan comandos (`run_command`) y código (`write_to_file`), eliminando el ruido técnico.

---

## 🧠 ANÁLISIS DE INGENIERÍA: Arquitectura del Instalador

Este apartado documenta el razonamiento técnico detrás de las decisiones clave para evitar que el conocimiento se pierda en logs recortados.

### 1. El Dilema: `next export` vs `output: standalone`
Originalmente intentamos usar la exportación estática (`out/`), pero falló debido a la naturaleza dinámica de Finaxis.

*   **¿Por qué falló `next export`?**
    - Finaxis usa **Rutas Dinámicas** (ej: `/admin/empresas/[id]`).
    - Next.js exige conocer todos los `[id]` en tiempo de compilación para generar archivos HTML físicos. Como los IDs se crean en la base de datos del cliente, es imposible pre-generarlos.
    - Obligaba a cambiar toda la navegación a "Query Parameters" (`?id=...`), lo cual degradaba la arquitectura actual.

*   **La Solución: Arquitectura Standalone (Servidor en el Desktop)**
    - Decidimos empaquetar un **mini-servidor Node.js** junto con el ejecutable de Python.
    - **Ventaja:** Permite que todas las rutas dinámicas, el manejo de sesiones y el renderizado del lado del cliente funcionen EXACTAMENTE igual que en la web.
    - **Costo:** El instalador pesa aproximadamente 100MB más (por el motor de Node), pero la estabilidad es del 100%.

### 2. Flujo de Comunicación en Local
Para que el programa funcione sin internet y de forma fluida:
1.  **Lanzador Python (`run_local.py`):** Inicia el backend de FastAPI en el puerto `8765`.
2.  **Servidor Frontend (Node.js):** Sirve la app de Next.js en el puerto `3000`.
3.  **Puente:** El frontend habla con `localhost:8765` para todas las operaciones de base de datos.
4.  **Base de Datos:** Se usa **SQLite** por defecto, almacenando el archivo `.db` en la carpeta de datos de usuario para asegurar que no se borre al actualizar el programa.

### 3. Estrategia de Seguridad (Protección de IP)
Dado que es una aplicación que vive en la PC del cliente, la ofuscación es vital:
- **PyArmor:** Protege la lógica de licencias. Aunque es versión Trial, es suficiente para "romper" los descompiladores automáticos en los 7 archivos más sensibles.
- **Compilación Bytecode:** Todo el resto del backend se distribuye como `.pyc`, no como código fuente `.py`.

---

---

## 🏁 Actualización de Sesión (6 de mayo de 2026)

### 1. Hallazgo Técnico: Persistencia de BD Local y "Dilema del Seeder"
- **Diagnóstico:** Se identificó que la base de datos local (`finaxis_local.db`) reside en `%APPDATA%\Finaxis\` y **persiste** incluso después de desinstalar el programa.
- **Problema:** El archivo `app/core/seeder.py` utiliza una lógica de "Solo si no existe". Si el usuario `soporte@soporte.com` ya existe en el archivo `.db` del cliente, el sistema **ignora** cualquier cambio de contraseña realizado en el código fuente durante una nueva compilación.
- **Regla de Oro Local:** Para forzar cambios en usuarios/configuraciones base en una PC que ya tenía Finaxis, se debe **borrar o renombrar** manualmente el archivo `finaxis_local.db` en `%APPDATA%`.

### 2. Automatización de Memoria (Exportación de Chats) ✅
- **Script Mejorado:** `scratch/export_chat.py` ahora es **dinámico**.
- **Cambio:** Se eliminó la necesidad de pegar el ID de conversación manualmente. El script ahora detecta automáticamente la carpeta más reciente en el sistema de logs (`brain/`), permitiendo exportar el chat actual con un solo comando.

### 3. Protocolo "Safety Restore" (Cinturón de Seguridad) 🔒
- **Ubicación:** `%APPDATA%\Finaxis\backups\safety`.
- **Función:** El sistema ahora genera un archivo `.json` (Snapshot) **automáticamente** cada vez que un usuario intenta restaurar un backup. 
- **Propósito:** Permitir una "vuelta atrás" inmediata si una importación de datos sale mal o si el usuario se arrepiente de sobrescribir su información actual.

### 5. Asistente de Bienvenida (Setup Wizard) - NUEVO ✅
- **Objetivo:** Eliminar la necesidad de usar el usuario de soporte para la configuración inicial.
- **Flujo:** Si el sistema detecta 0 empresas en la BD, redirige automáticamente a `/setup`.
- **Acción:** Crea la primera empresa y el administrador global con el rol "Administrador" de forma pública pero protegida (solo funciona una vez).


---

## 🚀 VISIÓN A FUTURO: IA como Soporte de Nivel 0

Hemos identificado una oportunidad disruptiva para escalar Finaxis en la web: **Integrar un Agente de IA Diagnóstico** directamente en la plataforma.

### 1. El Concepto
Permitir que el usuario final pregunte cosas como: *"¿Por qué mi balance no cuadra?"* o *"¿Por qué este pago no aparece en cartera?"*. La IA, con permisos controlados de lectura, analizará la base de datos de esa empresa específica para encontrar el error técnico (ej: cuenta contable mal enlazada en un concepto).

### 2. Implementación Técnica (Roadmap)
- **Backend:** Crear un servicio `DiagnosticAgent` usando Gemini (Functions/Tools).
- **Herramientas:** Definir funciones como `inspect_concept_config()` o `verify_puc_integrity()`.
- **Seguridad:** Aislamiento estricto por `empresa_id` para garantizar que la IA nunca cruce datos entre clientes.

### 3. Impacto
Transformar Finaxis de una herramienta pasiva a una plataforma que se "auto-diagnóstica", reduciendo la carga de soporte humano en un 80% y eliminando la fricción para el usuario final.

---

## 🏁 Actualización de Sesión (7 de mayo de 2026)

### 1. Generador de Licencias Móvil (Soporte-Only) ✅
- **Objetivo:** Permitir la generación de seriales de activación desde cualquier lugar (móvil) sin exponer la clave maestra.
- **Implementación:**
    - **Backend:** Nuevo endpoint seguro `/api/soporte/licencias/generar` protegido por el permiso `soporte:acceder_panel`.
    - **Sincronización:** La lógica utiliza el mismo algoritmo `itsdangerous` y `CLAVE_MAESTRA` que el validador local, garantizando compatibilidad total.
    - **Frontend:** Pestaña "Generar Licencia 🔑" integrada en el panel de utilidades de soporte.

### 2. Lógica Inteligente de Límites (Full, Lite, Demo) ✅
- **Mejora:** El generador ahora es "inteligente" y ajusta automáticamente los límites de registros según la versión elegida:
    - **FULL:** Ilimitado (-1).
    - **LITE:** 200 registros mensuales.
    - **DEMO:** 50 registros mensuales.
- **Visual:** Se añadieron etiquetas dinámicas en el selector para evitar errores de soporte durante la fabricación del serial.

### 3. Robustez en Creación de Empresas ✅
- **Self-Healing de Roles:** Se corrigió el error 500 que ocurría al crear empresas si el rol "Administrador" no existía en la base de datos local del cliente.
- **Solución:** El servicio `empresa.py` ahora busca el rol de forma insensible a mayúsculas y, si no lo encuentra, lo crea dinámicamente con los permisos base necesarios.

### 4. Definición de Estrategia de Datos (El Secreto de Soporte) 🔒
- **Clasificación:** Se estableció que `finaxis_local.db` es un archivo técnico de **uso exclusivo para soporte**.
- **Seguridad:** No se recomienda informar al cliente sobre la existencia de este archivo para evitar manipulaciones externas de la licencia o la estructura.
- **Backup vs DB:** El backup del menú (JSON) es la herramienta de usuario para portabilidad de datos; el `.db` es el contenedor maestro para recuperación forense y gestión de licencias.

---

## 🏁 Actualización de Sesión (8 de mayo de 2026)

### 1. Estabilización de Creación de Empresas Locales (SQLite)
- **Fix UnboundLocalError (`or_`):** Se corrigió un error en `dashboard.py` que impedía ver el consumo de registros en instalaciones locales debido a un alcance de variable incorrecto en SQLAlchemy.
- **Estabilización de Roles en SQLite:** Se implementó una lógica de `roles_override` en `empresa.py` para evitar errores 404 al crear empresas en ambientes locales donde los roles "Administrador" o "Contador" se crean dinámicamente y no son visibles inmediatamente por sub-procesos de base de datos.
- **Robustez del Instalador:** Se verificó que el sistema de "Autocuración" sea capaz de inicializar una base de datos vacía (`finaxis_local.db`) sin fallar si faltan roles base, garantizando que el primer inicio sea exitoso para el cliente.
### 2. Soporte Bidireccional y Portal Público ✅
- **Implementación:** Se habilitó el endpoint `GET /api/soporte/tickets/me` para que los terceros (clientes) puedan ver el historial de sus PQRs desde el portal.
- **Visualización:** Se actualizó `CustomerPortalFull.js` para mostrar las respuestas del administrador (`respuesta_soporte`), permitiendo una comunicación fluida entre el cliente y el soporte técnico.

### 3. Flexibilidad en Licenciamiento Local (Rol Contador) ✅
- **Permisos:** Se modificó `app/api/licencia/routes.py` para incluir al rol `contador` en la lista de administradores autorizados (`_ROLES_ADMIN`).
- **Contexto:** Esto permite que los usuarios que instalan Finaxis localmente (usualmente contadores independientes) puedan activar y gestionar sus llaves de licencia sin requerir un usuario con rol "administrador" explícito.

### 4. Mejora de UX: Monitor de Asientos Rediseñado ✅
- **Cambio:** Se eliminó el panel lateral estrecho ("el pedacito") que se abría al hacer clic en el rayito de la barra fija.
- **Redirección:** Ahora el botón redirige directamente a `/contabilidad/captura-rapida/monitor` (página completa), aprovechando todo el ancho de pantalla para la auditoría de movimientos.
- **Optimización:** Se eliminó el código muerto y el estado de monitorización del componente `RightSidebar.js`.

### 5. Robustez en Consumo (Bypass SQL Puro) ✅
- **Problema:** En SQLite local, la "ceguera de sesión" de SQLAlchemy impedía ver registros recién creados por procesos concurrentes, causando `IntegrityError` incluso con manejadores de excepciones estándar.
- **Solución Nuclear:** Se implementó un **Bypass de SQL Puro**. Se utiliza `INSERT OR IGNORE` para garantizar la existencia del plan a nivel de disco y un objeto **PlanProxy** que intercepta las actualizaciones y las ejecuta mediante comandos `UPDATE` directos, puenteando el sistema de objetos del ORM.
- **Resultado:** Estabilización total de la persistencia en entornos locales. El sistema es ahora inmune a bloqueos de sesión y colisiones de unicidad en el control de planes mensuales.

### 6. Herencia de Licencia para Empresas Hijas (Contadores) ✅
- **Problema:** Las empresas hijas creadas por contadores licenciados aparecían "bloqueadas" o sin cupo debido a que la lógica no propagaba la licencia del padre.
- **Solución:** Se implementó compatibilidad multi-dialecto en `consumo_service.py`.

### [2026-05-08] Estabilización de Visibilidad en Monitor de Asientos
- **Problema**: Las Facturas de Propiedad Horizontal (FPH) eran invisibles en el Monitor de Asientos, aunque aparecían en el Super Informe.
- **Causa Raíz**: 
    1. El Monitor solo filtraba terceros por la cabecera del documento, mientras que las FPH suelen tener el tercero en los movimientos contables.
    2. Inconsistencia de parámetros: el frontend enviaba `tipo_documento_id` y el backend esperaba `tipos_documento_ids`.
    3. Desajuste de fechas: El monitor abre por defecto el mes actual (Mayo), mientras que los datos de prueba eran de Abril.
- **Solución**:
    - Se actualizó `libros_oficiales.py` con `LEFT JOIN` y lógica de `COALESCE` para terceros.
    - Se flexibilizó la ruta `/journal` en `api/reports/routes.py` para aceptar ambos formatos de ID de tipo.
    - Se alinearon los labels de las columnas con las expectativas del frontend.
    - Se añadieron logs `[ESPIA-MONITOR]` para depuración en tiempo real.
 Si la empresa padre (Contador) está licenciada (Cupo >= 999,999 o `licencia_key` válida), todas sus empresas hijas heredan automáticamente el estatus de cupo ILIMITADO.
- **Impacto:** Un contador licencia su oficina una sola vez y puede crear infinitas empresas clientes que funcionan de inmediato sin configuraciones adicionales.

### 7. Estabilización de Atributos y Compatibilidad Proxy ✅
- **Mejora:** Se dotó al `PlanProxy` de todos los atributos del modelo original (`anio`, `mes`, `empresa_id`) y se blindó el acceso a campos de licencia en el modelo de Empresa usando `getattr`.
- **Garantía:** El sistema de consumo es ahora transparente para el resto de la aplicación, comportándose como un objeto ORM pero con la velocidad y seguridad del SQL atómico.

---
*Esta bitácora se actualizará cada vez que realicemos un cambio estructural importante para mantener la coherencia del proyecto.*

