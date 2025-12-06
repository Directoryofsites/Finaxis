# Manual de Usuario - Capítulo 17: Auditoría de Consecutivos (Soporte)

## 1. Introducción
Esta herramienta de diagnóstico permite al equipo de soporte verificar la integridad de la numeración de documentos en **cualquier empresa** del sistema. Es fundamental para detectar problemas de sincronización, errores de base de datos o manipulaciones indebidas.

**Ubicación:** `Administración > Utilidades > Panel de Soporte > Pestaña "Auditoría Consecutivos"`

---

## 2. Proceso de Auditoría

### 2.1. Selección del Objetivo
A diferencia de la auditoría normal (Capítulo 8), aquí usted tiene visión global:
1.  **Seleccionar Empresa:** Elija el tenant que desea inspeccionar.
2.  **Seleccionar Documento:** El sistema cargará los tipos de documento configurados para esa empresa específica.

### 2.2. Ejecución
Al hacer clic en **"Auditar"**, el sistema escaneará la secuencia numérica buscando saltos.

---

## 3. Interpretación de Resultados

### 3.1. Resumen
El panel superior le mostrará:
*   **Último Consecutivo Registrado:** El número más alto encontrado en la base de datos.
*   **Huecos Detectados:** La cantidad de interrupciones en la secuencia.

### 3.2. Tabla de Detalles
La grilla muestra la lista de documentos, pero resalta en **Amarillo** las filas críticas:
*   **ALERTA DE HUECO:** Indica un rango de números que *deberían* existir pero no están.
    *   *Ejemplo:* "Faltan 3 consecutivos desde el #105 hasta el #107".

---

## 4. Casos de Uso Comunes
*   **Ticket de Soporte:** "El cliente dice que el sistema se saltó del 50 al 52". Use esta herramienta para confirmar si el #51 realmente no existe o si fue borrado.
*   **Validación Post-Migración:** Después de importar datos masivos, ejecute esta auditoría para asegurar que no quedaron baches en la historia.
