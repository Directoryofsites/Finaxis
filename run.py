# C:\ContaPY2\run.py

import os
import uvicorn

if __name__ == "__main__":
    # 1. Se establece la variable de entorno ANTES de que uvicorn inicie.
    os.environ['GIO_USE_VOLUME_MONITOR'] = 'dummy'

    # 2. Se le pasa el control a uvicorn para que inicie la aplicación.
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True, reload_dirs=["app"])