from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class PagoConsolidadoCreate(BaseModel):
    propietario_id: int
    fecha: date
    monto_total: float
    observaciones: Optional[str] = None
    forma_pago_id: Optional[int] = None

class PagoConsolidadoResponse(BaseModel):
    message: str
    total_recibos: int
    monto_total: float
    detalle_pagos: List[dict]

class CarteraItem(BaseModel):
    unidad_id: int
    unidad_codigo: str
    propietario_nombre: str
    saldo_corriente: float = 0
    edad_0_30: float = 0
    edad_31_60: float = 0
    edad_61_90: float = 0
    edad_mas_90: float = 0
    saldo_total: float = 0

class CarteraEdadesResponse(BaseModel):
    items: List[CarteraItem]
    total_corriente: float = 0
    total_0_30: float = 0
    total_31_60: float = 0
    total_61_90: float = 0
    total_mas_90: float = 0
    total_general: float = 0

class ReporteSaldoItem(BaseModel):
    unidad_id: int
    unidad_codigo: str
    propietario_nombre: str
    torre_nombre: str
    saldo: float
    detalle: str
    antiguedad_promedio: float = 0
    conceptos_count: int = 0

class ReporteSaldoResponse(BaseModel):
    items: List[ReporteSaldoItem]
    total_general: float
    fecha_corte: Optional[str] = None
