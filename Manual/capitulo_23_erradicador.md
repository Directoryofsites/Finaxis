# Manual de Usuario - Capítulo 23: Erradicador Universal

## 1. Introducción
El **Exterminador Universal de Datos** es la herramienta más potente y peligrosa del sistema. Permite vaciar tablas completas de una empresa específica. A diferencia de la eliminación normal, esta acción **no deja rastro** en la papelera de reciclaje.

**Ubicación:** `Administración > Utilidades > Panel de Soporte > Pestaña "Erradicador"`

---

## 2. Funcionamiento
Esta herramienta está diseñada para "reiniciar" módulos específicos de una empresa sin tener que borrar la empresa completa.

### 2.1. Selección de Objetivo
1.  **Empresa:** Seleccione el tenant sobre el cual actuará.
2.  **Entidades a Erradicar:** Marque los módulos que desea limpiar.
    *   *Cartilla de Inventario:* Borra todos los productos y sus movimientos.
    *   *Movimientos y Documentos:* Borra toda la contabilidad (facturas, recibos, asientos).
    *   *Terceros:* Borra la base de datos de clientes y proveedores.
    *   *Logs de Operaciones:* Limpia el historial de auditoría.
    *   *(Otros maestros):* Plan de cuentas, centros de costo, etc.

### 2.2. Protocolo de Seguridad
Debido al riesgo de pérdida masiva de datos, el sistema exige una doble confirmación:
1.  **Frase de Seguridad:** Debe escribir exactamente la frase que el sistema le indica (ej: `ERRADICAR DATOS DE EMPRESA X`).
2.  **Confirmación Final:** Un cuadro de diálogo (popup) le preguntará por última vez si está seguro.

> [!DANGER]
> **Consecuencias Irreversibles:**
> *   Si borra **Terceros**, se romperá la integridad de los documentos históricos que referencien a esos terceros (aunque el sistema intentará borrar en cascada).
> *   Si borra **Movimientos y Documentos**, la contabilidad quedará en cero.
> *   **NO HAY DESHACER.** Asegúrese de tener una copia de seguridad si tiene dudas.
