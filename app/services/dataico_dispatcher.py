import aiohttp
import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class DataicoDispatcher:
    """
    Cliente de integración con DATAICO.
    Maneja Facturación Electrónica (FE), Documento Soporte (DS), Notas de Crédito, etc.
    """
    def __init__(self, dataico_account_id: Optional[str] = None, auth_token: Optional[str] = None):
        self.dataico_account_id = (dataico_account_id or os.getenv("DATAICO_ACCOUNT_ID") or "").strip()
        self.auth_token = (auth_token or os.getenv("DATAICO_AUTH_TOKEN") or "").strip()
        self.base_url = "https://api.dataico.com/direct/dataico_api/v2"
        
        self.headers = {
            "Content-Type": "application/json",
            "Dataico-Account-Id": self.dataico_account_id or "",
            "Auth-token": self.auth_token or ""
        }

    async def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Metodo base privado para orquestar llamadas a la API de Dataico"""
        url = f"{self.base_url}{endpoint}"
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                request_kwargs = {}
                if data:
                    request_kwargs["json"] = data
                
                print(f"[DATAICO] {method} Request to {url}")
                safe_headers = {k: (v[:5] + "..." if k.lower() == "auth-token" else v) for k, v in self.headers.items()}
                print(f"[DATAICO] Headers: {safe_headers}")
                print(f"[DATAICO] Payload: {json.dumps(data, indent=2)}")

                async with session.request(method, url, **request_kwargs) as response:
                    status = response.status
                    try:
                        # Forzamos content_type=None para que no falle si el servidor responde con otro mime (como octet-stream en 401s)
                        resp_data = await response.json(content_type=None)
                    except Exception:
                        resp_text = await response.text()
                        resp_data = {"raw_text": resp_text}

                    if 200 <= status < 300:
                        print(f"[DATAICO] Success ({status})")
                        return {"success": True, "status": status, "data": resp_data}
                    else:
                        print(f"[DATAICO] API Error ({status}): {resp_data}")
                        logger.error(f"Dataico API Error ({status}): {resp_data}")
                        return {"success": False, "status": status, "detail": resp_data}
            except Exception as e:
                print(f"[DATAICO] Exception during request: {str(e)}")
                logger.error(f"Dataico API Exception: {str(e)}")
                return {"success": False, "error": str(e)}

    async def create_invoice(self, invoice_payload: Dict) -> Dict[str, Any]:
        """
        Crea una Factura Electrónica (FE).
        invoice_payload: Dict con la estructura JSON que requiere DATAICO (actions, invoice, etc.)
        """
        return await self._request("POST", "/invoices", data=invoice_payload)

    async def create_support_document(self, support_doc_payload: Dict) -> Dict[str, Any]:
        """
        Crea un Documento Soporte en Adquisición (DS).
        support_doc_payload: Dict con la estructura JSON para el documento soporte.
        """
        return await self._request("POST", "/support_docs", data=support_doc_payload)

    async def get_invoice(self, invoice_number_or_uuid: str) -> Dict[str, Any]:
        """
        Consulta una factura por su UUID o número de factura
        """
        # La forma canónica de GET es /invoices/{uuid} o /invoices con params, se usa /{id}
        return await self._request("GET", f"/invoices/{invoice_number_or_uuid}")


async def run_test():
    # TEST DRIVER
    print("Iniciando prueba de conexión Dataico...")
    client = DataicoDispatcher(
        dataico_account_id="002979c5-7c23-43ab-aa98-3fa7dce6e4d0",
        auth_token="a4afb1e20e856e8fb031b487efbfd239"
    )
    # Test validación conexión (GET genérico que no existe el param)
    res = await client.get_invoice("DUMMY-UUID-TEST")
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_test())
