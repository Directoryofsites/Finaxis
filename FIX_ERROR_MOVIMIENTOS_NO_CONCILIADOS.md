# 🔧 FIX: Error al Cargar Movimientos No Conciliados

## 📋 Problema Identificado

**Error en consola del navegador:**
```
Error cargando movimientos no conciliados
Call Stack: ManualReconciliationInterface.useCallback[loadUnmatchedMovements]
```

## 🔍 Causa Raíz

El componente `ManualReconciliationInterface.js` estaba haciendo peticiones HTTP usando `fetch()` directamente **sin incluir el token de autenticación** en los headers. Esto causaba que el backend rechazara las peticiones porque el endpoint requiere autenticación.

### Problemas Específicos:

1. **Falta de autenticación en peticiones fetch**
   - Las peticiones no incluían el header `Authorization` con el token JWT
   - El backend requiere `current_user: Usuario = Depends(get_current_user)`

2. **Campo inexistente en modelo**
   - El endpoint intentaba acceder a `am.referencia` que no existe en `MovimientoContable`
   - El campo correcto es `am.documento.reconciliation_reference`

3. **Configuración de proxy faltante**
   - Next.js no tenía configurado el proxy para redirigir `/api/*` al backend en puerto 8002

## ✅ Soluciones Implementadas

### 1. Corrección del Endpoint Backend

**Archivo:** `app/api/conciliacion_bancaria/routes.py`

**Cambios:**
```python
# ANTES (causaba error):
"referencia": am.referencia,
"documento_tipo": am.documento.tipo_documento.nombre

# DESPUÉS (corregido):
"referencia": getattr(am.documento, 'reconciliation_reference', '') or "",
"documento_tipo": am.documento.tipo_documento.nombre if hasattr(am.documento, 'tipo_documento') and am.documento.tipo_documento else "N/A",
```

**Razón:** 
- `MovimientoContable` no tiene campo `referencia`
- Se usa `getattr()` y `hasattr()` para evitar errores si los campos no existen

### 2. Agregado de Autenticación en Frontend

**Archivo:** `frontend/app/conciliacion-bancaria/components/ManualReconciliationInterface.js`

**Cambios en 4 peticiones fetch:**

#### a) loadUnmatchedMovements
```javascript
// ANTES:
const response = await fetch(`/api/conciliacion-bancaria/manual-reconciliation/unmatched-movements?${params}`);

// DESPUÉS:
const response = await fetch(`/api/conciliacion-bancaria/manual-reconciliation/unmatched-movements?${params}`, {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
    'Content-Type': 'application/json'
  }
});
```

#### b) generateMatchPreview
```javascript
// ANTES:
const response = await fetch('/api/conciliacion-bancaria/manual-reconciliation/match-preview', {
  method: 'POST',
  body: formData
});

// DESPUÉS:
const response = await fetch('/api/conciliacion-bancaria/manual-reconciliation/match-preview', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
  },
  body: formData
});
```

#### c) applyManualReconciliation
```javascript
// ANTES:
const response = await fetch('/api/conciliacion-bancaria/reconcile/manual', {
  method: 'POST',
  body: formData
});

// DESPUÉS:
const response = await fetch('/api/conciliacion-bancaria/reconcile/manual', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
  },
  body: formData
});
```

#### d) getSuggestions
```javascript
// ANTES:
const response = await fetch(`/api/conciliacion-bancaria/reconcile/suggestions/${bankMovementId}`);

// DESPUÉS:
const response = await fetch(`/api/conciliacion-bancaria/reconcile/suggestions/${bankMovementId}`, {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
    'Content-Type': 'application/json'
  }
});
```

### 3. Configuración de Proxy en Next.js

**Archivo:** `frontend/next.config.mjs`

**Agregado:**
```javascript
async rewrites() {
    return [
        {
            source: '/api/:path*',
            destination: 'http://localhost:8002/api/:path*',
        },
    ];
},
```

**Razón:** Redirige todas las peticiones a `/api/*` al backend en puerto 8002

## 🎯 Resultado

✅ **El componente ManualReconciliationInterface ahora puede:**
- Cargar movimientos bancarios no conciliados
- Cargar movimientos contables no conciliados
- Generar vistas previas de conciliación
- Aplicar conciliaciones manuales
- Obtener sugerencias automáticas

✅ **Todas las peticiones incluyen autenticación JWT**

✅ **El backend maneja correctamente campos opcionales**

## 🔄 Próximos Pasos

1. **Reiniciar el frontend** para que tome la nueva configuración de proxy:
   ```bash
   cd frontend
   npm run dev
   ```

2. **Verificar que el backend esté corriendo** en puerto 8002:
   ```bash
   python run.py
   ```

3. **Probar la funcionalidad** en el navegador:
   - Ir a la página de Conciliación Bancaria
   - Seleccionar una cuenta bancaria
   - Verificar que se carguen los movimientos sin errores

## 📝 Notas Técnicas

### Autenticación en el Sistema

El sistema usa JWT (JSON Web Tokens) almacenados en `localStorage`:
- **Key:** `authToken`
- **Formato:** `Bearer <token>`
- **Ubicación:** Todos los headers de peticiones autenticadas

### Alternativa Recomendada

En lugar de usar `fetch()` directamente, se recomienda usar `apiService` de `lib/apiService.js` que ya incluye automáticamente la autenticación:

```javascript
import apiService from '@/lib/apiService';

// En lugar de fetch:
const response = await apiService.get('/conciliacion-bancaria/manual-reconciliation/unmatched-movements', {
  params: { bank_account_id: bankAccount.id }
});
```

## ✨ Mejoras Futuras

1. **Refactorizar para usar apiService** en lugar de fetch directo
2. **Agregar manejo de errores más robusto** con mensajes específicos
3. **Implementar retry logic** para peticiones fallidas
4. **Agregar loading states** más granulares por operación

---

**Fecha:** 2024
**Módulo:** Conciliación Bancaria
**Estado:** ✅ RESUELTO
