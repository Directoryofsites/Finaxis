# reset_password.py
from app.core.hashing import get_password_hash

# IMPORTANTE: Coloca aquí la nueva contraseña que quieres establecer.
NUEVA_CONTRASENA = "SoporteClave2025*"

# El email del usuario de soporte que vamos a actualizar.
EMAIL_USUARIO = "soporte_final@contapy.com"

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