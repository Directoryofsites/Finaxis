# Manual de Usuario: Reportes de Remisiones (Auditoría de Entregas)

## 1. ¿Qué es y para qué sirve?
Este módulo es su **Centro de Control** para vigilar la mercancía que ha salido de la empresa.
Recuerde que una Remisión es "dinero en la calle" (mercancía entregada pero no cobrada). Este reporte le ayuda a responder preguntas vitales como:
*   *¿Qué entregamos el mes pasado y aún no hemos facturado?*
*   *¿Cuánto dinero tenemos represado en mercancía en consignación?*
*   *¿Qué despachos se cancelaron?*

---

## 2. El Tablero de Control (Lo primero que ve)

Al entrar, verá tres tarjetas grandes en la parte superior. Estos son los "Signos Vitales" de su operación:

1.  **Total Remisiones:** Es simplemente un contador. Le dice cuántos documentos se han creado en el periodo consultado.
2.  **💰 Pendientes por Facturar:** **¡EL NÚMERO MÁS IMPORTANTE!**
    *   Representa el valor total de la mercancía que usted ya entregó (salió de su bodega) pero que **aún no se ha convertido en venta real**.
    *   Este dinero no está "ni en el banco ni en la bodega". Debe hacerle seguimiento constante.
3.  **Anuladas:** Cantidad de despachos que fueron cancelados.

---

## 3. Cómo usar el Listado Detallado (Filtros)

La tabla muestra cientos de datos. Use los filtros de la barra superior para encontrar lo que busca:

### A. Filtrar por Fechas 📅
El sistema por defecto muestra el mes actual. Si quiere ver despachos antiguos:
1.  Haga clic en el selector de fechas.
2.  Elija "Desde" y "Hasta".
3.  La tabla se actualizará automáticamente.

### B. Filtrar por Estado (El semáforo) 🚦
*   **TODAS:** Muestra un histórico completo. Úselo para auditorías generales.
*   **BORRADOR:** Muestra documentos incompletos. Úselo para limpiar basura del sistema.
*   **APROBADA (Alerta 🚨):** Muestra las remisiones que están listas, entregadas y vivas, pero **sin facturar**.
    *   *Acción recomendada:* Revise esta lista semanalmente. Llame a esos clientes y pregunte si ya puede enviar la factura.
*   **FACTURADA:** Muestra despachos exitosos que ya cerraron el ciclo.

### C. Buscar por Cliente 🔍
En la casilla "Buscar Tercero", escriba el nombre (ej. "Juan") o el NIT. El sistema filtrará inmediatamente todos los despachos a ese cliente específico.

---

## 4. Exportar Datos (Sacar la información)

A veces necesita trabajar estos datos en Excel o enviarlos al contador.

*   **Botón [PDF]:** Genera un documento bonito, listo para imprimir y firmar. Úselo para reportes físicos a gerencia.
*   **Botón [EXCEL]:** Descarga un archivo `.xlsx`. Úselo si necesita sumar, hacer tablas dinámicas o cruzar datos con otros sistemas.

---

## 5. Preguntas Frecuentes (FAQ)

**1. ¿Por qué el "Total Pendiente" no coincide con mis Cuentas por Cobrar?**
Porque son cosas distintas.
*   **Cuentas por Cobrar:** Es deuda de FACTURAS (ya hay obligación legal de pago).
*   **Pendiente Remisión:** Es mercancía entregada SIN FACTURA. Legalmente es un inventario en poder de terceros, no una deuda financiera todavía.

**2. Veo una remisión antigua que ya me pagaron, pero aquí sale como "Aprobada". ¿Por qué?**
Si ya se la pagaron, significa que hicieron la factura *sin cruzarla* con la remisión (hicieron la factura directa).
*   **Consecuencia:** Usted descargó el inventario DOS VECES (una al remitir, una al facturar).
*   **Solución:** Debe anular esa remisión antigua para corregir el inventario, ya que la factura real hizo la salida definitiva.

**3. ¿Cómo sé qué productos exactos tiene una remisión de la lista?**
Haga clic en el icono del **Ojo (👁️)** o **Lupita** al lado derecho de cada fila. Se abrirá una ventana con el detalle de ítems, cantidades y precios.

**4. ¿Puedo ver quién creó la remisión?**
Sí. En la exportación a Excel sale una columna llamada "Usuario Creador", útil para auditoría interna.
