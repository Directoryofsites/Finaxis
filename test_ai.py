import asyncio
from app.services.ai_agent import procesar_comando_natural

async def run():
    res = await procesar_comando_natural("Dame los ingresos y gastos de enero")
    print("RES:", res)

asyncio.run(run())
