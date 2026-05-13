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

### Sesión 12/05/2026: Estabilización de Restauración y Portabilidad Cross-DB (SQLite/PostgreSQL)

#### 1. Estabilización de Restauración (IDs Cruzados)
- **Problema:** Errores `ForeignKeyViolation` durante la restauración en PostgreSQL debido a IDs de usuarios, tipos de documento y cuentas contables que no coincidían entre el backup (SQLite) y la base de datos destino.
- **Solución:** 
    - Se implementó un mapeo global de usuarios en `_upsert_manual_seguro`.
    - Se completó el mapeo de `PHConfiguracion` para incluir todos los tipos de documento (factura, recibo, mora, cruce) y todas las cuentas contables (cartera, caja, caja manual, intereses, anticipos, descuento).
    - Se actualizó `app/services/migracion.py` para incluir `cuenta_costo_produccion_id` en el mapeo de grupos de inventario.

#### 2. Protección Global de Relaciones con Usuarios
Se detectó que varios modelos (especialmente `FormatoImpresion`) fallaban al referenciar IDs de usuarios inexistentes en la base de datos destino.
- **Solución Global:** Se amplió la lógica de `_upsert_manual_seguro` en `app/services/migracion.py` para validar automáticamente campos como `creado_por_usuario_id`, `usuario_id`, `cerrado_por_usuario_id`, entre otros.
- **Comportamiento:** Si el ID del usuario original no existe en el sistema destino, el registro se asigna automáticamente al usuario que realiza la restauración. Esto garantiza la integridad referencial sin perder datos.

#### 3. Mejora en la Portabilidad del Backup (v7.7)
Para garantizar que los backups funcionen sin importar si se mueven de SQLite (Mono-usuario) a PostgreSQL (Multi-usuario) o viceversa:
- **Exportación Robusta:** Ahora el proceso de backup exporta explícitamente los **Códigos de Cuenta** en un diccionario `cuentas` dentro de cada grupo de inventario.
- **Importación Inteligente:** La restauración intenta primero resolver por ID interno (mapeo rápido) y, si falla o no está presente, utiliza los códigos de cuenta exportados para buscar el ID correcto en la base de datos destino.

#### 3. Protocolo de Replicación para Restauración Exitosa
1. **Generar Backup:** En el PC origen, ir a Configuración -> Backup y generar archivo `.json`.
2. **Preparar Destino:** Asegurar que el Plan de Cuentas (PUC) esté cargado en la empresa destino (o seleccionar "Restaurar Maestros" al importar).
3. **Restaurar:** Seleccionar el archivo, marcar los módulos deseados y procesar. El sistema ahora maneja automáticamente la discrepancia de IDs de producción.

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
### Causa Raíz: 3 Bugs combinados
1. **Icono inexistente en lucide-react:** La reescritura del Wizard usó íconos (`Monitor`, `Globe`, `Database`, `Building2`) no disponibles en v0.562. React los recibía como `undefined` y crasheaba silenciosamente → página en blanco.
2. **Config.json sucio:** Si quedaba un `config.json` de instalación anterior apuntando a PostgreSQL con datos, el `/check` devolvía `setup_needed: false` y el wizard nunca aparecía.
3. **El Dilema del Startup (Creación prematura de finaxis_local.db):** `app/main.py` y `app/api/setup/routes.py` se conectaban a SQLite vía SQLAlchemy en el momento que arrancaba el servidor, lo que forzaba la creación de un archivo de base de datos vacío y disparaba el seeder ANTES de que el usuario pudiera elegir la opción Multiusuario.

