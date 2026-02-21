import sqlite3

try:
    conn = sqlite3.connect('contapy.db')
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE indicadores_economicos ADD COLUMN tasa_usura FLOAT DEFAULT 0;")
        print("tasa_usura añadida")
    except Exception as e:
        print("tasa_usura ya existe o error:", e)
        
    try:
        cursor.execute("ALTER TABLE indicadores_economicos ADD COLUMN fecha_sincronizacion DATE;")
        print("fecha_sincronizacion añadida")
    except Exception as e:
        print("fecha_sincronizacion ya existe o error:", e)
        
    conn.commit()
    conn.close()
    print("Columnas agregadas con exito en contapy.db.")
except Exception as e:
    print("Error general:", e)
