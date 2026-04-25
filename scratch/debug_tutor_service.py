import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

# Mocking app context
import sys
sys.path.append('c:\\ContaPY2')

from app.services.tutor_service import tutor_service

async def main():
    print("PROBANDO TUTOR SERVICE...")
    try:
        res = await tutor_service.process_query(
            query="hola",
            history=[],
            empresa_id=1,
            user_id=1
        )
        print(f"RESULTADO: {res}")
    except Exception as e:
        print(f"ERROR_TUTOR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
