import os
import asyncio
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv("c:\\ContaPY2\\.env")

async def test_tutor():
    print("Iniciando prueba de Finaxis Tutor...")
    
    # Importar el servicio
    try:
        from app.services.tutor_service import tutor_service
        print("Servicio importado correctamente.")
    except Exception as e:
        print(f"Error al importar el servicio: {e}")
        return

    # Probar el parser de manuales directamente
    from app.services.manual_parser import get_combined_manuals_context
    manuals_dir = os.path.join("c:\\ContaPY2", "frontend", "public", "manual", "ph")
    print(f"Buscando manuales en: {manuals_dir}")
    
    try:
        context = get_combined_manuals_context(manuals_dir)
        print(f"Contexto obtenido. Longitud: {len(context)} caracteres.")
        if len(context) == 0:
            print("ADVERTENCIA: El contexto está VACÍO. Verifica la ruta de los manuales.")
    except Exception as e:
        print(f"Error en manual_parser: {e}")

    # Probar una consulta real
    query = "como hago para hacer un recibo?"
    history = []
    empresa_id = 1 # ID genérico para prueba
    user_id = 1
    
    print(f"Enviando consulta: '{query}'")
    try:
        result = await tutor_service.process_query(query, history, empresa_id, user_id)
        print("RESULTADO:", result)
    except Exception as e:
        print(f"EXCEPCIÓN EN process_query: {e}")

if __name__ == "__main__":
    asyncio.run(test_tutor())