### Fixes
- **`app/main.py` y `app/api/setup/routes.py`:** Se agregaron pre-checks (sondas y guardias) que interceptan la conexión a SQLite. Si el archivo `.db` no existe físicamente en disco, se cancela la creación de tablas y la ejecución del seeder, dejándole esta responsabilidad exclusivamente al Wizard de instalación (`/api/setup/initialize`). Esto evita la aparición "mágica" de bases de datos antes de preguntar.
- **`frontend/app/setup/page.js`:** Reescrito con estilos inline 100% (sin Tailwind que pueda fallar) y solo íconos confirmados: `Rocket, Store, User, CheckCircle, Server`.
- **`app/api/setup/routes.py`:** Mejorado `/check` con `ignore_tenant=True` y manejo de excepciones (devuelve `true` si la DB no está lista). Nuevo endpoint `/reset` para limpiar `config.json` y volver al wizard.
- **`frontend/app/login/page.js`:** Agregado enlace discreto "Reconfigurar sistema" al pie, que llama a `/reset` y redirige al wizard. Solución ante instalaciones sucias sin necesidad de editar archivos a mano.
✅

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
    - **Sincronización:** La lógica utiliza el mismo algoritmo `itsdangerous` y `CLAVE_MAESTRA` que el validadallocal, garantizando compatibilidad total.
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

## 🏁 Actualización de Sesión (9 de mayo de 2026)

### 1. Blindaje Multiusuario: Bloqueo Optimista ✅
- **Implementación:** Se añadió la columna `version_id` en los modelos **Empresa** y **Tercero**.
- **Función:** Previene que en entornos de red con múltiples operarios, los cambios concurrentes causen pérdida de integridad de datos. El sistema ahora detecta colisiones de guardado de forma nativa.

### 2. Auto-Migración Inteligente (Self-Healing) ✅
- **Mejora:** Se actualizó `app/core/auto_migrate.py` para inyectar automáticamente el `version_id` y otras columnas de seguridad en instalaciones existentes.
- **Resultado:** Las PC que ya tienen Finaxis instalado recibirán la mejora de seguridad al simplemente reiniciar el programa, sin intervención manual.

### 3. Herramienta de Traspaso (SQLite ↔ Postgres) ✅
- **Nuevo Script:** `app/scripts/migrate_to_postgres.py`.
- **Capacidad:** Permite migrar una base de datos local completa a un servidor PostgreSQL centralizado, gestionando la creación de esquemas y el reinicio de secuencias de numeración.

### 4. Roadmap Multiusuario: Fase 2 COMPLETADA ✅
- **Hito:** Implementación del **Asistente de Configuración de Entorno** (Multi-step Wizard).
- **Logro:** Soporte para persistencia de credenciales Postgres en `%APPDATA%\Finaxis\config.json` con conmutación automática de motor al arranque.

### 5. Roadmap Multiusuario: Fase 3 COMPLETADA ✅
- **Hito:** Utilidad de Migración Integrada.
- **Logro:** Script `run_sqlite_to_postgres_migration` y endpoint API para traspaso de datos local-red con un solo clic desde el Wizard.

### 6. Roadmap Multiusuario: Fase 4 INICIADA 🚀
- **Objetivo:** Automatización de Red y Firewall. Creación de scripts de PowerShell para apertura de puertos y guías de configuración de acceso remoto en PostgreSQL (`pg_hba.conf`).

---

## 🏗️ ESTUDIO TÉCNICO: Implementación Multiusuario en Red Local (PostgreSQL)

Este apartado documenta la arquitectura y el plan de ejecución para permitir que Finaxis funcione en una red local con múltiples operarios simultáneos (hasta 10), superando las limitaciones de SQLite.

### 1. El Concepto: "Instalador Único, Dos Mundos"
Para optimizar el mantenimiento, se ha decidido utilizar un **único binario** (compilado una sola vez) que detecta dinámicamente su entorno:
- **Modo Monousuario:** Usa SQLite en `%APPDATA%` (Comportamiento actual).
- **Modo Multiusuario (Red):** Se conecta a una instancia de PostgreSQL central.
- **Drivers:** El instalador empaqueta `psycopg2-binary` por defecto, permitiendo el cambio de motor sin reinstalar el programa.

### 2. Arquitectura de Red (Topología Cliente-Servidor)
- **Servidor (PC Maestro):** 
    - Aloja el servicio de **PostgreSQL**.
    - Puede ser la misma máquina donde trabaja un operario principal.
    - Requiere una **IP Estática** (ej: `192.168.1.50`) para evitar que los clientes pierdan la conexión si el router reinicia.
