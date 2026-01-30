from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..core.database import Base

class EstadoEscenario(str, enum.Enum):
    BORRADOR = "BORRADOR"
    APROBADO = "APROBADO"
    CERRADO = "CERRADO"

class TipoSector(str, enum.Enum):
    PRIVADO = "PRIVADO"
    PUBLICO = "PUBLICO"

class MetodoProyeccion(str, enum.Enum):
    MANUAL = "MANUAL"
    PROMEDIO_HISTORICO = "PROMEDIO_HISTORICO"
    EJECUCION_ANTERIOR = "EJECUCION_ANTERIOR"
    VALOR_FIJO = "VALOR_FIJO"
    INCREMENTO_PORCENTUAL = "INCREMENTO_PORCENTUAL"

class EscenarioPresupuestal(Base):
    __tablename__ = "presupuesto_escenarios"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    
    nombre = Column(String(100), nullable=False) # Ej: "Presupuesto 2026 Optimista"
    anio = Column(Integer, nullable=False)
    
    estado = Column(Enum(EstadoEscenario), default=EstadoEscenario.BORRADOR)
    tipo_sector = Column(Enum(TipoSector), default=TipoSector.PRIVADO)
    
    # Variables globales para este escenario (IPC, SMLV, etc)
    # Ejemplo: {"IPC": 5.0, "SMLV": 10.0}
    variables_globales = Column(JSON, nullable=True, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    # Relaciones
    empresa = relationship("Empresa")
    items = relationship("PresupuestoItem", back_populates="escenario", cascade="all, delete-orphan")

class PresupuestoItem(Base):
    """
    Detalle del presupuesto por cuenta contable o rubro.
    Reemplaza/Evoluciona a PHPresupuesto.
    """
    __tablename__ = "presupuesto_items"

    id = Column(Integer, primary_key=True, index=True)
    escenario_id = Column(Integer, ForeignKey("presupuesto_escenarios.id"), nullable=False)
    cuenta_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=False)
    
    # Datos de Proyección / Origen
    metodo_proyeccion = Column(Enum(MetodoProyeccion), default=MetodoProyeccion.MANUAL)
    base_calculo = Column(String(50), nullable=True) # Ej: "2025_REAL", "2025_PRESUPUESTO"
    factor_ajuste = Column(Float, default=0) # Ej: 5.0 para 5%
    variable_aplicada = Column(String(20), nullable=True) # Ej: "IPC"

    # Valores Mensuales Proyectados
    mes_01 = Column(Float, default=0)
    mes_02 = Column(Float, default=0)
    mes_03 = Column(Float, default=0)
    mes_04 = Column(Float, default=0)
    mes_05 = Column(Float, default=0)
    mes_06 = Column(Float, default=0)
    mes_07 = Column(Float, default=0)
    mes_08 = Column(Float, default=0)
    mes_09 = Column(Float, default=0)
    mes_10 = Column(Float, default=0)
    mes_11 = Column(Float, default=0)
    mes_12 = Column(Float, default=0)
    
    valor_total = Column(Float, default=0)
    
    # Notas u observaciones por linea
    observacion = Column(String(255), nullable=True)

    # Relaciones
    escenario = relationship("EscenarioPresupuestal", back_populates="items")
    cuenta = relationship("PlanCuenta")

    __table_args__ = (
        UniqueConstraint('escenario_id', 'cuenta_id', name='uq_presupuesto_item_escenario_cuenta'),
    )
