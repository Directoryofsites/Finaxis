from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.schema import UniqueConstraint
from ..core.database import Base

class TipoDocumento(Base):
    __tablename__ = "tipos_documento"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    codigo = Column(String(5), nullable=False)
    nombre = Column(String(100), nullable=False)
    consecutivo_actual = Column(Integer, nullable=False, default=0)
    numeracion_manual = Column(Boolean, nullable=False, default=False)
    funcion_especial = Column(String(50), nullable=True)

    afecta_inventario = Column(Boolean, nullable=False, server_default='false')
    
    # --- INICIO CORRECCIÓN CRÍTICA: CAMPOS FUNCIONALES PARA FILTRO ---
    es_venta = Column(Boolean, nullable=False, server_default='false')
    es_compra = Column(Boolean, nullable=False, server_default='false')
    # --- FIN CORRECCIÓN CRÍTICA ---

    # --- INICIO DE LA MODIFICACIÓN ---
    # Se añade el campo para la cuenta de contado (Caja)
    cuenta_caja_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True)
    # --- FIN DE LA MODIFICACIÓN ---

    cuenta_debito_cxc_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True)
    cuenta_credito_cxc_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True)
    cuenta_debito_cxp_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True)
    cuenta_credito_cxp_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True)

    created_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    __table_args__ = (
        UniqueConstraint('empresa_id', 'codigo', name='uq_tipos_documento_empresa_codigo'),
    )