
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from ..core.database import Base

class ConfiguracionFE(Base):
    __tablename__ = "configuracion_fe"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, unique=True)
    
    # Proveedor Tecnológico (Factus, Dataico, etc)
    proveedor = Column(String(50), nullable=False, default='FACTUS')
    ambiente = Column(String(20), nullable=False, default='PRUEBAS') # PRUEBAS, PRODUCCION
    
    # Credenciales API
    api_token = Column(Text, nullable=True)
    api_url = Column(String(255), nullable=True)
    email_registro = Column(String(255), nullable=True)
    
    # Numeración DIAN (Ventas)
    prefijo = Column(String(10), nullable=True)
    resolucion_numero = Column(String(50), nullable=True)
    resolucion_fecha = Column(Date, nullable=True)
    rango_desde = Column(Integer, nullable=True)
    rango_hasta = Column(Integer, nullable=True)

    # Numeración DIAN (Documento Soporte)
    ds_prefijo = Column(String(10), nullable=True)
    ds_resolucion_numero = Column(String(50), nullable=True)
    ds_rango_id = Column(Integer, nullable=True)
    
    # Numeración Notas (Factus Range IDs)
    nc_rango_id = Column(Integer, nullable=True)
    nd_rango_id = Column(Integer, nullable=True)
    
    # Estado (Habilitado para Facturar)
    habilitado = Column(Boolean, default=False)
    
    # Relación
    empresa = relationship("Empresa", backref="configuracion_fe")
