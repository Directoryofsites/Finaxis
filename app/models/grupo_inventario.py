# app/models/grupo_inventario.py (Versión con Características y Reglas de Precio)

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from ..core.database import Base

class GrupoInventario(Base):
    __tablename__ = 'grupos_inventario'
    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False)
    nombre = Column(String(100), nullable=False)

    cuenta_inventario_id = Column(Integer, ForeignKey('plan_cuentas.id'), nullable=True)
    cuenta_ingreso_id = Column(Integer, ForeignKey('plan_cuentas.id'), nullable=True)
    cuenta_costo_venta_id = Column(Integer, ForeignKey('plan_cuentas.id'), nullable=True)
    cuenta_ajuste_faltante_id = Column(Integer, ForeignKey('plan_cuentas.id'), nullable=True)
    cuenta_ajuste_sobrante_id = Column(Integer, ForeignKey('plan_cuentas.id'), nullable=True)

    # --- CAMBIO: Se elimina impuesto_predeterminado_id ---
    # impuesto_predeterminado_id = Column(Integer, ForeignKey('tasas_impuesto.id'), nullable=True)

    # Relaciones con PlanCuenta (sin cambios)
    cuenta_inventario = relationship("PlanCuenta", foreign_keys=[cuenta_inventario_id])
    cuenta_ingreso = relationship("PlanCuenta", foreign_keys=[cuenta_ingreso_id])
    cuenta_costo_venta = relationship("PlanCuenta", foreign_keys=[cuenta_costo_venta_id])
    cuenta_ajuste_faltante = relationship("PlanCuenta", foreign_keys=[cuenta_ajuste_faltante_id])
    cuenta_ajuste_sobrante = relationship("PlanCuenta", foreign_keys=[cuenta_ajuste_sobrante_id])

    # --- CAMBIO: Se elimina relación impuesto ---
    # impuesto_predeterminado = relationship("TasaImpuesto", foreign_keys=[impuesto_predeterminado_id])

    # Relación inversa con Producto (sin cambios)
    productos = relationship('Producto', back_populates='grupo_inventario')

    # --- INICIO NUEVAS RELACIONES ---
    # Relación uno-a-muchos con las definiciones de características para este grupo
    caracteristicas_definidas = relationship(
        'CaracteristicaDefinicion',
        back_populates='grupo_inventario',
        cascade="all, delete-orphan" # Si se borra el grupo, se borran sus definiciones
    )

    # Relación uno-a-muchos con las reglas de precios para este grupo
    reglas_precio = relationship(
        'ReglaPrecioGrupo',
        back_populates='grupo_inventario',
        cascade="all, delete-orphan" # Si se borra el grupo, se borran sus reglas de precio
    )
    # --- FIN NUEVAS RELACIONES ---


    __table_args__ = (
        UniqueConstraint('empresa_id', 'nombre', name='uq_grupos_inventario_empresa_nombre'),
    )