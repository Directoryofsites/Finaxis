from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, DateTime, TIMESTAMP, text, Text, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base

# Estas importaciones se mantienen para las relaciones
from .empresa import Empresa
from .tipo_documento import TipoDocumento
from .tercero import Tercero
from .centro_costo import CentroCosto
from .usuario import Usuario
from .movimiento_contable import MovimientoContable, MovimientoEliminado
from .log_operacion import LogOperacion
from .aplicacion_pago import AplicacionPago

class Documento(Base):
    __tablename__ = "documentos"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    tipo_documento_id = Column(Integer, ForeignKey("tipos_documento.id"), nullable=False)
    numero = Column(Integer, nullable=False)
    fecha = Column(Date, nullable=False)
    fecha_vencimiento = Column(Date)
    beneficiario_id = Column(Integer, ForeignKey("terceros.id"))
    centro_costo_id = Column(Integer, ForeignKey("centros_costo.id"))
    unidad_ph_id = Column(Integer, ForeignKey("ph_unidades.id"), nullable=True) # Enlace Propter Rem para PH
    anulado = Column(Boolean, nullable=False, default=False)
    estado = Column(String, default='ACTIVO', nullable=False)
    observaciones = Column(Text, nullable=True)
    usuario_creador_id = Column(Integer, ForeignKey("usuarios.id"))

    # --- CORRECCIÓN: Se elimina el server_default PostgreSQL-específico ---
    fecha_operacion = Column(TIMESTAMP(timezone=True))
    
    # --- FACTURACIÓN ELECTRÓNICA ---
    dian_estado = Column(String(20), nullable=True, default=None) # PENDIENTE, ENVIADO, ACEPTADO, RECHAZADO, ERROR
    dian_cufe = Column(String(255), nullable=True)
    dian_xml_url = Column(String(500), nullable=True)
    dian_error = Column(Text, nullable=True)
    # -------------------------------
    
    # --- CONCILIACION BANCARIA: NUEVA COLUMNA ---
    reconciliation_reference = Column(String(255), nullable=True)
    # --- FIN CONCILIACION BANCARIA ---

    # --- DESCUENTOS Y RECARGOS GLOBALES ---
    descuento_global_valor = Column(Numeric(15, 2), default=0)
    cargos_globales_valor = Column(Numeric(15, 2), default=0)
    # --------------------------------------

    # Relaciones existentes
    empresa = relationship("Empresa")
    tipo_documento = relationship("TipoDocumento", back_populates="documentos")
    beneficiario = relationship("Tercero", back_populates="documentos")
    centro_costo = relationship("CentroCosto", back_populates="documentos")
    unidad_ph = relationship("app.models.propiedad_horizontal.unidad.PHUnidad")
    usuario_creador = relationship("Usuario")
    movimientos = relationship("MovimientoContable", back_populates="documento", cascade="all, delete-orphan")

    logs_operacion = relationship("LogOperacion", back_populates="documento_asociado")

    aplicaciones_recibidas = relationship(
        "AplicacionPago",
        foreign_keys="AplicacionPago.documento_factura_id",
        back_populates="documento_factura",
        cascade="all, delete-orphan"
    )

    aplicaciones_realizadas = relationship(
        "AplicacionPago",
        foreign_keys="AplicacionPago.documento_pago_id",
        back_populates="documento_pago",
        cascade="all, delete-orphan"
    )

    # --- HISTORIAL CONSUMO (CASCADA) ---
    historial_consumos = relationship(
        "app.models.consumo_registros.HistorialConsumo",
        back_populates="documento",
        cascade="all, delete-orphan"
    )


class DocumentoEliminado(Base):
    __tablename__ = 'documentos_eliminados'

    id = Column(Integer, primary_key=True, index=True)
    id_original = Column(Integer, nullable=False)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False)
    tipo_documento_id = Column(Integer, ForeignKey('tipos_documento.id'), nullable=False)
    numero = Column(String, nullable=False)
    fecha = Column(Date, nullable=False)
    fecha_vencimiento = Column(Date, nullable=True)
    beneficiario_id = Column(Integer, ForeignKey('terceros.id'), nullable=True)
    centro_costo_id = Column(Integer, ForeignKey('centros_costo.id'), nullable=True)
    usuario_creador_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    fecha_eliminacion = Column(DateTime, default=datetime.utcnow)
    usuario_eliminacion_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    log_eliminacion_id = Column(Integer, ForeignKey('log_operaciones.id'), nullable=True)

    # Relaciones
    empresa = relationship("Empresa", foreign_keys=[empresa_id])
    tipo_documento = relationship("TipoDocumento", foreign_keys=[tipo_documento_id])
    beneficiario = relationship("Tercero", back_populates="documentos_eliminados")
    centro_costo = relationship("CentroCosto", foreign_keys=[centro_costo_id])
    usuario_creador = relationship("Usuario", foreign_keys=[usuario_creador_id])
    usuario_eliminacion = relationship("Usuario", foreign_keys=[usuario_eliminacion_id])
    log_eliminacion = relationship("LogOperacion", back_populates="documentos_eliminados")
    movimientos = relationship("MovimientoEliminado", back_populates="documento_eliminado", cascade="all, delete-orphan")