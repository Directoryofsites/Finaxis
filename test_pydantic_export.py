from pydantic import BaseModel
from typing import Optional

class ExportPaquetes(BaseModel):
    plan_cuentas: bool = False
    terceros: bool = False
    centros_costos: bool = False
    tipos_documentos: bool = False
    productos_servicios: bool = False
    bodegas: bool = False
    transacciones_contabilidad: bool = False
    transacciones_inventario: bool = False
    transacciones: bool = False

class ExportRequest(BaseModel):
    paquetes: ExportPaquetes
    tipoDocId: Optional[int] = None
    cuentaId: Optional[int] = None
    montoMinimo: Optional[float] = None

req = ExportRequest(
    paquetes=ExportPaquetes(transacciones_contabilidad=True),
    cuentaId=51159501
)

print(req.dict(exclude_none=True))
