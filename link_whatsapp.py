from app.core.database import SessionLocal
from app.models.usuario import Usuario

db = SessionLocal()

# Vamos a buscar al usuario con id=1 (usualmente el administrador root)
user = db.query(Usuario).first()

if user:
    # Meta envía los teléfonos de Colombia sin el '+', es decir '573234259925'
    user.whatsapp_number = "573234259925"
    db.commit()
    print(f"Número de WhatsApp vinculado exitosamente a: {user.nombre_completo or user.email}")
else:
    print("No se encontraron usuarios en la base de datos.")
