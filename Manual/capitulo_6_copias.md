# Manual de Usuario - Capítulo 6: Copias y Restauración (Migración)

## 1. Introducción
El módulo de **Migración de Datos** es la herramienta más potente para la seguridad y portabilidad de su información.

A diferencia de un simple "Guardar como...", este módulo permite:
1.  **Exportar (Backup):** Generar un archivo `.json` completo con toda la estructura de su empresa (Terceros, Cuentas, Facturas, Inventario).
2.  **Restaurar (Fusión):** Insertar datos de un archivo en una empresa existente sin borrar lo que ya tiene (Modo Fusión).
3.  **Transformar:** Cambiar masivamente códigos de cuentas o terceros (Herramienta avanzada).

---

## 2. ¿Cómo acceder al módulo?
Siga esta ruta en el menú principal:

1.  Ubique la sección **Administración y Configuración**.
2.  Busque el grupo **Utilidades**.
3.  Haga clic en la opción **Migración de Datos**.

> **Ruta Rápida:** `Administración > Utilidades > Migración`

---

## 3. Lógica de Negocio (Seguridad Atómica)

### 3.1. El Protocolo Espejo Atómico
Al restaurar una copia, el sistema no borra ciegamente. Utiliza un protocolo de seguridad llamado **"Fusión Segura"**:
*   **No Borrado Masivo:** Si usted restaura una copia sobre una empresa que ya tiene datos, el sistema **NO** borrará sus facturas existentes. Solo agregará las nuevas o actualizará las que coincidan exactamente en número y tipo.
*   **Snapshot de Seguridad:** Antes de cualquier restauración, el sistema crea automáticamente una copia de seguridad interna (Snapshot) de cómo estaba la empresa *antes* de tocar nada. Si algo falla, se puede revertir.

### 3.2. Diferencia entre Backup y Exportación
En ContaPY, ambos términos se usan para lo mismo: un archivo `.json` que contiene la "ADN" de su empresa. Este archivo es legible por humanos y por máquinas, lo que garantiza que sus datos son suyos y no están "secuestrados" en un formato extraño.

---

## 4. Guía Paso a Paso


### 4.1. Exportar Datos (Crear Copia de Seguridad)
Esta herramienta le permite extraer información quirúrgica de su empresa. No es solo un "todo o nada"; usted puede decidir exactamente qué llevarse.

#### A. Selección de Paquetes (El "Qué")
En la columna izquierda encontrará tres grupos de datos. Lo que marque aquí será lo que el sistema escriba en el archivo `.json`.

**1. Datos Maestros (La Estructura)**
Son los cimientos de su contabilidad.
*   **Plan de Cuentas:** Exporta su árbol de cuentas (PUC) completo.
    *   *¿Qué pasa si lo marco?* El sistema guarda códigos, nombres, niveles y configuraciones (si pide tercero, si es de impuestos, etc.).
    *   *Uso común:* Ideal para replicar su estructura contable en una empresa nueva sin llevarse los saldos.
*   **Terceros:** Exporta su directorio de clientes, proveedores y empleados.
*   **Centros de Costo:** Exporta su estructura de departamentos o proyectos.
*   **Tipos de Documento:** Exporta la configuración de sus comprobantes (Facturas, Egresos, etc.), incluyendo sus resoluciones de facturación y numeración actual.
*   **Inventario (Bodegas, Grupos, Productos):** Exporta todo su catálogo de productos y precios, pero **NO** las cantidades (el stock se define por los movimientos, ver "Transacciones").

**2. Configuraciones (La Personalización)**
*   **Plantillas de Documentos:** Exporta los diseños HTML de sus facturas. ¡Muy útil para no tener que volver a diseñar su factura en cada empresa!
*   **Librería de Conceptos:** Exporta sus textos predefinidos.

