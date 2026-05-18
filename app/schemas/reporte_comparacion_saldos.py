from pydantic import BaseModel
from typing import Optional, List, Dict

class FiltrosComparacionSaldos(BaseModel):
    """ Define los filtros para la petición del Reporte de Comparación Mensual de Saldos. """
    anio: int
    cuenta_codigo: Optional[str] = None
    nivel_maximo: Optional[int] = 9
    tipo_filtro: Optional[str] = "TODAS"  # 'TODAS', 'BALANCE' (1, 2, 3), 'RESULTADOS' (4, 5, 6, 7)
    mes_inicio: Optional[int] = 1
    mes_fin: Optional[int] = 12

class FilaComparacionSaldos(BaseModel):
    """ Estructura de una fila individual en el reporte de comparación de saldos. """
    codigo: str
    nombre: str
    nivel: int
    saldo_inicial: float
    # Mapeo de mes (por número 1-12) al saldo acumulado al fin de ese mes
    saldos_mensuales: Dict[int, float]

class ReporteComparacionSaldosResponse(BaseModel):
    """ Respuesta completa de datos para el reporte de comparación de saldos. """
    filas: List[FilaComparacionSaldos]
    meses: List[int]  # Lista de meses incluidos (ej. [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
