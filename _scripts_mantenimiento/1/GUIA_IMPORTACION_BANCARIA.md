# 📥 Guía de Importación de Extractos Bancarios

## 🎯 ¿Qué es la Importación de Extractos Bancarios?

La importación de extractos bancarios te permite **subir el archivo que te da el banco** (TXT, CSV, Excel) directamente al sistema para que pueda:

1. **Leer automáticamente** todos los movimientos del banco
2. **Compararlos** con lo que tienes registrado en tu contabilidad
3. **Identificar diferencias** entre lo que el banco registró y lo que tú registraste
4. **Conciliar automáticamente** los movimientos que coinciden
5. **Alertarte** sobre movimientos que necesitan revisión manual

## 🚀 Cómo Usar la Importación

### Paso 1: Configurar el Formato del Banco

Antes de importar, necesitas configurar cómo leer el archivo de tu banco:

1. Ve a la pestaña **"Configuración"**
2. Haz clic en **"Nueva Configuración"**
3. Completa los datos:
   - **Nombre**: Ej. "Bancolombia - CSV"
   - **Banco**: Selecciona tu banco
   - **Formato**: CSV, TXT o Excel
   - **Delimitador**: Coma (,), punto y coma (;), tabulador, etc.
   - **Formato de fecha**: Ej. DD/MM/YYYY o YYYY-MM-DD
   - **Mapeo de campos**: Indica en qué columna está cada dato:
     - Columna de fecha
     - Columna de descripción
     - Columna de monto
     - Columna de referencia (opcional)

4. **Prueba la configuración** con un archivo de muestra
5. Guarda la configuración

### Paso 2: Importar el Archivo del Banco

1. Ve a la pestaña **"Importar"**
2. Selecciona:
   - **Cuenta bancaria**: La cuenta donde se registrarán los movimientos
   - **Configuración**: La configuración que creaste para ese banco
3. Haz clic en **"Continuar con Archivo"**
4. **Sube el archivo** que te dio el banco
5. El sistema **validará automáticamente** el archivo:
   - Te mostrará una vista previa de los datos
   - Te alertará si hay errores
   - Te mostrará cuántos movimientos se encontraron
6. Si todo está bien, haz clic en **"Importar Movimientos"**

### Paso 3: Revisar la Importación

Después de importar:

1. Verás un **resumen de la importación**:
   - Total de movimientos importados
   - Estado de la importación
   - Alertas de duplicados (si los hay)

2. Los movimientos quedan **listos para conciliar**

### Paso 4: Conciliar Automáticamente

1. Ve a la pestaña **"Conciliación"**
2. Haz clic en **"Conciliar Automáticamente"**
3. El sistema:
   - Comparará los movimientos del banco con tu contabilidad
   - Conciliará automáticamente los que coinciden
   - Te mostrará los que necesitan revisión manual

## 📋 Formatos de Archivo Soportados

### CSV (Valores Separados por Comas)
```csv
Fecha,Descripción,Monto,Referencia
2024-01-15,Transferencia recibida,1500000.00,TRF001
2024-01-16,Pago servicios,-250000.00,PSP002
```

### TXT (Texto Delimitado)
```txt
2024-01-15|Transferencia recibida|1500000.00|TRF001
2024-01-16|Pago servicios|-250000.00|PSP002
```

### Excel (XLS/XLSX)
Archivo de Excel con columnas organizadas:
| Fecha | Descripción | Monto | Referencia |
|-------|-------------|-------|------------|
| 2024-01-15 | Transferencia | 1500000 | TRF001 |

## ⚙️ Configuraciones Comunes por Banco

### Bancolombia
- **Formato**: CSV
- **Delimitador**: Coma (,)
- **Formato fecha**: DD/MM/YYYY
- **Columnas**: Fecha, Descripción, Débito, Crédito, Saldo

### Banco de Bogotá
- **Formato**: TXT
- **Delimitador**: Punto y coma (;)
- **Formato fecha**: YYYY-MM-DD
- **Columnas**: Fecha, Concepto, Valor, Referencia