- **Clientes (PCs Operativos):**
    - Se conectan al servidor mediante la IP.
    - **Acceso Web:** Los clientes pueden entrar simplemente vía navegador (`http://IP_SERVIDOR:3000`) sin instalar nada localmente, aprovechando que el frontend es Next.js.
    - **Acceso App:** También pueden tener el aplicativo instalado pero configurado para apuntar a la base de datos remota.

### 3. Configuración de Base de Datos (PostgreSQL)
- **Concurrencia:** PostgreSQL maneja el pool de conexiones (configurado en 20-40) permitiendo que 10+ usuarios graben documentos simultáneamente sin bloqueos de tabla.
- **Seguridad LAN:** Se debe configurar `pg_hba.conf` para permitir conexiones desde la subred local (`192.168.1.0/24`) y `postgresql.conf` para escuchar en todas las interfaces (`*`).
- **Backup:** A diferencia de SQLite (copiar archivo), PostgreSQL requiere el uso de `pg_dump` para respaldos consistentes.

### 4. Roles y Flujo de Trabajo
El sistema utiliza su motor de **RBAC** para segmentar la red:
- **Puntos de Facturación/Recibos:** Roles con permisos limitados a creación de documentos.
- **Contabilidad/Gerencia:** Roles con acceso a monitor de asientos y estados financieros.
- **Centralización:** Todos alimentan la misma base de datos en tiempo real.

### 5. Plan de Ejecución (Roadmap)
### 6. Refinamiento de Ingeniería (Análisis de Experto)

Tras una revisión profunda bajo estándares de aplicaciones financieras distribuidas, se precisan los siguientes puntos críticos para garantizar el éxito del despliegue:

#### A. Integridad Financiera y Concurrencia (Race Conditions)
*   **Numeración Secuencial:** En modo multiusuario, el cálculo del "siguiente número" no puede ser una simple lectura + escritura. Se debe implementar `SELECT FOR UPDATE` en SQLAlchemy o delegar en `SEQUENCES` de PostgreSQL para evitar duplicidad de facturas cuando dos operarios guardan al mismo tiempo.
*   **Bloqueo Optimista:** Se recomienda añadir una columna `version_id` (o timestamp de última modificación) en las tablas maestras (Empresas, Terceros). Si un operario intenta guardar un cambio sobre un registro que ya fue modificado por otro, el sistema debe alertar: *"Los datos han cambiado, por favor recargue"*.

#### B. Estabilidad de Red y Descubrimiento
*   **Hostnames sobre IPs:** Para evitar que la conexión se rompa si el router cambia la IP (DHCP), se priorizará el uso del **Nombre de Equipo** (ej: `http://SERVIDOR-FINAXIS:8765`). El Wizard de configuración intentará resolver el nombre mediante NetBIOS/mDNS.
*   **Automatización de Firewall:** El instalador incluirá un script de PowerShell para abrir automáticamente los puertos `5432` (Postgres), `8765` (Backend) y `3000` (Frontend) en el Firewall de Windows del servidor, eliminando errores de "Conexión Rechazada".

#### C. Compatibilidad de Dialectos (SQLite ↔ Postgres)
*   **Tipos de Datos:** Se identificó que el uso de campos `JSON` y `Boolean` varía entre motores. Se estandarizará el uso de `JSONB` para Postgres (para búsquedas rápidas en metadatos extra) y se validará que las migraciones de Alembic detecten el dialecto actual para aplicar los índices correctos.
*   **Script de Migración Robusto:** No se usará un simple "Dump". Se desarrollará una herramienta de "Sincronización de Motores" que lea de SQLite y escriba en Postgres vía objetos de SQLAlchemy, manejando automáticamente las diferencias de formato de fecha y llaves foráneas.

#### D. Gestión de Licencias en Red
*   **Licencia Centralizada:** La licencia se validará **únicamente en el servidor**. Las estaciones cliente heredarán el estado de activación del servidor central.
*   **Control de Sesiones:** El sistema permitirá monitorear qué usuarios están conectados actualmente y desde qué IP, facilitando auditorías de seguridad interna.

