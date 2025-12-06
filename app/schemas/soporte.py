# app/schemas/soporte.py
from pydantic import BaseModel
from typing import List

# Importamos los 'ladrillos' que ya preparamos
from .empresa import EmpresaConUsuarios
from .usuario import User

class DashboardData(BaseModel):
    """
    Este es el schema principal que representa todo el paquete de datos
    necesario para renderizar el Panel de Mando de Soporte.
    """
    empresas: List[EmpresaConUsuarios]
    usuarios_soporte: List[User]

    class Config:
        from_attributes = True