**3. Transacciones (El "Movimiento")**
Esta es la opción más potente.
*   **Incluir Movimientos Contables:** Al activar este interruptor, usted le dice al sistema: *"No quiero solo la estructura, quiero la historia financiera"*.
*   *Efecto:* Se habilitará el panel derecho de **Filtros Avanzados**.
---
#### B. Filtros de Transacciones (El "Cuánto")
Si activó la opción de "Transacciones", el panel derecho se iluminará. Aquí puede aplicar un bisturí a su información. **Los filtros son acumulativos** (funcionan con lógica "Y").
*   **Rango de Fechas:**
    *   *Ejemplo:* Del `01/01/2023` al `31/12/2023`.
    *   *Resultado:* Solo se exportarán los comprobantes de ese año. El resto se ignora.
    
*   **Por Tercero:**
    *   *Ejemplo:* Selecciona al cliente "Éxito S.A.".
    *   *Resultado:* El sistema buscará **todas** las facturas, recibos o asientos donde este tercero sea el protagonista. Ideal para auditorías específicas o entregar información a un abogado.
*   **Por Cuenta Contable:**
    *   *Ejemplo:* Selecciona la cuenta `4135 (Comercio al por mayor)`.
    *   *Resultado:* Exportará solo los movimientos que tocaron esa cuenta de ingresos.
*   **Por Centro de Costo:**
    *   *Ejemplo:* Proyecto "Edificio Norte".
    *   *Resultado:* Obtendrá un archivo con la contabilidad exclusiva de ese proyecto.
*   **Palabra Clave:**
    *   *Ejemplo:* Escribe "Arriendo".
    *   *Resultado:* El sistema buscará en las observaciones de todos los documentos y exportará aquellos que contengan esa palabra.
#### C. El Resultado Final
Al hacer clic en **Generar Backup JSON**, obtendrá un archivo con un nombre como:
`backup_contable_MiEmpresa_2025-10-27.json`
Este archivo es inteligente:
1.  **Autocontenido:** Si usted filtró las facturas de "Juan Pérez", el sistema automáticamente incluirá en el paquete al tercero "Juan Pérez" y las cuentas contables que usó en esas facturas, para que al restaurar no falte nada.
2.  **Legible:** Aunque es técnico, puede abrirlo con un bloc de notas y leer su información.

### 4.2. Restaurar Copia de Seguridad (Importar Datos)
El proceso de restauración en ContaPY no es ciego. El sistema actúa como un "Aduanero": revisa cada dato antes de dejarlo entrar a su empresa.
#### A. El Proceso de Análisis (La "Aduana")
Antes de guardar un solo dato, el sistema lee su archivo `.json` y lo compara con lo que ya existe en la empresa destino.
1.  **Seleccione la Empresa Destino:**
    *   *Precaución:* Asegúrese de elegir la empresa correcta. Si elige una empresa vacía, se llenará con los datos. Si elige una empresa en marcha, el sistema intentará fusionar la información.
2.  **Cargue el Archivo:**
    *   Busque el archivo `.json` en su computador.
3.  **El Informe de Impacto (Vital):**
    *   Al cargar el archivo, **NO** se guardan los datos inmediatamente. Aparecerá un panel de "Análisis de Impacto".
    *   **Semáforo de Datos:**
        *   🟢 **A Importar:** Registros nuevos que no existen en la empresa destino. Estos entrarán sin problemas.
        *   🔴 **Conflictos (Omitidos):** Registros que YA existen (ej: el Tercero con cédula 123 ya está creado). El sistema **protege** el dato existente y omite el del archivo para no sobrescribir información valiosa.
