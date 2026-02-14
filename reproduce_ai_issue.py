import asyncio
import json
import os
import sys

# Add app directory to path
sys.path.append(os.path.join(os.getcwd(), 'app'))

from services.ai_agent import procesar_comando_natural

async def test_command(command):
    print(f"\nPROMPT: {command}")
    result = await procesar_comando_natural(command)
    print(f"AI RESPONSE: {json.dumps(result, indent=2, ensure_ascii=False)}")

async def main():
    # Caso 1: Movimiento de cuenta (Sin mencionar terceros)
    await test_command("movimiento de la cuenta de cafeteria")
    
    # Caso 2: Movimiento de cuenta Y terceros
    await test_command("movimiento de cafeteria y sus terceros")

    # Caso 3: El reporte de saldos original (para no romperlo)
    await test_command("de la cuenta de gastos de cafetería tráeme todos los terceros")

if __name__ == "__main__":
    asyncio.run(main())
