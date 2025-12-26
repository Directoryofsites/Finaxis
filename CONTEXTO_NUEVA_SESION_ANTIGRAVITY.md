# CONTEXTO GRABADO PARA NUEVA SESIÓN DE IA (ANTIGRAVITY)
> **Fecha:** 25 de Diciembre de 2025
> **Estado:** Fase de Refinamiento Completada. Iniciando Migración Masiva.

Hola, próxima instancia de Antigravity. Aquí tienes el estado actual del proyecto para que continúes sin preguntar obviedades.

## 1. El Objetivo
Estamos dotando a **ContaPY2** de automatización por voz para reportes contables.
El flujo es:
`Voz (Frontend) -> AI Analysis (Backend) -> Tool Selection -> URL Param Injection -> Page Auto-Execution -> PDF/Email Dispatch`.

## 2. Arquitectura OBLIGATORIA (No usar if/else)
Hemos migrado a un patrón de **Registry + Hooks** para evitar deuda técnica.
*   **Backend:** Los reportes heredan de `BaseReport` y se registran con `@ReportRegistry.register`.
*   **Frontend:** Las páginas usan `useAutoReport('key', callback)` para manejar la automatización.

## 3. Logros Recientes (Critical Knowledge)

### A. Solución "Triple Capa" en Búsqueda de Cuentas (`auxiliar-cuenta/page.js`)
Logramos que la búsqueda de cuentas sea resistente a errores humanos:
1.  **Fonética:** Implementamos `v->b, z->s, c->s` (ej: "Grabados" == "Gravados").
2.  **Hojas:** Priorizamos cuentas Auxiliares (+25 pts) sobre Grupos.
3.  **Desempate:** En empate, gana el nombre más largo (más específico).

### B. Corrección de "Secuestro" (Hijacking)
En `RightSidebar.js`, corregimos interceptores agresivos.
*   *Regla:* Si el usuario dice "Contabilidad", NUNCA redirigir al módulo de Inventarios, aunque diga la palabra "inventario".

### C. Fechas por Defecto
El System Prompt (`ai_agent.py`) está configurado para asumir `01-Ene` a `Hoy` si no se dan fechas.

### D. Control de Formularios por Voz (Captura Rápida)
Implementamos "Auto-Fill" diferido en `contabilidad/captura-rapida`.
*   **Parámetros:** `ai_plantilla`, `ai_tercero`, `ai_valor`.
*   **Lógica:** Fuzzy matching (Cliente) -> Aplicación de Valor (Diferida 800ms) -> Auto-Guardado (2s delay).
*   **Patrón:** "The 3-Stage Rocket" (Documentado en Protocolo Sec. 11).

## 4. Tareas Pendientes (Tu Misión)
Revisa `task.md` para más detalles, pero el foco es **FASE 3: MIGRACIÓN MASIVA**.

1.  **Migrar Reportes Restantes al Registry:**
    *   Actualmente solo "Super Informe Inventarios" y "Rentabilidad" usan la arquitectura nueva 100%.
    *   **Auxiliar por Cuenta:** Funciona perfecto, pero falta migrar su backend al Registry (actualmente usa endpoint legacy con params manuales).
    *   **Balance de Prueba / Estado de Resultados:** Siguen en el modelo antiguo.

2.  **Consolidación:**
    *   Asegurar que TODOS los reportes usen `useAutoReport` en el frontend.

## 5. Referencias
*   **Protocolo Técnico:** `C:\ContaPY2\Manual\PROTOCOLO_IA_AUTOMATIZACION.md` (Lectura OBLIGATORIA).
*   **Agent Logic:** `C:\ContaPY2\app\services\ai_agent.py`.

*Buena suerte.*
