from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from decimal import Decimal

class RecaudoFila(BaseModel):
    referencia: str
    fecha: date
    monto: Decimal
    descripcion: Optional[str] = None
    line_number: int

class RecaudoMatch(BaseModel):
    line_number: int
    referencia: str
    fecha_pago: date
    monto_recibido: Decimal
    
    # Matching status
    is_valid: bool
    unidad_id: Optional[int] = None
    unidad_codigo: Optional[str] = None
    unidad_propietario: Optional[str] = None
    
    # Financial preview
    deuda_total: Decimal = Decimal('0.0')
    monto_a_aplicar: Decimal = Decimal('0.0')
    excedente_anticipo: Decimal = Decimal('0.0')
    pronto_pago_aplicado: bool = False
    
    # Error handling
    error_msg: Optional[str] = None

class RecaudoPreviewResult(BaseModel):
    total_filas: int
    filas_validas: int
    filas_error: int
    total_recaudado: Decimal
    detalles: List[RecaudoMatch]

class RecaudoProcessRequest(BaseModel):
    cuenta_bancaria_id: int
    fecha_consignacion: date
    # Enviamos solo los que estaban válidos en el preview o re-enviamos el batch
    filas: List[RecaudoMatch]

class RecaudoProcessResponse(BaseModel):
    exitosos: int
    fallidos: int
    errores: List[str]
    mensaje: str