### Davivienda
- **Formato**: Excel
- **Formato fecha**: DD/MM/YYYY
- **Columnas**: Fecha Transacción, Descripción, Valor, Número Referencia

## 🔍 Validaciones Automáticas

El sistema valida automáticamente:

✅ **Formato del archivo**: Verifica que sea CSV, TXT o Excel
✅ **Estructura**: Confirma que tenga las columnas necesarias
✅ **Fechas**: Valida que las fechas estén en el formato correcto
✅ **Montos**: Verifica que los montos sean números válidos
✅ **Duplicados**: Detecta movimientos que ya fueron importados
✅ **Datos obligatorios**: Asegura que fecha, descripción y monto estén presentes

## ⚠️ Manejo de Duplicados

Si el sistema detecta movimientos duplicados:

1. Te **alertará** antes de importar
2. Te mostrará **qué movimientos** están duplicados
3. Puedes elegir:
   - **Omitir duplicados**: No importar los que ya existen
   - **Importar todos**: Importar incluyendo duplicados (no recomendado)
   - **Revisar manualmente**: Ver cada duplicado antes de decidir

## 💡 Consejos y Mejores Prácticas

### ✅ Hacer
- **Configura una vez** por banco y reutiliza la configuración
- **Prueba con un archivo pequeño** antes de importar archivos grandes
- **Revisa la vista previa** antes de confirmar la importación
- **Importa regularmente** (semanal o mensualmente)
- **Verifica los duplicados** antes de importar

### ❌ Evitar
- No importes el mismo archivo dos veces
- No modifiques el archivo del banco manualmente
- No uses configuraciones de un banco para otro
- No ignores las alertas de validación

## 🆘 Solución de Problemas

### "Formato de fecha inválido"
**Solución**: Verifica que el formato de fecha en la configuración coincida con el del archivo.
- Ejemplo: Si el archivo tiene "15/01/2024", usa formato "DD/MM/YYYY"

### "Columna no encontrada"
**Solución**: Revisa el mapeo de campos en la configuración. Las columnas se cuentan desde 0.
- Columna 0 = Primera columna
- Columna 1 = Segunda columna, etc.

### "Archivo con errores"
**Solución**: 
1. Abre el archivo en Excel o un editor de texto
2. Verifica que todas las filas tengan el mismo número de columnas
3. Asegúrate de que no haya filas vacías al inicio
4. Confirma que el delimitador sea consistente

### "Duplicados detectados"
**Solución**: Esto es normal si ya importaste este período. Puedes:
1. Omitir los duplicados (recomendado)
2. Verificar si realmente son duplicados o movimientos similares

## 📊 Después de Importar

Una vez importados los movimientos:

1. **Dashboard**: Ve el resumen de movimientos importados
2. **Conciliación Automática**: Ejecuta la conciliación para emparejar movimientos
3. **Conciliación Manual**: Revisa y concilia manualmente los que no se emparejaron automáticamente
4. **Ajustes**: Genera ajustes automáticos para comisiones, intereses, etc.
5. **Reportes**: Genera reportes de conciliación en PDF o Excel

## 🎯 Flujo Completo de Trabajo

```
1. Descargar extracto del banco
   ↓
2. Configurar formato (solo la primera vez)
   ↓
3. Importar archivo
   ↓
4. Validar datos
   ↓
5. Confirmar importación
   ↓
6. Conciliar automáticamente
   ↓
7. Revisar pendientes manualmente
   ↓
8. Generar ajustes si es necesario
   ↓
9. Generar reporte final
```

## 📞 Soporte

Si tienes problemas con la importación:

1. Verifica que el archivo del banco esté en el formato correcto
2. Revisa la configuración de importación
3. Prueba con un archivo de muestra pequeño
4. Consulta los mensajes de error específicos
5. Contacta al soporte técnico si el problema persiste

---

**¡Listo!** Ahora puedes importar tus extractos bancarios y conciliar automáticamente. 🎉
