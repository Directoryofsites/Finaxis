from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.models.consumo_registros import EstadoPlan, EstadoBolsa, EstadoRecarga, TipoOperacionConsumo, TipoFuenteConsumo

# --- SCHEMAS DE LECTURA ---

class PlanMensualRead(BaseModel):
    anio: int
    mes: int
    limite_asignado: int
    cantidad_disponible: int
    estado: EstadoPlan
    fecha_cierre: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class BolsaItemRead(BaseModel):
    id: int
    anio_origen: int
    mes_origen: int
    cantidad_inicial: int
    cantidad_disponible: int
    fecha_vencimiento: datetime
    estado: EstadoBolsa
    
    class Config:
        from_attributes = True

class RecargaItemRead(BaseModel):
    id: int
    cantidad_comprada: int
    cantidad_disponible: int
    fecha_compra: datetime
    valor_total: int
    facturado: bool
    estado: EstadoRecarga
    
    class Config:
        from_attributes = True

class ResumenConsumo(BaseModel):
    plan_actual: Optional[PlanMensualRead]
    bolsas_vigentes: List[BolsaItemRead]
    recargas_vigentes: List[RecargaItemRead]
    
    total_disponible: int # Suma total calculada
    
class HistorialConsumoRead(BaseModel):
    id: int
    fecha: datetime
    cantidad: int
    tipo_operacion: TipoOperacionConsumo
    fuente_tipo: TipoFuenteConsumo
    fuente_id: Optional[int]
    saldo_fuente_antes: int
    saldo_fuente_despues: int
    documento_id: Optional[int] # ID interno DB
    documento_numero: Optional[int] = None # Consecutivo Humano
    
    class Config:
        from_attributes = True

class PaqueteRecargaBase(BaseModel):
    nombre: str
    cantidad_registros: int
    precio: int
    activo: bool = True

class PaqueteRecargaCreate(PaqueteRecargaBase):
    pass

class PaqueteRecargaUpdate(PaqueteRecargaBase):
    pass

class PaqueteRecargaRead(PaqueteRecargaBase):
    id: int
    fecha_creacion: datetime
    class Config:
        from_attributes = True
