from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship # <-- Se añade 'relationship'
from ..core.database import Base

class PeriodoContableCerrado(Base):
    __tablename__ = "periodos_cerrados"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    cerrado_por_usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    # --- INICIO: DEFINICIÓN EXPLÍCITA DE LAS RELACIONES ---
    empresa = relationship("Empresa", back_populates="periodos_cerrados")
    usuario = relationship("Usuario", back_populates="periodos_cerrados_por_usuario")
    # --- FIN: DEFINICIÓN EXPLÍCITA ---

    __table_args__ = (UniqueConstraint('empresa_id', 'ano', 'mes', name='_empresa_ano_mes_uc'),)