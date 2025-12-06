# app/schemas/rol.py
from pydantic import BaseModel

class Rol(BaseModel):
    id: int
    nombre: str

    class Config:
        from_attributes = True