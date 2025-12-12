
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.usuario_favorito import UsuarioFavorito

def list_favorite_routes():
    db = SessionLocal()
    favoritos = db.query(UsuarioFavorito).all()
    print("--- RUTAS ACTUALES EN FAVORITOS ---")
    for f in favoritos:
        print(f"'{f.ruta_enlace}'")
    db.close()

if __name__ == "__main__":
    list_favorite_routes()
