from app.core.database import SessionLocal
from app.models.empresa import Empresa

def asignar_cuota_todas_empresas():
    db = SessionLocal()
    empresas = db.query(Empresa).all()
    count = 0
    for emp in empresas:
        if emp.limite_mensajes_ia_mensual is None or emp.limite_mensajes_ia_mensual <= 0:
            emp.limite_mensajes_ia_mensual = 5000  # Asignar 5000 mensajes de prueba
            emp.consumo_mensajes_ia_actual = 0
            count += 1
    
    db.commit()
    print(f"Se asignó cuota de IA a {count} empresas locales.")
    db.close()

if __name__ == "__main__":
    asignar_cuota_todas_empresas()
