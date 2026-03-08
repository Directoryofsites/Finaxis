import sys
import os

# Set up environment
sys.path.append(r'c:\ContaPY2')
os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost:5432/contapy' # Adjust if needed

from app.database import SessionLocal
from app.models.tercero import Tercero

db = SessionLocal()
try:
    # Look for a third party with email and balance
    t = db.query(Tercero).filter(Tercero.email != None).first()
    if t:
        print(f"NIT: {t.nit}")
        print(f"Email: {t.email}")
    else:
        print("No third party with email found")
finally:
    db.close()
