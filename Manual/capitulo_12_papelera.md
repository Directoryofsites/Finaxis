# Manual de Usuario - Capítulo 12: Papelera de Reciclaje

## 1. Introducción
La **Papelera de Reciclaje** es la red de seguridad definitiva de ContaPY2. Su función es retener todos los documentos que han sido eliminados del sistema, permitiendo su recuperación en caso de error humano o auditoría.

**Ubicación:** `Administración > Utilidades > Papelera`

---

## 2. Funcionamiento
Cuando usted utiliza la opción "Eliminar" en cualquier módulo (como la *Eliminación Masiva* del Capítulo 11), los datos **NO** se destruyen físicamente del disco duro. En su lugar:
1.  El documento se marca como "Eliminado".
2.  Desaparece de todos los informes contables, balances y estados financieros.
3.  Se traslada a esta bandeja de custodia.
4.  El sistema registra la "Huella de Auditoría": **Quién** lo eliminó y **Cuándo**.

---

## 3. Interfaz de la Papelera
La pantalla presenta una tabla detallada con los documentos en custodia:

*   **ID Original:** El código interno único del registro.
*   **Tipo de Documento:** (Ej: Factura, Recibo de Caja).
*   **Valor:** El monto total por el que se creó el documento.
*   **Número:** El consecutivo que tenía antes de ser borrado.
*   **Fecha Original:** La fecha contable del documento.
*   **Datos de Eliminación:** Muestra el usuario responsable y la fecha/hora exacta del borrado.

---

## 4. Restauración de Documentos
Si eliminó un registro por accidente, puede traerlo de vuelta a la vida ("Resucitarlo"):

1.  Localice el documento en la lista.
2.  Haga clic en el botón azul **"Restaurar"**.
3.  Confirme la acción en la ventana emergente.

### 4.1. ¿Qué sucede al restaurar?
*   El documento desaparece de la Papelera.
*   Reaparece en el *Explorador de Documentos* y en los *Libros Contables*.
*   Recupera su contabilidad original (Débitos y Créditos).
*   **IMPORTANTE:** Intenta recuperar su **Número Consecutivo** original.

> [!WARNING]
> **Conflicto de Consecutivos:**
> Si usted eliminó la *Factura #50* y, posteriormente, creó una *nueva* *Factura #50*, el sistema **NO** le permitirá restaurar la antigua, ya que no pueden existir dos documentos del mismo tipo con el mismo número.
>
> **Solución:** Deberá cambiar el número de la factura nueva o eliminarla temporalmente para liberar el cupo de la #50 antigua.

---

## 5. Preguntas Frecuentes

*   **P: ¿Cómo vaciar la papelera definitivamente?**
    *   **R:** Por seguridad y cumplimiento de normas de auditoría (NIIF), la opción de "Vaciar Papelera" está restringida exclusivamente al Super-Administrador de la base de datos o personal de Soporte Técnico. Los usuarios funcionales no pueden destruir evidencia forense.

*   **P: ¿Puedo ver el detalle (cuentas, terceros) de un documento en la papelera?**
    *   **R:** No directamente. Debe restaurarlo primero para poder inspeccionar su contenido detallado. La papelera solo muestra los datos de encabezado.

*   **P: ¿Cuánto tiempo se guardan los archivos?**
    *   **R:** Indefinidamente. El sistema no borra automáticamente nada a menos que se ejecute una purga de base de datos manual.

*   **P: ¿Quién puede entrar a la papelera?**
    *   **R:** El acceso suele estar restringido a usuarios con perfil de Administrador o Auditor, ya que ver documentos eliminados puede revelar información sensible.
