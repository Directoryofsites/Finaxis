import asyncio
import json
from app.services.dataico_dispatcher import DataicoDispatcher

async def test_create_support_document():
    print("--- Probando Creación de Documento Soporte (SANDBOX) ---")
    client = DataicoDispatcher(
        dataico_account_id="002979c5-7c23-43ab-aa98-3fa7dce6e4d0",
        auth_token="a4afb1e20e856e8fb031b487efbfd239"
    )
    
    # Payload DUMMY mínimo de Documento Soporte (Ajustado para forzar validaciones formales de Dataico y entender esquema)
    ds_payload = {
        "actions": {
            "send_dian": False,
            "send_email": False
        },
        "support_doc": {
            "number": 999999,
            "prefix": "SETT", # SETT es usado comúnmente en el RUT de pruebas DIAN
            "issue_date": "2024-03-03T10:00:00-05:00",
            "payment_means_type": "CASH",
            "payment_date": "2024-03-03",
            "notes": ["Documento de prueba soporte ContaPY2"],
            "currency_code": "COP",
            "items": [
                {
                    "sku": "001",
                    "description": "Servicio profesional de prueba",
                    "price": 50000,
                    "quantity": 1,
                    "taxes": [
                        {
                            "tax_category": "IVA",
                            "tax_rate": 0
                        }
                    ]
                }
            ],
            "customer": {
                "party_type": "PERSON",
                "first_name": "PROVEEDOR",
                "family_name": "PRUEBA",
                "party_identification_type": "CC",
                "company_id": "123456789",
                "email": "proveedor@prueba.com",
                "address": {
                    "city": "BOGOTA",
                    "department": "BOGOTA",
                    "country": "CO",
                    "address_line": "Calle falsa 123"
                }
            }
        }
    }
    
    res = await client.create_support_document(ds_payload)
    print("Respuesta ds_payload:")
    print(json.dumps(res, indent=2))


async def main():
    await test_create_support_document()

if __name__ == "__main__":
    asyncio.run(main())
