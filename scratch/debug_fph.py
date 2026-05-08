
import sqlite3
import os

db_path = 'contapy.db'
if not os.path.exists(db_path):
    print(f"No se encuentra {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- INVESTIGANDO DOCUMENTO 1649 ---")
cursor.execute("""
    SELECT d.id, d.numero, d.tipo_documento_id, t.codigo, t.nombre, d.anulado, d.estado, d.empresa_id
    FROM documentos d 
    LEFT JOIN tipos_documento t ON d.tipo_documento_id = t.id 
    WHERE d.numero = '1649'
""")
rows = cursor.fetchall()
for row in rows:
    print(f"ID: {row[0]}, Num: {row[1]}, TipoID: {row[2]}, TipoCod: {row[3]}, TipoNom: {row[4]}, Anulado: {row[5]}, Estado: {row[6]}, EmpresaID: {row[7]}")

print("\n--- INVESTIGANDO TIPOS DE DOCUMENTO (FPH) ---")
cursor.execute("SELECT id, codigo, nombre FROM tipos_documento WHERE nombre LIKE '%Propiedad%' OR codigo LIKE '%FPH%'")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Cod: {row[1]}, Nom: {row[2]}")

print("\n--- VERIFICANDO MOVIMIENTOS PARA DOCUMENTO 1649 ---")
cursor.execute("SELECT id, cuenta_id, debito, credito FROM movimientos_contables WHERE documento_id = (SELECT id FROM documentos WHERE numero = '1649' LIMIT 1)")
for row in cursor.fetchall():
    print(f"MovID: {row[0]}, CuentaID: {row[1]}, Deb: {row[2]}, Cred: {row[3]}")

conn.close()
