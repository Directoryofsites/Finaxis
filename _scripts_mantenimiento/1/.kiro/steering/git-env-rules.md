---
inclusion: always
---

# Reglas Críticas de Git y Configuración

## REGLA OBLIGATORIA: Archivo .env

**BAJO NINGUNA CIRCUNSTANCIA añadir el archivo .env al repositorio Git**

### Prohibiciones Absolutas:
- ❌ NO ejecutar `git add .env`
- ❌ NO usar `git add .` sin verificar `git status` primero
- ❌ NO subir configuraciones locales al repositorio

### Estado Actual:
- El archivo `.env` ha sido eliminado del seguimiento de Git (`git rm --cached .env`)
- Añadido a `.gitignore` para prevenir commits accidentales
- Cada desarrollador mantiene su configuración local:
  - Kiro: `kiro_clean_db`
  - Desarrollador principal: `contapy_db`

### Procedimientos Permitidos:
- ✅ Compartir cambios de configuración a través de `.env.example`
- ✅ Comunicar cambios necesarios en el chat
- ✅ Verificar siempre `git status` antes de cualquier commit

### Consecuencias de Violación:
Romperá el acceso a la base de datos del otro entorno y causará conflictos de configuración.

---
**Esta regla debe ser recordada y aplicada en TODAS las sesiones de trabajo.**