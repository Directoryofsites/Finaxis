from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import date

class VendedorDesempeñoUnid(BaseModel):
    vendedor_id: Optional[int]
    vendedor_nombre: str
    total_ventas_brutas: Decimal
    total_descuentos: Decimal
    total_iva: Decimal
    total_neto: Decimal
    costo_total: Decimal
    utilidad_bruta: Decimal
    margen_porcentaje: Decimal
    cantidad_facturas: int

class ReporteDesempeñoVendedoresResponse(BaseModel):
    fecha_inicio: date
    fecha_fin: date
    ranking: List[VendedorDesempeñoUnid]
    totales_globales: dict
