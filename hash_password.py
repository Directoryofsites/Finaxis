from passlib.context import CryptContext

# Usamos el mismo contexto que en nuestra aplicación
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ----- CAMBIA ESTA CONTRASEÑA POR LA QUE QUIERAS USAR -----
nueva_contrasena = "admin123" 
# -----------------------------------------------------------

hashed_password = pwd_context.hash(nueva_contrasena)

print("\n--- COPIA EL SIGUIENTE HASH ---\n")
print(hashed_password)
print("\n-------------------------------\n")