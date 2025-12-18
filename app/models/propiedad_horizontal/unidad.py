from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, Date, DateTime, Text, Float, func
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class PHTorre(Base):
    """
    Representa una Torre, Bloque, Manzana o Zona dentro de la Copropiedad.
    Ej: Torre A, Bloque 1, Zona Comercial.
    """
    __tablename__ = "ph_torres"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    nombre = Column(String(50), nullable=False) # Ej: "Torre A"
    descripcion = Column(String(200), nullable=True)

    # Relaciones
    unidades = relationship("PHUnidad", back_populates="torre")
    empresa = relationship("Empresa")

class PHUnidad(Base):
    """
    Representa una unidad privada (Apartamento, Casa, Local, Parqueadero, Depósito).
    Base fundamental para la liquidación de coeficientes.
    """
    __tablename__ = "ph_unidades"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    torre_id = Column(Integer, ForeignKey("ph_torres.id"), nullable=True)
    
    codigo = Column(String(50), nullable=False) # Ej: "501", "204", "LC-01"
    tipo = Column(String(50), nullable=False, default="RESIDENCIAL") # RESIDENCIAL, COMERCIAL, PARQUEADERO, DEPOSITO
    
    matricula_inmobiliaria = Column(String(100), nullable=True)
    area_privada = Column(Numeric(10, 2), nullable=True, default=0) # Metros cuadrados
    
    # Coeficiente de Copropiedad (CRÍTICO para Ley 675)
    # Se usa Numeric con alta precisión (ej: 0.023450)
    coeficiente = Column(Numeric(10, 6), nullable=False, default=0)
    
    # Relaciones con Terceros (Propietarios y Residentes)
    propietario_principal_id = Column(Integer, ForeignKey("terceros.id"), nullable=True)
    residente_actual_id = Column(Integer, ForeignKey("terceros.id"), nullable=True)
    
    activo = Column(Boolean, default=True)
    observaciones = Column(Text, nullable=True)
    
    # Relaciones
    empresa = relationship("Empresa")
    torre = relationship("PHTorre", back_populates="unidades")
    
    propietario_principal = relationship("Tercero", foreign_keys=[propietario_principal_id])
    residente_actual = relationship("Tercero", foreign_keys=[residente_actual_id])

    vehiculos = relationship("PHVehiculo", back_populates="unidad", cascade="all, delete-orphan")
    mascotas = relationship("PHMascota", back_populates="unidad", cascade="all, delete-orphan")
    historial_coeficientes = relationship("PHCoeficienteHistorial", back_populates="unidad", cascade="all, delete-orphan")

    # Módulos de Contribución (PH Mixta)
    modulos_contribucion = relationship(
        "app.models.propiedad_horizontal.modulo_contribucion.PHModuloContribucion",
        secondary="ph_unidad_modulo_association",
        back_populates="unidades"
    )

    @property
    def propietario_nombre(self):
        return self.propietario_principal.razon_social if self.propietario_principal else None

    @property
    def torre_nombre(self):
        return self.torre.nombre if self.torre else None

class PHVehiculo(Base):
    __tablename__ = "ph_vehiculos"
    
    id = Column(Integer, primary_key=True, index=True)
    unidad_id = Column(Integer, ForeignKey("ph_unidades.id"), nullable=False)
    placa = Column(String(20), nullable=False)
    tipo = Column(String(30), nullable=True) # Carro, Moto, Bicicleta
    marca = Column(String(50), nullable=True)
    color = Column(String(30), nullable=True)
    propietario_nombre = Column(String(100), nullable=True) # Texto libre o link a tercero si se quisiera
    
    unidad = relationship("PHUnidad", back_populates="vehiculos")

class PHMascota(Base):
    __tablename__ = "ph_mascotas"
    
    id = Column(Integer, primary_key=True, index=True)
    unidad_id = Column(Integer, ForeignKey("ph_unidades.id"), nullable=False)
    nombre = Column(String(50), nullable=False)
    especie = Column(String(30), nullable=False) # Perro, Gato
    raza = Column(String(50), nullable=True)
    vacunas_al_dia = Column(Boolean, default=False)
    
    unidad = relationship("PHUnidad", back_populates="mascotas")


class PHCoeficienteHistorial(Base):
    __tablename__ = "ph_coeficientes_historial"
    
    id = Column(Integer, primary_key=True, index=True)
    unidad_id = Column(Integer, ForeignKey("ph_unidades.id"), nullable=False)
    valor_anterior = Column(Float, nullable=False)
    valor_nuevo = Column(Float, nullable=False)
    fecha_cambio = Column(DateTime, server_default=func.now())
    motivo = Column(String(255), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True) # Quien hizo el cambio
    
    unidad = relationship("PHUnidad", back_populates="historial_coeficientes")
    usuario = relationship("app.models.usuario.Usuario")
