from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from datetime import datetime

# Setup DB connection
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

start_date = '2025-11-01'
end_date = '2025-11-30 23:59:59'

try:
    # 1. Check HistorialConsumo
    print(f"--- Checking HistorialConsumo for {start_date} to {end_date} ---")
    sql_historial = text("""
        SELECT count(*), empresa_id 
        FROM historial_consumo 
        WHERE fecha >= :start AND fecha <= :end
        GROUP BY empresa_id
    """)
    results_hist = db.execute(sql_historial, {"start": start_date, "end": end_date}).fetchall()
    if not results_hist:
        print("No matches in HistorialConsumo for this period.")
    else:
        for row in results_hist:
            print(f"Empresa {row[1]}: {row[0]} entries in HistorialConsumo")

    # 2. Check Documento (Real activity)
    print(f"\n--- Checking Documento (Accounting Activity) for same period ---")
    sql_docs = text("""
        SELECT count(*), empresa_id 
        FROM documentos 
        WHERE fecha >= :start AND fecha <= :end
        GROUP BY empresa_id
    """)
    results_docs = db.execute(sql_docs, {"start": start_date, "end": end_date}).fetchall()
    if not results_docs:
        print("No documents found in Documento for this period.")
    else:
        for row in results_docs:
            print(f"Empresa {row[1]}: {row[0]} entries in Documento")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
