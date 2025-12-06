# reset_password.py
from app.core.security import get_password_hash

# IMPORTANTE: Coloca aquí la contraseña que quieres establecer.
NUEVA_CONTRASENA = "Panica35576"

# El email del usuario que vamos a actualizar.
EMAIL_USUARIO = "hector811880@contapy.com"

nuevo_hash = get_password_hash(NUEVA_CONTRASENA)

print("="*70)
print("      *** SCRIPT PARA RESETEAR CONTRASEÑA DE SOPORTE ***")
print("="*70)
print(f"Nuevo HASH generado para la contraseña: {nuevo_hash}")
print("\n--- COPIA Y EJECUTA EL SIGUIENTE COMANDO EN psql ---")

# Generamos el comando SQL exacto que necesitas.
sql_command = f"UPDATE usuarios SET password_hash = '{nuevo_hash}' WHERE email = '{EMAIL_USUARIO}';"

print(sql_command)
print("="*70)