> **Ejemplo de Fusión:** Si usted importa una copia donde "Juan Pérez" tiene el teléfono "555-5555", pero en su empresa actual "Juan Pérez" ya existe con el teléfono "999-9999", el sistema **RESPETA** el teléfono "999-9999" y no lo toca.
#### B. Ejecución (La Confirmación)
Solo si está de acuerdo con el informe de impacto (cuántos entran, cuántos rebotan), proceda.
1.  **Revisar Conflictos:** Si ve números en rojo, puede desplegar la lista para ver exactamente qué registros se están omitiendo.
2.  **Confirmar:** Haga clic en el botón **Confirmar e Importar Datos**.
3.  **Snapshot de Seguridad:** En este milisegundo, el sistema hace una copia interna de emergencia por si algo sale mal durante la escritura.
#### C. Escenarios de Uso Comunes
*   **Clonación de Empresas:** Exportar la "Empresa Modelo" (con PUC y Plantillas listas) y restaurarla en una "Empresa Nueva" vacía. Ahorra horas de configuración.
*   **Fusión de Sucursales:** Si tiene dos empresas separadas y quiere unificarlas, puede exportar la Sucursal B y restaurarla dentro de la Sucursal A.
*   **Recuperación de Desastres:** Si borró accidentalmente un bloque de facturas, puede restaurar una copia de ayer. El sistema omitirá lo que no borró (porque ya existe) y solo re-insertará lo que falta.

### 4.3. Transformación de Datos (ETL)
> **¿Qué es ETL?** Siglas de *Extract, Transform, Load*. Es una herramienta para "operar" sus datos fuera del sistema antes de ingresarlos.
Esta pantalla no toca su base de datos actual. Funciona como un **Laboratorio de Archivos**: usted sube un archivo `.json`, le aplica reglas de cambio, y el sistema le devuelve un **nuevo archivo `.json` transformado** listo para restaurar.
#### A. ¿Para qué sirve esto? (Casos de Uso)
1.  **Corregir Errores de Fecha:** Imaginemos que digitó 1.000 facturas con fecha "2023" pero eran del "2024". En lugar de editarlas una por una, usa esta herramienta para cambiar el año masivamente.
2.  **Migrar de Software Viejo:** Si viene de otro software y quiere importar sus datos, puede usar esta herramienta para asignarles los Tipos de Documento correctos de ContaPY.
3.  **Renumeración Masiva:** Si su resolución de facturación cambió y necesita que sus facturas antiguas empiecen desde el número 5000 para no chocar con las nuevas.
#### B. Guía de Uso del Laboratorio
**Paso 1: Cargar la Fuente**
Suba el archivo `.json` que desea modificar. El sistema le dirá cuántos documentos encontró dentro.
**Paso 2: Definir las Reglas (El Bisturí)**
Puede aplicar una o varias reglas al mismo tiempo:
*   **Recodificación General (Renumerar):**
    *   *Campo:* `Nuevo N° Inicial Consecutivo`.
    *   *Acción:* Si escribe `1001`, el sistema tomará el documento más antiguo y le pondrá el #1001, al siguiente el #1002, y así sucesivamente.
    *   *Utilidad:* Ordenar cronológicamente facturas desordenadas.
*   **Cambio de Fechas (Viaje en el Tiempo):**
    *   Puede forzar un **Día**, **Mes** o **Año** específico.
    *   *Ejemplo:* Si pone Año `2025`, todas las facturas del archivo pasarán a ser del 2025, manteniendo su día y mes original.
*   **Cambio de Tipo de Documento (Metamorfosis):**
    *   Esta es la función más potente. Permite convertir documentos de una clase a otra.
    *   *Filtro de Fechas:* Primero, diga "Desde qué fecha" quiere aplicar el cambio (para no afectar años cerrados).
    *   *Origen y Destino:* Seleccione "De Tipo: Cotización" -> "A Tipo: Factura de Venta".
    *   *Resultado:* El sistema buscará todas las cotizaciones en ese rango de fechas y les cambiará su código interno para que, al restaurarlas, el sistema las reconozca como Facturas reales.
**Paso 3: Aplicar y Descargar**
Haga clic en **Aplicar y Generar JSON**.
*   El sistema procesará los datos en memoria (segundos).
*   Se habilitará un panel negro (Terminal) mostrando el resultado.
*   Haga clic en **Descargar Archivo .JSON**.
> **Nota Final:** El archivo que descarga aquí es el que debe usar luego en la pestaña de **Restauración** (Sección 4.2).



