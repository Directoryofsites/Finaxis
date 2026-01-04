import sys
import os
 
# Add app path to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, engine # Import engine
from app.services.legacy_import_service import import_legacy_data
from datetime import date
 
# Setup DB
# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/contapy_db"
# engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()
 
def test_import():
   file_path = "backups/modelos/inf 1/AA99.TXT"
   if not os.path.exists(file_path):
       print(f"File not found: {file_path}")
       return
       
   with open(file_path, "rb") as f:
       content = f.read()
       
   print(f"Testing import with {file_path}...")
   
   # Dummy data
   empresa_id = 1
   period_date = date(2021, 1, 1)
   default_tercero_id = 1 # Assuming ID 1 exists
   
   with open("scripts/import_log.txt", "w", encoding="utf-8") as log_file:
       try:
           from app.services.legacy_import_service import LegacyParsingService
           
           # 1. Test Parsing Only
           entries = LegacyParsingService.parse_txt_report(content)
           log_file.write(f"Direct Parse Check: found {len(entries)} entries.\n")
           if len(entries) > 0:
               log_file.write(f"Sample Entry 0: {entries[0]}\n")
               log_file.write(f"Sample Entry 1: {entries[1]}\n")
               
           # 2. Test Import
           result = import_legacy_data(
               db=db,
               empresa_id=empresa_id,
               period_date=period_date,
               default_tercero_id=default_tercero_id,
               file_txt=content
           )
           log_file.write(f"Result: {result}\n")
           
       except Exception as e:
           log_file.write(f"Error during import: {e}\n")
           import traceback
           traceback.print_exc(file=log_file)
       finally:
           db.close()
   print("Log written to scripts/import_log.txt")
 
if __name__ == "__main__":
   test_import()
