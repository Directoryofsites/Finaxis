# Estudio Técnico: Arquitectura de Reportes Unificada (The "Sweep" Strategy)

**Fecha:** 24 de Diciembre de 2025
**Objetivo:** Eliminar la implementación manual ("reporte por reporte") de funciones de IA, PDF y Correo.
**Estado Actual:** Fragmentado / Manual.
**Estado Propuesto:** Automatizado / Basado en Registros.

---

## 1. El Problema: "La Trampa del `If/Else`"

Actualmente, cada vez que queremos que la IA soporte un nuevo reporte, tenemos que "tocar" 4 puntos diferentes. Esto es lo que está haciendo el trabajo eterno:

1.  **Frontend (Page.js):** Lógica personalizada en `useEffect` para leer parámetros.
2.  **API Router (`dispatch-email`):** Un bloque `if/elif` gigante que crece infinitamente.
3.  **Servicio (`reportes_service.py`):** Funciones con nombres únicos (`generar_pdf_x`, `generar_pdf_y`) sin estandarizar.
4.  **IA Tool (`ai_agent.py`):** Definiciones manuales de parámetros.

Si tenemos 50 reportes, haremos este trabajo 50 veces. **Esto es insostenible.**

---

## 2. La Solución: "Registry Pattern" (Patrón de Registro)

La solución "experta" no es programar más, sino crear un **Sistema de Enchufes (Interface Standard)**. Si un reporte cumple con el estándar, el sistema (IA, Correo, PDF) lo absorbe automáticamente sin escribir código nuevo en los controladores.

### A. Backend: El Registro Maestro

En lugar de tener funciones sueltas, creamos una clase base y un registro central.

**Concepto:**
```python
# app/services/reporting/registry.py

# 1. Definir el "Contrato" (Interface)
class BaseReport:
    key = "nombre_clave_del_reporte"
    model_filter = FiltroPydanticModelo
    
    def get_data(self, db, empresa_id, filtros):
        raise NotImplementedError
        
    def generate_pdf(self, db, empresa_id, filtros) -> bytes:
        raise NotImplementedError

# 2. El Registro Automático
REPORT_REGISTRY = {}

def register_report(cls):
    REPORT_REGISTRY[cls.key] = cls()
    return cls

# 3. Uso en Reportes (Ejemplo Inventario)
@register_report
class InventoryReport(BaseReport):
    key = "super_informe_inventarios"
    
    def get_data(self, ...):
        # Lógica existente...
    
    def generate_pdf(self, ...):
         # Lógica existente...
```

### B. API: El Controlador Universal

Con el registro, el endpoint de correo (y el de descarga) se vuelve **genérico**. Nunca más tendrás que tocar este archivo al agregar un reporte.

**Código Universal (No se toca más):**
```python
@router.post("/universal/dispatch/{action}") # action: email, pdf
def universal_dispatch(payload: UniversalPayload):
    # 1. Buscar el reporte en el registro por su nombre
    report_service = REPORT_REGISTRY.get(payload.report_type)
    if not report_service:
        raise Error("Reporte no registrado")
        
    # 2. Ejecutar ciegamente (Polimorfismo)
    pdf_bytes = report_service.generate_pdf(db, user, payload.filtros)
    
    # 3. Accionar
    if action == 'email':
        send_email(pdf_bytes, payload.email)
    return pdf_bytes
```

---

## 3. Frontend: El "Hook" Maestro (`useAutoReport`)

En lugar de copiar y pegar el código del `useEffect` e `RightSidebar` en cada página, creamos un **Hook de React** (una pieza de lógica reutilizable).

**Cómo se vería `page.js` en el futuro:**

```javascript
import { useAutoReport } from '@/hooks/useAutoReport';

export default function CualquierReportePage() {
    // ESTA LÍNEA hace todo el trabajo sucio:
    // 1. Lee la URL (IA params)
    // 2. Ejecuta la búsqueda
    // 3. Detecta "ai_accion=email" y envía el correo automáticamente.
    const { resultados, filtros, loading } = useAutoReport({
        reportKey: 'super_informe_inventarios', // La clave única
        initialFilters: INITIAL_STATE
    });

    return ( <Tabla datos={resultados} /> );
}
```

---

## 4. IA: La "Barredora" (Discovery)

Para que la IA sepa qué reportes existen sin que tú se los enseñes uno a uno:

1.  Creamos un endpoint `/api/reports/meta` que devuelve la lista de claves en `REPORT_REGISTRY`.
2.  Al iniciar, el Agente IA lee esa lista.
3.  Si le pides "Reporte de Ventas", ella busca en su lista si tiene algo parecido a "ventas" y usa la clave correspondiente automáticamente.

---

## 5. Plan de Acción (Hoja de Ruta)

Para salir del ciclo de "trabajo manual", propongo detener la implementación individual y ejecutar esta refactorización en **3 Fases**:

### Fase 1: El Núcleo (Backend)
- [ ] Crear `app/core/reporting_registry.py`.
- [ ] Mover **1 solo reporte** (ej: Inventario) a este nuevo sistema para probar.
- [ ] Reemplazar el endpoint gigante `if/else` con el `universal_dispatch`.

### Fase 2: El Cliente (Frontend)
- [ ] Crear el hook `useAutoReport.js`.
- [ ] Limpiar `super-informe-inventarios/page.js` para usar el hook (reducirá el código en 100 líneas).

### Fase 3: Migración Masiva
- [ ] "Barrer" los archivos antiguos y migrarlos al registro uno por uno (pero será copiar/pegar rápido, no programar lógica).

---

### Conclusión
Tienes toda la razón. Seguir como vamos es un camino eterno. La arquitectura basada en **Registro y Polimorfismo** es la única forma profesional de escalar esto a cientos de reportes sin volverse loco.

**¿Autorizas proceder con la FASE 1 (Arquitectura Base) en lugar de seguir parchando reporte por reporte?**
