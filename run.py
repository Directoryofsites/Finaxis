# C:\ContaPY2\run.py

import os
import uvicorn

if __name__ == "__main__":
    # 1. Se establece la variable de entorno ANTES de que uvicorn inicie.
    os.environ['GIO_USE_VOLUME_MONITOR'] = 'dummy'

    # Se obtiene el puerto desde la variable de entorno, por defecto 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=True, reload_dirs=["app"])