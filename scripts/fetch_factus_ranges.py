
import sys
import os
import json
import logging
import requests

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE
from app.services.providers.factus_provider import FactusProvider

def fetch_ranges():
    db = SessionLocal()
    try:
        # Get the first active configuration
        config = db.query(ConfiguracionFE).filter(ConfiguracionFE.habilitado == True).first()
        
        if not config:
            logger.error("No active FE configuration found.")
            return

        logger.info(f"Using configuration for Empresa ID: {config.empresa_id}")
        
        # Parse credentials
        try:
            creds = json.loads(config.api_token)
        except json.JSONDecodeError:
            logger.error("Invalid API token format in database.")
            return

        # Initialize provider
        provider_config = {
            "environment": config.ambiente, 
            "client_id": creds.get("client_id"),
            "client_secret": creds.get("client_secret"),
            "username": creds.get("username"),
            "password": creds.get("password")
        }
        
        provider = FactusProvider(provider_config)
        
        # Login to get token
        logger.info("Authenticating with Factus...")
        provider.login()
        
        # Fetch ranges
        url = f"{provider.base_url}/v1/numbering-ranges"
        headers = provider._get_headers()
        
        logger.info(f"Fetching ranges from: {url}")
        resp = requests.get(url, headers=headers)
        
        if resp.status_code == 200:
            json_data = resp.json()
            logger.info("--- FULL JSON SAVED TO FILE ---")
            
            with open("factus_ranges_dump.json", "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2)
            
            logger.info(f"Size: {len(json_data.get('data', []))} items (if list)")
            
            ranges = json_data.get('data', [])
            
            if isinstance(ranges, dict):
                 logger.warning("Ranges received as DICT, converting to LIST values...")
                 ranges = list(ranges.values())
            
            if not isinstance(ranges, list):
                 logger.error(f"Ranges is not a list! Type: {type(ranges)}. Value: {ranges}")
                 return

            for r in ranges:
                if isinstance(r, dict):
                    logger.info(f"ID: {r.get('id')} | Code: {r.get('document_type')} | Prefix: {r.get('prefix')} | Name: {r.get('name')} | Resolution: {r.get('resolution_number')}")
                else:
                    logger.error(f"Range item is not a dict: {type(r)} -> {r}")
            
            # Auto-update if DS range found
            ds_range = next((r for r in ranges if r.get('document_type') == '5' or 'soporte' in str(r.get('name', '')).lower()), None)
            
            if ds_range:
                new_id = ds_range.get('id')
                logger.info(f"Found match for Documento Soporte Range ID: {new_id}")
                
                if config.ds_rango_id != new_id:
                    config.ds_rango_id = new_id
                    db.commit()
                    logger.info("UPDATED Configuration in Database.")
                else:
                    logger.info("Configuration already up to date.")
            else:
                logger.warning("No specific 'Documento Soporte' (Type 5) range found.")
                
        else:
            logger.error(f"Failed to fetch ranges. Status: {resp.status_code}. Response: {resp.text}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fetch_ranges()