---
*Esta bitácora se actualizará cada vez que realicemos un cambio estructural importante para mantener la coherencia del proyecto.*

---

## 🐛 CORRECCIONES CRÍTICAS — Sesión 2026-05-09 (Tarde)

### Problema: Instalador Roto — 4 Bugs en Cadena

Se identificó una "tormenta perfecta" de 4 errores que hacían que el Wizard de configuración creara una base de datos ilegible y bloqueara el acceso de todos los usuarios.

#### Bug 1: Motor de DB Estático (RAÍZ DEL PROBLEMA)
- **Síntoma:** El programa se conectaba a SQLite al arrancar y no cambiaba a PostgreSQL aunque se guardara el `config.json`.
- **Fix:** Refactorizado `app/core/database.py` con un sistema de "motor dinámico" (`get_engine()`). Ahora cada llamada verifica si `config.json` cambió y, si es así, destruye la conexión vieja y crea la nueva. El endpoint `config-db` invalida el caché explícitamente (`db_module._engine = None`) antes de llamar `get_engine()`.

#### Bug 2: Caché No Invalidado en `config-db`
- **Síntoma:** Aunque se guardaba el nuevo URL en `config.json`, el engine cacheado con la URL vieja seguía en memoria.
- **Fix:** El endpoint `POST /api/setup/config-db` ahora pone a `None` las 3 variables de caché (`_engine`, `_last_db_url`, `_SessionLocal`) antes de re-inicializar.

#### Bug 3: `fecha_inicio` Requerido Pero No Enviado
- **Síntoma:** El endpoint `POST /api/setup/initialize` devolvía HTTP 422 (error silencioso) porque `fecha_inicio` era obligatorio en el schema pero el frontend no lo enviaba siempre.
- **Fix:** `fecha_inicio` ahora es `Optional[date] = None` en `InitialSetupSchema`. Si no se envía, usa `date.today()`.

#### Bug 4: SQLite con Pool de Conexiones Inválido
- **Síntoma:** `pool_size=20` y `max_overflow=40` son parámetros inválidos para SQLite, causando errores en instalaciones monousuario.
- **Fix:** `get_engine()` ahora detecta si es SQLite y usa `StaticPool` (sin pool). Para PostgreSQL mantiene los parámetros de alto rendimiento.

#### Bonus: Wizard Reescrito de Cero
- El archivo `frontend/app/setup/page.js` fue completamente reescrito.
- Flujo garantizado: Paso 0 (Modo) → Paso 1 (PostgreSQL, solo si Multi, **imposible saltarse**) → Paso 2 (Empresa).
- Se agregó panel informativo de red (instrucciones para estaciones vía navegador).

**Archivos modificados:**
- `app/core/database.py`
- `app/api/setup/routes.py`
- `frontend/app/setup/page.js`

---

## 🏁 Actualización de Sesión (11 de mayo de 2026)

### 🛰️ ESTABILIZACIÓN TOTAL: Red Local y Multi-usuario ✅

Se logró el hito de comunicación bi-direccional estable entre servidor y clientes en ambiente de red real (Wi-Fi/Hotspot). Esta configuración permite que múltiples estaciones de trabajo operen sobre el mismo motor PostgreSQL centralizado.

#### 1. Arquitectura de Red Dinámica (Self-Adapting)
- **Problema:** El frontend estaba "ciego" a la red, intentando conectar siempre a `localhost`.
- **Solución:** Se implementó `getDynamicApiUrl()` en `apiService.js`. El programa ahora detecta la IP desde la cual el usuario está accediendo (ej: `172.16.104.23`) y ajusta automáticamente todas las llamadas de la API a esa dirección en el puerto `8765`.
- **Impacto:** Un solo instalador sirve para cualquier red sin necesidad de recompilar el código.

