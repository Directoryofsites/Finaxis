# 🚀 Guía de Inicialización para PC 2 (Con Cambios Pendientes)

**Objetivo:** Conectar el PC 2 a GitHub y subir sus cambios actuales sin "chocar" con lo que ya subió el PC 1.

Como el PC 2 ya tiene código trabajado pero no está conectado a Git, seguiremos este protocolo de seguridad ("Rama Paralela").

## 📋 Credenciales
*   **Repo URL:** `https://github.com/Directoryofsites/Finaxis.git`
*   **Usuario:** `Finaxis Dev`
*   **Email:** `dev@finaxis.com`

---

## 💻 Paso a Paso (Ejecutar en PC 2)

Abre la terminal en la carpeta del proyecto en PC 2 (`C:\ContaPY2`) y ejecuta uno a uno:

### 1. Inicialización
```bash
git init
git config user.name "Finaxis Dev"
git config user.email "dev@finaxis.com"
```

### 2. Conexión Remota
```bash
git remote add origin https://github.com/Directoryofsites/Finaxis.git
```

### 3. Seguridad (Crear Rama)
En lugar de subir directo a `main` (que ya existe y causaría error), creamos una rama temporal con tus cambios:

```bash
git checkout -b pc2-cambios-pendientes
```

### 4. Guardar Cambios Locales
```bash
git add .
git commit -m "Sincronizacion inicial desde PC 2"
```

### 5. Subir a la Nube
```bash
git push -u origin pc2-cambios-pendientes
```

---

## 🏁 ¿Y después?
Una vez aparezca el mensaje de éxito en la terminal:
1.  Avísale al Antigravity del PC 1.
2.  El PC 1 se encargará de fusionar (unir) tu rama `pc2-cambios-pendientes` con `main`.
3.  Al día siguiente, en PC 2, solo tendrás que hacer `git pull origin main` para tener todo unificado.
