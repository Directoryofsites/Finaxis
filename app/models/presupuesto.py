from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base

class PresupuestoCabecera(Base):
    __tablename__ = "presupuesto_cabecera"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    anio = Column(Integer, nullable=False)
    estado = Column(Enum('borrador', 'revisión', 'aprobado', 'publicado', name='presupuesto_estado_enum'), default='borrador')
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    detalles = relationship("PresupuestoDetalle", back_populates="cabecera", cascade="all, delete-orphan")
    empresa = relationship("Empresa")

class PresupuestoDetalle(Base):
    __tablename__ = "presupuesto_detalle"

    id = Column(Integer, primary_key=True, index=True)
    cabecera_id = Column(Integer, ForeignKey("presupuesto_cabecera.id"), nullable=False)
    codigo_cuenta = Column(String(20), nullable=False) # Código del PUC (nivel auxiliar)
    mes = Column(Integer, nullable=False) # 1-12
    valor_automatico = Column(Numeric(18, 2), default=0)
    valor_editado = Column(Numeric(18, 2), nullable=True)
    valor_vigente = Column(Numeric(18, 2), nullable=False) # Result of COALESCE(valor_editado, valor_automatico)
    fecha_edicion = Column(DateTime, nullable=True)

    cabecera = relationship("PresupuestoCabecera", back_populates="detalles")
    bitacora = relationship("PresupuestoBitacora", back_populates="detalle", cascade="all, delete-orphan")

class PresupuestoBitacora(Base):
    __tablename__ = "presupuesto_bitacora"

    id = Column(Integer, primary_key=True, index=True)
    detalle_id = Column(Integer, ForeignKey("presupuesto_detalle.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    fecha_hora = Column(DateTime, default=datetime.utcnow)
    valor_anterior = Column(Numeric(18, 2))
    valor_nuevo = Column(Numeric(18, 2))
    motivo = Column(Text, nullable=True)

    detalle = relationship("PresupuestoDetalle", back_populates="bitacora")
    usuario = relationship("Usuario")
