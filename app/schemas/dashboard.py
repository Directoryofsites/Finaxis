# app/schemas/dashboard.py (REEMPLAZO COMPLETO - RENOMBRADO ROTACIÓN -> MARGEN BRUTO)

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date

class FinancialRatiosResponse(BaseModel):
    """
    Schema para los KPIs, las 9 Razones Financieras y el Diagnóstico Estratégico (SEEE) del Dashboard.
    """
    fecha_corte: date = Field(..., description="Fecha hasta la cual se calcularon los datos de Balance.")
    
    # --- PYG (Estado de Resultados Anual Fijo) ---
    ingresos_anuales: float = Field(..., description="Total de ingresos (Clase 4).")
    costo_ventas_total: float = Field(..., description="Total de costo de ventas (Clase 61).")
    utilidad_neta: float = Field(..., description="Utilidad Neta.")
    
    # --- Balance General (Saldos para Cálculo) ---
    activos_total: float = Field(..., description="Total Activos (Clase 1).")
    pasivos_total: float = Field(..., description="Total Pasivos (Clase 2).")
    patrimonio_total: float = Field(..., description="Total Patrimonio (Clase 3).")
    
    # --- Detalle Contable Requerido para Ratios ---
    activo_corriente: float = Field(..., description="Clase 11 a 14.")
    pasivo_corriente: float = Field(..., description="Clase 21 a 23.")
    inventarios_total: float = Field(..., description="Clase 14.") # Necesario para Prueba Ácida
    
    # --- 9 RAZONES FINANCIERAS (Los indicadores del Tablero) ---
    razon_corriente: float = Field(..., description="Activo Corriente / Pasivo Corriente.")
    prueba_acida: float = Field(..., description="(Activo Corriente - Inventarios) / Pasivo Corriente.")
    apalancamiento_financiero: float = Field(..., description="Pasivo Total / Patrimonio.")
    nivel_endeudamiento: float = Field(..., description="Pasivo Total / Activo Total.")
    margen_neto_utilidad: float = Field(..., description="(Utilidad Neta / Ingresos Operacionales) * 100.")
    rentabilidad_patrimonio: float = Field(..., description="(Utilidad Neta / Patrimonio) * 100.")
    rentabilidad_activo: float = Field(..., description="(Utilidad Neta / Activo Total) * 100.")
    margen_bruto_utilidad: float = Field(..., description="(Ingresos - Costo de Ventas Ampliado) / Ingresos * 100.") # CAMBIO CLAVE
    
    # --- DIAGNÓSTICO ESTRATÉGICO SEEE (NUEVOS CAMPOS) ---
    escenario_general: int = Field(..., description="Clasificación del estado financiero de la empresa (1: Óptimo a 5: Crítico).")
    texto_interpretativo: str = Field(..., description="Análisis narrativo integral del escenario y las referencias cruzadas.")
    recomendaciones_breves: List[str] = Field(..., description="Lista de recomendaciones automáticas cortas.")
    
    model_config = ConfigDict(from_attributes=True)


# --- NUEVOS SCHEMAS PARA ANÁLISIS FINANCIERO (HORIZONTAL / VERTICAL) ---

class AnalysisRow(BaseModel):
    """Fila genérica para tablas de análisis."""
    codigo_cuenta: str
    nombre_cuenta: str
    
    # Valores
    saldo_periodo_1: float = 0.0
    saldo_periodo_2: Optional[float] = 0.0 # Para Horizontal o Comparativo
    
    # Cálculos Horizontal
    variacion_absoluta: Optional[float] = 0.0 # P2 - P1
    variacion_relativa: Optional[float] = 0.0 # (P2 - P1) / P1 * 100
    
    # Cálculos Vertical
    porcentaje_participacion: Optional[float] = 0.0 # Saldo / Total Grupo * 100
    
    es_titulo: bool = False # Para indicar si es un encabezado de grupo (ej. ACTIVO)
    nivel: int = 1 # Para indentación en frontend

class HorizontalAnalysisRequest(BaseModel):
    fecha_inicio_1: date
    fecha_fin_1: date
    fecha_inicio_2: date
    fecha_fin_2: date

class VerticalAnalysisRequest(BaseModel):
    fecha_inicio: date
    fecha_fin: date

class HorizontalResponse(BaseModel):
    items: List[AnalysisRow]
    periodo_1_texto: str
    periodo_2_texto: str

class VerticalResponse(BaseModel):
    items: List[AnalysisRow]
    periodo_texto: str
