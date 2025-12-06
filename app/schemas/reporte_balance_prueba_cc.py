# app/schemas/reporte_balance_prueba_cc.py

from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class FiltrosBalancePruebaCC(BaseModel):
    """ Define los filtros para la petición del Balance de Prueba por Centro de Costo. """
    fecha_inicio: date
    fecha_fin: date
    nivel_maximo: int
    filtro_centros_costo: str # Valores: 'TODOS', 'CON_MOVIMIENTO', 'CON_SALDO_O_MOVIMIENTO'
    
    # --- INICIO: NUEVO FILTRO OPCIONAL ---
    cuenta_id: Optional[int] = None # Para filtrar por una cuenta contable específica
    # --- FIN: NUEVO FILTRO OPCIONAL ---


class CentroCostoBalancePrueba(BaseModel):
    """ Define la estructura de una fila individual en el reporte (gemelo de Cuenta). """
    codigo: str
    nombre: str
    nivel: int
    saldo_inicial: float
    debito: float
    credito: float
    nuevo_saldo: float

class TotalesBalancePruebaCC(BaseModel):
    """ Define la estructura de la fila de totales (gemelo de Totales). """
    saldo_inicial: float
    debito: float
    credito: float
    nuevo_saldo: float

class ReporteBalancePruebaCCResponse(BaseModel):
    """ Define la respuesta completa del reporte (gemelo de Response). """
    filas: List[CentroCostoBalancePrueba]
    totales: TotalesBalancePruebaCC