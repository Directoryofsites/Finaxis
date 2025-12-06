from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class FiltrosBalancePrueba(BaseModel):
    """ Define los filtros para la petición del Balance de Prueba. """
    fecha_inicio: date
    fecha_fin: date
    centro_costo_id: Optional[int] = None
    nivel_maximo: int
    filtro_cuentas: str # Valores esperados: 'TODAS', 'CON_MOVIMIENTO', 'CON_SALDO_O_MOVIMIENTO'

class CuentaBalancePrueba(BaseModel):
    """ Define la estructura de una fila individual en el reporte. """
    codigo: str
    nombre: str
    nivel: int
    saldo_inicial: float
    debito: float
    credito: float
    nuevo_saldo: float

class TotalesBalancePrueba(BaseModel):
    """ Define la estructura de la fila de totales. """
    saldo_inicial: float
    debito: float
    credito: float
    nuevo_saldo: float

class ReporteBalancePruebaResponse(BaseModel):
    """ Define la respuesta completa del reporte. """
    filas: List[CuentaBalancePrueba]
    totales: TotalesBalancePrueba