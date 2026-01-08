from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, ForeignKey, Index, Enum, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

# Enums para estados y tipos
class EstadoPlan(str, enum.Enum):
    ABIERTO = "ABIERTO"
    CERRADO = "CERRADO"

class EstadoBolsa(str, enum.Enum):
    VIGENTE = "VIGENTE"
    AGOTADO = "AGOTADO"
    VENCIDO = "VENCIDO"

class EstadoRecarga(str, enum.Enum):
    VIGENTE = "VIGENTE"
    AGOTADA = "AGOTADA"
    EXPIRADA = "EXPIRADA"

class TipoFuenteConsumo(str, enum.Enum):
    PLAN = "PLAN"
    BOLSA = "BOLSA"
    RECARGA = "RECARGA"

class TipoOperacionConsumo(str, enum.Enum):
    CONSUMO = "CONSUMO"
    REVERSION = "REVERSION"
    CIERRE = "CIERRE"
    EXPIRACION = "EXPIRACION"

class ControlPlanMensual(Base):
    __tablename__ = "control_plan_mensual"

    empresa_id = Column(Integer, ForeignKey("empresas.id"), primary_key=True)
    anio = Column(Integer, primary_key=True)
    mes = Column(Integer, primary_key=True)
    
    limite_asignado = Column(Integer, nullable=False, default=0)
    cantidad_disponible = Column(Integer, nullable=False, default=0)
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_cierre = Column(DateTime, nullable=True)
    
    estado = Column(String, default=EstadoPlan.ABIERTO.value)  # Usamos String para compatibilidad fácil, validado por lógica

    # Relaciones
    empresa = relationship("Empresa")

class BolsaExcedente(Base):
    __tablename__ = "bolsa_excedente"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    
    anio_origen = Column(Integer, nullable=False)
    mes_origen = Column(Integer, nullable=False)
    
    cantidad_inicial = Column(Integer, nullable=False)
    cantidad_disponible = Column(Integer, nullable=False)
    
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_vencimiento = Column(DateTime, nullable=False)
    
    estado = Column(String, default=EstadoBolsa.VIGENTE.value)

    empresa = relationship("Empresa")

    __table_args__ = (
        Index("idx_bolsa_fifo", "empresa_id", "fecha_vencimiento", "estado"),
    )

class RecargaAdicional(Base):
    __tablename__ = "recarga_adicional"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    
    anio = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    
    cantidad_comprada = Column(Integer, nullable=False)
    cantidad_disponible = Column(Integer, nullable=False)
    
    fecha_compra = Column(DateTime, default=datetime.utcnow)
    
    estado = Column(String, default=EstadoRecarga.VIGENTE.value)
    
    # Campos para Facturación (Nuevo Requerimiento)
    valor_total = Column(Integer, nullable=False, default=0) # Costo histórico de la compra
    facturado = Column(Boolean, default=False) # Si ya se cobró en factura periódica
    fecha_facturacion = Column(DateTime, nullable=True) # Cuándo se cobró

    empresa = relationship("Empresa")

class PaqueteRecarga(Base):
    __tablename__ = "paquetes_recarga"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False) # Ej: "Paquete Inicio", "Paquete Pro"
    cantidad_registros = Column(Integer, nullable=False) 
    precio = Column(Integer, nullable=False)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

class HistorialConsumo(Base):
    __tablename__ = "historial_consumo"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False)
    cantidad = Column(Integer, nullable=False) # Positivo para consumo, Negativo para reversión (o usar tipo_operacion)
    
    tipo_operacion = Column(String, nullable=False) # CONSUMO, REVERSION, etc.
    
    fuente_tipo = Column(String, nullable=False) # PLAN, BOLSA, RECARGA
    fuente_id = Column(Integer, nullable=True) # ID de la Bolsa o Recarga. Null si es Plan.
    
    # Snapshot de auditoría
    saldo_fuente_antes = Column(Integer, nullable=False)
    saldo_fuente_despues = Column(Integer, nullable=False)
    
    documento_id = Column(Integer, ForeignKey("documentos.id"), nullable=True)
    
    empresa = relationship("Empresa")
    documento = relationship("Documento")
