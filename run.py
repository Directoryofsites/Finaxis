
import uvicorn
import os

def print_banner():
    print("=" * 55)
    print("  FINAXIS - Sistema Contable (MODO RED)")
    print("  Version: 1.1")
    print("  Backend API:  http://0.0.0.0:8765")
    print("  Estado:       ESCUCHANDO EN TODA LA RED LOCAL")
    print("=" * 55)

if __name__ == "__main__":
    # Force GIO monitor disable to avoid recursive reload issues with WeasyPrint
    os.environ['GIO_USE_VOLUME_MONITOR'] = 'dummy'
    
    print_banner()
    
    # Run Uvicorn
    # reload=True para desarrollo local. 
    # Agregamos 'build' a reload_excludes para evitar el error de "Ruta no encontrada"
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8765, 
        reload=False,  # False en produccion: evita inestabilidad en el .exe y en modo red
        log_level="info"
    )
