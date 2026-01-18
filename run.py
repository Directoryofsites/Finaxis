
import uvicorn
import os

if __name__ == "__main__":
    # Force GIO monitor disable to avoid recrusive reload issues with WeasyPrint
    os.environ['GIO_USE_VOLUME_MONITOR'] = 'dummy'
    
    # Run Uvicorn
    # Use 'app.main:app' string to enable reload
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