#### 2. Configuración Maestra de PostgreSQL (Acceso Remoto)
Para habilitar el servidor, se deben aplicar estos cambios en la carpeta `data` de Postgres:
- **`postgresql.conf`**: Cambiar a `listen_addresses = '*'` (Escuchar en todas las interfaces).
- **`pg_hba.conf`**: Agregar el permiso de subred. 
    *   *Regla de Oro:* `host all all [SUBRED_IP]/24 scram-sha-256`. 
    *   Ejemplo para red común: `192.168.1.0/24`.
- **Servicio:** Reiniciar siempre el servicio `postgresql-x64-17` tras modificar estos archivos.

#### 3. El Protocolo de Windows (El "Muro" de Seguridad)
Se identificó que Windows bloquea la comunicación incluso con el programa instalado. Para replicar el éxito, se DEBEN ejecutar estos comandos en el Servidor (PowerShell Admin):
1.  **Perfil de Red:** Cambiar a "Privado" (Indispensable para que el Firewall respeite las reglas).
    *   `Get-NetConnectionProfile | Set-NetConnectionProfile -NetworkCategory Private`
2.  **Regla de Apertura:** Crear pase VIP para los puertos de Finaxis.
    *   `New-NetFirewallRule -DisplayName "Finaxis Network" -Direction Inbound -LocalPort 3000,8765,5432 -Protocol TCP -Action Allow`

#### 4. Preparación del Instalador (`.exe`)
Se ajustó el lanzador `run.py` para producción:
- **Binding:** `host="0.0.0.0"` y `port=8765`.
- **Estabilidad:** Se desactivó `reload=False`. En ambientes compilados, el auto-reload de Uvicorn causa inestabilidad y bloqueos de puerto.
- **CORS:** Se habilitó `allow_origins=["*"]` en `app/main.py`. Es la única forma de garantizar que navegadores en otros PCs no bloqueen la interfaz por seguridad de dominio cruzado en LAN.

#### 5. Guía de Replicación (Resumen de Éxito)
1.  **Servidor:** Ejecutar instalador → Configurar como "Multiusuario" → Registrar Empresa.
2.  **Red:** Asegurar que Servidor y Cliente estén en la misma red y en modo "Privado".
3.  **Cliente:** No instalar nada. Simplemente abrir navegador en: `http://[IP_SERVIDOR]:3000/login`.

---

## 🏁 Actualización de Sesión (12 de mayo de 2026)

### 🛰️ ESTABILIZACIÓN DE PAGOS Y DEPURACIÓN DE SETUP ✅

Se ha logrado la estabilización final de la lógica de recaudos y se ha robustecido el proceso de inicialización para despliegues multiusuario, eliminando fricciones técnicas en la puesta en marcha.

#### 1. Corrección del Error 422 (Unprocessable Entity) en Pagos
- **Diagnóstico:** El formulario de pagos en el frontend enviaba una cadena vacía (`""`) en el campo `cuenta_caja_id` cuando el usuario no seleccionaba una cuenta opcional. Esto causaba un fallo de validación en el backend (Pydantic), que esperaba un entero o `None`.
- **Solución (Frontend):** Se modificó `frontend/app/ph/pagos/page.js` para inicializar el campo en `null` y sanitizar el envío antes de llamar a la API.
- **Solución (Backend):** Se añadió un `field_validator` en `app/api/propiedad_horizontal/routes.py` que convierte automáticamente cadenas vacías en `None`, haciendo que el sistema sea tolerante a fallos de entrada.

#### 2. Depuración del Bloqueo 403 en Inicialización
- **Mejora:** El endpoint `/api/setup/initialize` ahora proporciona **información forense** en el mensaje de error. Si el sistema detecta que ya fue inicializado por "usuarios reales", ahora muestra los correos electrónicos específicos que están ocupando la base de datos.
- **Utilidad:** Esto permite identificar rápidamente si hay usuarios de pruebas residuales en la base de datos PostgreSQL del cliente que impiden el registro de la nueva empresa.

#### 3. Automatización de Base de Datos en PostgreSQL
- **Hito:** Se confirmó que el instalador **automatiza totalmente la creación de la base de datos**. 
- **Lógica:** Al configurar PostgreSQL en el wizard, el sistema se conecta a la base maestra (`postgres`), verifica la existencia de `finaxis_network` y, si no existe, la crea con codificación UTF8. El cliente NO necesita abrir pgAdmin para crear la base de datos manualmente.
- **Nota de Seguridad:** Se aclaró que el instalador **no asigna** la clave a PostgreSQL; requiere que el usuario ingrese la clave maestra que ya fue definida durante la instalación del motor de base de datos.

