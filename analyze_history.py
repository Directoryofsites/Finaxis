from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Setup DB connection
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    print(f"--- Analyzing HistorialConsumo Data Distribution ---")
    
    # 1. Total count
    total = db.execute(text("SELECT count(*) FROM historial_consumo")).scalar()
    print(f"Total Records: {total}")

    # 2. Group by Month/Year
    print("\n--- Records by Month ---")
    sql_by_month = text("""
        SELECT to_char(fecha, 'YYYY-MM') as mes, count(*) as cantidad
        FROM historial_consumo 
        GROUP BY mes
        ORDER BY mes DESC
    """)
    results = db.execute(sql_by_month).fetchall()
    
    if not results:
        print("No records found.")
    else:
        for row in results:
            print(f"{row[0]}: {row[1]} records")

    # 3. Sample of the 'mystery' 371 records (if any)
    print("\n--- Sample Records (First 5) ---")
    sql_sample = text("SELECT id, fecha, tipo_operacion, cantidad FROM historial_consumo ORDER BY id ASC LIMIT 5")
    samples = db.execute(sql_sample).fetchall()
    for s in samples:
        print(f"ID: {s[0]} | Date: {s[1]} | Type: {s[2]} | Amount: {s[3]}")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
