---
description: Procedimiento para centralizar y sincronizar el código de Kyro y Antigravity en la rama Main.
---

# Flujo de Trabajo: Sincronización de IAs (Kyro + Antigravity)

Este flujo define cómo integrar el trabajo de ambos asistentes de manera segura, permitiendo que **Antigravity** actúe como el "Jefe de Integración" en tu PC local.

## 1. Instrucciones para Kyro (La otra IA)
Cuando termines de trabajar con Kyro, solo pídele esto:
> "Sube tus cambios a tu rama `kiro-rama`. No toques main."

Kyro ejecutará:
```bash
git add .
git commit -m "Descripción de cambios"
git push origin kiro-rama
```

## 2. Instrucciones para Antigravity (Aquí en local)
Yo me encargaré de traer el trabajo de Kyro, juntarlo con el mío y subirlo todo limpio a la rama principal (`main`).

**Comando Turbo para Antigravity:**
Puedes decirme: `/slash-command sincronizacion-ias` (o simplemente "Sincroniza el trabajo de Kyro").

Yo ejecutaré internamente:
// turbo-all
1. Descargar cambios remotos (sin mezclar aún)
   `git fetch origin`
2. Asegurar que estoy en main
   `git checkout main`
3. Fusionar el trabajo de Kyro (kiro-rama) en main
   `git merge origin/kiro-rama`
4. Fusionar mi propio trabajo (antigravity-rama) en main
   `git merge antigravity-rama`
5. Subir la versión definitiva a GitHub
   `git push origin main`

## 3. Cierre del Ciclo (Actualizar a Kyro)
Una vez yo te confirme "Sincronización Completada", vuelves con Kyro y le dices:
> "Actualízate con `main`, ya está todo integrado."

Kyro ejecutará:
```bash
git pull origin main
```

---
**Ventajas de este método:**
1.  **Cero Conflictos Remotos:** Kyro nunca toca `main` directamente, así no "choca" con lo que yo hago.
2.  **Control Local:** Tú y yo resolvemos cualquier problema aquí en tu PC antes de publicar la versión final.
3.  **Orden:** Cada IA trabaja en su carril (`kiro-rama`, `antigravity-rama`) y solo se mezclan cuando tú lo ordenas.
