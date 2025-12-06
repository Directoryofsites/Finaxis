# 📘 Manual de Sincronización Git (Modo 2 PCs)

Este manual explica cómo trabajar en el proyecto **Finaxis / ContaPY2** utilizando dos o más computadores simultáneamente sin perder datos.

## 🌟 La Regla de Oro
> **GitHub es la fuente de la verdad.** 
> Tus PCs son solo estaciones de trabajo temporales. Nunca confíes en que lo que hay en tu PC es lo "último" hasta que no hayas sincronizado con GitHub.

---

## 🚀 1. Configuración Inicial (Solo la primera vez en un PC Nuevo)

Si te sientas en un computador donde **NUNCA** has trabajado en este proyecto:

1.  **Instalar Prerrequisitos:**
    *   [Instalar Git](https://git-scm.com/download/win) (Siguiente a todo).
    *   [Instalar VS Code](https://code.visualstudio.com/).

2.  **Clonar el Proyecto:**
    *   Crea una carpeta vacía (ej: `C:\ContaPY2`).
    *   Abre esa carpeta, clic derecho -> "Git Bash Here" o abre la terminal.
    *   Ejecuta:
        ```bash
        git clone https://github.com/Directoryofsites/Finaxis.git .
        ```
        *(⚠️ Ojo al punto al final. Significa "aquí mismo". Si no lo pones, creará una subcarpeta).*

3.  **Configurar Entorno Virtual:**
    *   Ejecuta: `python -m venv .venv`
    *   Ejecuta: `.venv\Scripts\pip install -r requirements.txt`

---

## ☀️ 2. Rutina Diaria (El Ritual Sagrado)

Para prevenir errores, repite esto como un mantra.

### ☕ Al Empezar el Día (Antes de escribir código)
**Objetivo:** Traer al PC actual lo que trabajaste ayer en el otro PC.

1.  Abre la terminal en la carpeta del proyecto.
2.  Ejecuta:
    ```bash
    git pull
    ```
    *   *Si dice "Already up to date":* Nadie hizo nada nuevo. Puedes empezar.
    *   *Si descarga archivos:* ¡Bien! Ya tienes la última versión.

### 🌙 Al Terminar el Día (Antes de apagar el PC)
**Objetivo:** Guardar tu trabajo en la nube para que el otro PC lo reciba mañana.

1.  Abre la terminal.
2.  Ejecuta estos 3 comandos en orden:
    ```bash
    git add .
    ```
    *(Prepara TODOS los archivos modificados para ser guardados).*

    ```bash
    git commit -m "Descripción breve de lo que hice hoy"
    ```
    *(Sella los cambios en tu PC con un mensaje).*
    
    ```bash
    git push
    ```
    *(Envía el paquete a la nube/GitHub).*

---

## 🚑 3. Solución de Problemas Comunes

### 🔴 Error: "Git Push Failed" / "Updates were rejected"
**Causa:** Intentaste subir (`push`) cambios pero alguien (quizás tú mismo en el otro PC) subió cosas antes y no las descargaste. GitHub protege el proyecto rechazando tu subida.

**Solución:**
1.  Descarga primero: `git pull`.
2.  Es posible que Git mezcle todo automáticamente.
3.  Si todo sale bien, intenta subir de nuevo: `git push`.

### 🟠 "Merge Conflict" (Conflicto de Fusión)
**Causa:** Ambos PCs modificaron la **mismo archivo** en la **misma línea**. Git no sabe cuál versión elegir.

**Solución:**
1.  Abre el archivo "rojo" (el que tiene conflicto).
2.  Verás signos como `<<<<<<< HEAD` y `>>>>>>>`.
3.  Borra manualente el código que NO quieres y deja el código correcto.
4.  Borra las marcas raras (`<<<`, `===`, `>>>`).
5.  Guarda el archivo.
6.  Ejecuta:
    ```bash
    git add .
    git commit -m "Arreglando conflicto"
    git push
    ```

---

## 🧪 Comandos Útiles Extra

*   `git status`: Te dice qué archivos has modificado pero no has guardado.
*   `git log`: Muestra el historial de quién hizo qué y cuándo.
