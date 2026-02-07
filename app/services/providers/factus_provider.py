
import requests
import json
from datetime import datetime
from fastapi import HTTPException

class FactusProvider:
    def __init__(self, config: dict):
        """
        config debe contener:
        - environment: 'PRUEBAS' o 'PRODUCCION'
        - client_id
        - client_secret
        - username
        - password
        """
        self.env = config.get('environment', 'PRUEBAS')
        self.base_url = "https://api-sandbox.factus.com.co" if self.env == 'PRUEBAS' else "https://api.factus.com.co"
        
        # Safety Check: Si no es PRODUCCION explícito, forzar sandbox en URL por si acaso
        if self.env != 'PRODUCCION' and 'sandbox' not in self.base_url:
             self.base_url = "https://api-sandbox.factus.com.co"

        self.auth_url = f"{self.base_url}/oauth/token"
        
        # FIX 405 ERROR: El endpoint correcto para emitir/validar suele ser /v1/bills/validate
        # Si v1/bills POST falla, es porque es solo para GET (Listar).
        # Intentamos con la ruta explícita de validación que sí acepta POST.
        self.validate_url = f"{self.base_url}/v1/bills/validate"
        
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.username = config.get('username')
        self.password = config.get('password')
        
        self.token = None
        self.token_expires_at = None

    def login(self):
        """Obtiene un nuevo token de acceso"""
        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password
        }
        
        try:
            resp = requests.post(self.auth_url, data=payload)
            resp.raise_for_status()
            data = resp.json()
            self.token = data['access_token']
            # Opcional: manejar expiración
            return self.token
        except Exception as e:
            print(f"Error Login Factus: {e}")
            if resp.text: print(f"Response: {resp.text}")
            raise HTTPException(status_code=500, detail="Error autenticando con Factus")

    def _get_headers(self):
        if not self.token:
            self.login()
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def emit(self, invoice_payload: dict):
        """Envía la factura a Factus"""
        headers = self._get_headers()
        
        # LOGICA DE REINTENTO SIMPLE 401
        try:
            resp = requests.post(self.validate_url, json=invoice_payload, headers=headers)
            if resp.status_code == 401:
                # Token vencido, reintentar una vez
                print("Token vencido, renovando...")
                self.login()
                headers = self._get_headers()
                resp = requests.post(self.validate_url, json=invoice_payload, headers=headers)
            
            resp_json = resp.json()

            # Factus devuelve 'Created', 'ok' o success dependiendo del endpoint
            if resp.status_code in [200, 201] and resp_json.get('status') in ['ok', 'Created', 'Success']:
                data_bill = resp_json.get('data', {}).get('bill', {})
                return {
                    "success": True,
                    "message": "Factura emitida exitosamente",
                    "cufe": data_bill.get('cufe'),
                    "xml_url": data_bill.get('public_url'), # URL pública de Factus
                    "dian_status": "ACEPTADO", # Factus valida sincrónicamente en Sandbox
                    "provider_response": resp_json
                }
            else:
                return {
                    "success": False,
                    "error": str(resp_json.get('message', 'Error desconocido en Factus')),
                    "details": resp_json
                }
                
        except Exception as e:
             return {"success": False, "error": f"Error de conexión Provider: {str(e)}"}