#### 4. Verificación del Instalador Standalone
- **Prueba de Éxito:** Se verificó que al borrar `config.json` y eliminar la base de datos, el instalador reconstruye el entorno completo (Conexión -> Creación de DB -> Creación de Tablas -> Seeder -> Registro de Empresa) de forma autónoma.

---

## 🛰️ GUÍA DE DESPLIEGUE EN RED: PASO A PASO (Sesión 12/05/2026)

Esta sección documenta el proceso manual de configuración para estaciones cliente en red local.

### 1. Configuración del Servidor (PC Maestro)
*   **Paso 1: Perfil de Red (OK)** ✅
    - Se forzó el cambio de categoría de red a `Private` mediante PowerShell (Admin).
    - Comando: `Get-NetConnectionProfile | Set-NetConnectionProfile -NetworkCategory Private`
*   **Paso 2: Firewall de Windows - Apertura de Puertos (Servidor)** ✅
    - **Objetivo:** Autorizar la entrada de datos desde la red local al servidor.
    - **Acción Realizada:** Se creó la regla de entrada "Finaxis Network" mediante el comando:
      ```powershell
      New-NetFirewallRule -DisplayName "Finaxis Network" -Direction Inbound -LocalPort 3000,8765,5432 -Protocol TCP -Action Allow
      ```
    - **Puertos Autorizados:**
        - `3000` (Interfaz de Usuario / Frontend).
        - `8765` (Motor de Lógica / Backend).
        - `5432` (Base de Datos / PostgreSQL).
    - **Verificación:** Se validó con el comando `Get-NetFirewallRule -DisplayName "Finaxis Network"`.
    - **Interpretación del Resultado:** 
        - `PrimaryStatus: OK`: Significa que la regla fue analizada y aceptada por el almacén de seguridad de Windows sin errores de sintaxis.
        - `Enabled: True`: Indica que la regla está operando activamente.
*   **Paso 3: Configuración de Escucha Global (OK)** ✅
    - Modificación de `listen_addresses = '*'` en `postgresql.conf`.
*   **Paso 4: Permisos de Subred Local (OK)** ✅
    - Adición de regla `host all all 192.168.40.0/24 scram-sha-256` en `pg_hba.conf`.
*   **Paso 5: Reinicio de Motor de Base de Datos (OK)** ✅
    - Reinicio del servicio `postgresql-x64-17` para aplicar cambios.
*   **Paso 6: Re-compilación de Instalador (CÓDIGO LISTO)** ✅
    - **Cambio Aplicado:** `run_local.py` corregido con `host="0.0.0.0"`.
    - **Cambio Aplicado:** `build_instalador.bat` limpio de `localhost` en el frontend.
    - **Estado:** Código fuente preparado para generar el instalador multiusuario definitivo.

*   **Paso 7: Configuración de Equipos Clientes (Manual de Despliegue Detallado)** 📋
    - **Objetivo:** Preparar los computadores de los usuarios finales para conectar con el servidor.
    
    **Sub-paso 7.1: Preparación de Permisos de Red (En el Equipo Cliente)**
    1.  **Abrir PowerShell como Administrador:**
        - Presionar la tecla `Windows` en el teclado.
        - Escribir `PowerShell`.
        - En el menú de la derecha, hacer clic en **"Ejecutar como administrador"** (o clic derecho > Ejecutar como administrador).
        - Confirmar en la ventana de control de usuario (Hacer clic en **SÍ**).
    2.  **Configurar Perfil de Red a Privado:**
        - Copiar y pegar el siguiente comando en la ventana azul y presionar `Enter`:
          `Get-NetConnectionProfile | Set-NetConnectionProfile -NetworkCategory Private`
        - *Razón:* Esto habilita que Windows confíe en los otros equipos de la oficina y permita el tráfico de datos de Finaxis.

    **Sub-paso 7.2: Verificación de Canal de Datos (Prueba de Ping)**
    1.  Abrir el navegador (Chrome, Edge o Firefox).
    2.  Ingresar la URL de prueba de vida del motor: `http://192.168.40.133:8765/api/ping`
    3.  **Resultado Correcto:** Debe visualizarse en pantalla el mensaje: `{"status": "alive"}`.
    4.  Si el mensaje no aparece, se debe revisar nuevamente el Paso 2 (Firewall del Servidor).

    **Sub-paso 7.3: Acceso Final al Sistema**
    1.  Ingresar a la URL del sistema: `http://192.168.40.133:3000`
    2.  **Verificación Final:** El sistema debe cargar la pantalla de **Login** (Usuario y Clave).
    3.  Si carga el "Asistente de Inicio", reportar error de conexión al puerto 8765.
