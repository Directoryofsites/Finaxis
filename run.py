
import uvicorn
import os

if __name__ == "__main__":
    # Force GIO monitor disable to avoid recrusive reload issues with WeasyPrint
    os.environ['GIO_USE_VOLUME_MONITOR'] = 'dummy'
    
    # Run Uvicorn
    # Run Uvicorn with specific excludes to prevent crashing on large folders like node_modules
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        reload_excludes=["frontend/*", "node_modules/*", ".git/*"]
    )
