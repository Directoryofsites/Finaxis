import json

filepath = r"C:\ContaPY2\backup_contable_IGLESIA_BIBLICA_GRACIA_Y_VIDA_2026-03-10 (9).json"

try:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"Tipo raíz: {type(data)}")
    if 'data' in data:
        print("Es un backup firmado (tiene 'data')")
        transacciones = data['data'].get('transacciones', [])
    else:
        print("Es un backup plano")
        transacciones = data.get('transacciones', [])
        
    print(f"Total de documentos en transacciones: {len(transacciones)}")
    
    if len(transacciones) > 0:
        doc = transacciones[0]
        movs = doc.get("movimientos_contables", [])
        print(f"Doc 1 ({doc.get('numero')}) - Movimientos: {len(movs)}")
        for i, m in enumerate(movs[:2]):
            print(f"  Mov {i+1}: Cuenta {m.get('cuenta_codigo')} | Deb {m.get('debito')} | Cred {m.get('credito')}")
            
except Exception as e:
    print(f"Error: {e}")