---

## 🏁 Actualización de Sesión (12 de mayo de 2026 - Noche)

### 🚀 OPTIMIZACIÓN MULTI-USUARIO Y RESCATE DE INFRAESTRUCTURA ✅

Se ha consolidado la arquitectura de red local para Finaxis, logrando un despliegue "Plug & Play" que supera las barreras de autenticación de PostgreSQL y la rigidez de las direcciones IP.

#### 1. Backend: Escucha Global (0.0.0.0)
- **Cambio:** Se modificó `run_local.py` para que el servidor Uvicorn escuche en `0.0.0.0` en lugar de `127.0.0.1`.
- **Razón:** El binding a `127.0.0.1` solo permite conexiones desde el mismo PC. Con `0.0.0.0`, el servidor acepta peticiones desde cualquier dispositivo de la red local (LAN).
- **Puerto:** Se mantiene en `8765`.

#### 2. Frontend: Detección Dinámica de Servidor
- **Archivo:** `frontend/lib/apiService.js`.
- **Lógica:** Se reemplazó la IP estática por `window.location.hostname`.
- **Beneficio:** No importa si la IP del servidor cambia (ej: de `.133` a `.100`), el cliente detecta automáticamente a qué dirección debe pedirle los datos.

#### 3. El Protocolo de Rescate: "Modo Trust" para PostgreSQL
Se documentó una solución definitiva para cuando el instalador de PostgreSQL en un equipo nuevo no solicita contraseña y bloquea el acceso administrativo (`FATAL: password authentication failed`).

- **Causa:** PostgreSQL se instala con un estado de autenticación `scram-sha-256` sin una clave conocida por el usuario.
- **Acción de Rescate:**
    1.  Editar `pg_hba.conf` (como Administrador).
    2.  Cambiar el método de autenticación para `127.0.0.1/32` de `scram-sha-256` a **`trust`**.
    3.  Reiniciar el servicio `postgresql-x64-17`.
    4.  Entrar vía pgAdmin (sin clave), definir una contraseña real para el usuario `postgres` y crear la DB `finaxis_network`.
    5.  **Reversión:** Volver a poner `scram-sha-256` en `pg_hba.conf` y reiniciar para restaurar el blindaje de seguridad.

#### 4. Validación: El Escenario Invertido
Se realizó una prueba crítica:
- **PC A (Anterior Servidor):** Pasó a ser **Cliente**.
- **PC B (Anterior Cliente):** Pasó a ser **Servidor**.
- **Resultado:** ÉXITO TOTAL. Al seguir el manual (Apertura de Firewall, Perfil Privado y Protocolo de Rescate), la conexión se estableció instantáneamente mediante el puerto `3000`.

#### 5. Artefactos Entregados
- **Manual Maestro v1.7:** `MANUAL_DESPLIEGUE_RED_FINAXIS.html`. Contiene 10 pasos detallados, incluyendo el anexo de emergencia para rescate de contraseñas.
- **Instalador Network-Ready:** El script `build_instalador.bat` genera ahora versiones compatibles con red local de forma nativa.

---
*Fin de la sesión: Sistema operativo, documentado y blindado contra errores de configuración inicial.*
