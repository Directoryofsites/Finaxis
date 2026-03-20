
from datetime import datetime, time
import sys
import os

# Simular el logger para que no falle el script
class MockLogger:
    def error(self, msg): print(f"ERROR: {msg}")
    def info(self, msg): print(f"INFO: {msg}")
    def warning(self, msg): print(f"WARN: {msg}")

logger = MockLogger()

def _parse_time(hora_str: str):
    """
    Copia exacta de la función implementada en scheduler_backup.py
    """
    hora_str = hora_str.strip().lower().replace(".", "").replace(" ", "") # Limpiar puntos y espacios: "a. m." -> "am"
    
    # Intentar 24h (HH:MM)
    try:
        if ":" in hora_str:
            return datetime.strptime(hora_str, "%H:%M").time()
    except ValueError:
        pass
        
    # Intentar 12h (HH:MM am/pm)
    formats = ["%I:%M%p", "%I:%M %p", "%H:%M%p", "%H:%M %p"]
    for fmt in formats:
        try:
            return datetime.strptime(hora_str, fmt).time()
        except ValueError:
            continue
            
    # Si falla todo, loguear y retornar default
    logger.error(f"[AutoBackup] No se pudo parsear el formato de hora: '{hora_str}'. Usando 03:00 por defecto.")
    return datetime.strptime("03:00", "%H:%M").time()

# Casos de prueba
test_cases = [
    "09:41",
    "09:41 a. m.",
    "09:41 am",
    "9:41 PM",
    "21:41",
    "asdf", # Caso inválido
    " 08:30  "
]

print("--- VERIFICACIÓN DE PARSEO DE HORA ---")
for case in test_cases:
    result = _parse_time(case)
    print(f"Input: '{case}' -> Result: {result}")
print("---------------------------------------")
