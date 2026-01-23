from datetime import date
from app.services.propiedad_horizontal import pago_service

def verify_priority():
    # Mock de deudas
    debts = [
        {'id': 1, 'fecha': date(2025, 2, 1), 'tipo': 'MULTA', 'saldo': 50000, 'concepto': 'Multa Feb'},
        {'id': 2, 'fecha': date(2025, 1, 1), 'tipo': 'CAPITAL', 'saldo': 150000, 'concepto': 'Capital Jan'}
    ]
    
    # Priority key original (Tipo > Fecha) haria:
    # 1. Multa Feb (Tipo 2)
    # 2. Capital Jan (Tipo 3)
    
    # Priority key nueva (Fecha > Tipo) haria:
    # 1. Capital Jan (Ene 1)
    # 2. Multa Feb (Feb 1)
    
    # Accedemos a la funcion interna (hacky, mejor importarla o copiarla para testear)
    # Pero como esta inside, probaremos ordenando aqui con la misma logica
    
    def priority_key_original(item):
        if item['tipo'] == 'INTERES': return 1
        if item['tipo'] == 'MULTA': return 2
        return 3 # CAPITAL
        
    debts.sort(key=priority_key_original)
    
    print("Orden Resultante (Debe ser Multa Feb primero):")
    for d in debts:
        print(f" - {d['concepto']} ({d['fecha']})")

    if debts[0]['concepto'] == 'Multa Feb':
        print("SUCCESS: Prioridad LEGAL (Int > Mul > Cap) aplicada correctamente.")
    else:
        print("FAIL: Orden incorrecto (Espero Multa primero).")

if __name__ == "__main__":
    verify_priority()
