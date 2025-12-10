from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean, Enum, Numeric, Text
from sqlalchemy.orm import relationship
import enum
from datetime import date
from app.core.database import Base

# ==========================================================
# ENUMS
# ==========================================================

class TipoContrato(str, enum.Enum):
    INDEFINIDO = "Indefinido"
    FIJO = "Término Fijo"
    OBRA_LABOR = "Obra o Labor"
    APRENDIZ = "Aprendizaje"
    PRESTACION_SERVICIOS = "Prestación de Servicios" # Aunque este tecnicamente no es nómina, se usa para cuentas de cobro recurrentes

class PeriodoPago(str, enum.Enum):
    MENSUAL = "Mensual"
    QUINCENAL = "Quincenal"

class EstadoNomina(str, enum.Enum):
    BORRADOR = "Borrador"
    APROBADA = "Aprobada"
    PAGADA = "Pagada"
    ANULADA = "Anulada"

class EstadoEmpleado(str, enum.Enum):
    ACTIVO = "Activo"
    INACTIVO = "Inactivo"
    LICENCIA = "Licencia"

# ==========================================================
# MODELOS
# ==========================================================

class Empleado(Base):
    __tablename__ = "nomina_empleados"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"))
    
    # Información Personal
    tipo_documento = Column(String(5), default="CC")
    numero_documento = Column(String(20), index=True)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True)
    telefono = Column(String(20), nullable=True)
    direccion = Column(String(200), nullable=True)
    
    # Información Contractual
    fecha_ingreso = Column(Date, nullable=False)
    fecha_retiro = Column(Date, nullable=True)
    tipo_contrato = Column(Enum(TipoContrato), default=TipoContrato.INDEFINIDO)
    cargo = Column(String(100), nullable=True)
    
    # Información Salarial
    salario_base = Column(Numeric(18, 2), default=0)
    auxilio_transporte = Column(Boolean, default=True) # Si false, no se calcula
    riesgo_arl = Column(Integer, default=1) # Nivel de Riesgo (1-5)
    
    # Configuración Pago
    banco = Column(String(50), nullable=True)
    numero_cuenta = Column(String(50), nullable=True)
    
    estado = Column(Enum(EstadoEmpleado), default=EstadoEmpleado.ACTIVO)

    # Relaciones
    detalles_nomina = relationship("DetalleNomina", back_populates="empleado")
    tercero_id = Column(Integer, ForeignKey("terceros.id"), nullable=True)
    tercero = relationship("Tercero", backref="empleado_nomina")


class ConfiguracionNomina(Base):
    __tablename__ = "nomina_configuracion"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), unique=True)
    
    # Configuración General
    tipo_documento_id = Column(Integer, ForeignKey("tipos_documento.id"), nullable=True)

    # CUENTAS PUC (IDs de PlanCuenta)
    # Devengados
    cuenta_sueldo_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True) # 510506
    cuenta_auxilio_transporte_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True) # 510527
    cuenta_horas_extras_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True) # 510555
    cuenta_comisiones_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True) # 510518
    
    # Pasivos (Por Pagar) / Deducciones
    cuenta_salarios_por_pagar_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True) # 250501
    cuenta_aporte_salud_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True) # 237005 (Total)
    cuenta_aporte_pension_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True) # 238030 (Total)
    cuenta_fondo_solidaridad_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True) # 238030 o similar
    cuenta_retencion_fuente_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True) # 236505
    
    # Provisiones (Gastos vs Pasivos Estimados) - Futuro
    # cuenta_gasto_cesantias_id...



class Nomina(Base):
    __tablename__ = "nomina_documentos"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"))
    
    # Periodo
    anio = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    periodo_pago = Column(Enum(PeriodoPago), default=PeriodoPago.MENSUAL) 
    quincena = Column(Integer, default=0) # 1, 2 o 0 (Mensual)
    
    fecha_liquidacion = Column(Date, default=date.today)
    fecha_inicio_periodo = Column(Date, nullable=False)
    fecha_fin_periodo = Column(Date, nullable=False)
    
    # Totales
    total_devengado = Column(Numeric(18, 2), default=0)
    total_deducciones = Column(Numeric(18, 2), default=0)
    total_neto = Column(Numeric(18, 2), default=0)
    
    estado = Column(Enum(EstadoNomina), default=EstadoNomina.BORRADOR)
    observaciones = Column(Text, nullable=True)

    # Relaciones
    detalles = relationship("DetalleNomina", back_populates="nomina", cascade="all, delete-orphan")
    empresa = relationship("app.models.empresa.Empresa") # Late import string to avoid circulars


class DetalleNomina(Base):
    """
    Representa el 'Desprendible' de un empleado en una nómina específica.
    """
    __tablename__ = "nomina_detalles"

    id = Column(Integer, primary_key=True, index=True)
    nomina_id = Column(Integer, ForeignKey("nomina_documentos.id"))
    empleado_id = Column(Integer, ForeignKey("nomina_empleados.id"))
    
    dias_trabajados = Column(Integer, default=30)
    dias_incapacidad = Column(Integer, default=0)
    dias_licencia = Column(Integer, default=0)
    
    # DEVENGADOS
    sueldo_basico_periodo = Column(Numeric(18, 2), default=0) # Proporcional a días
    auxilio_transporte_periodo = Column(Numeric(18, 2), default=0)
    horas_extras_total = Column(Numeric(18, 2), default=0)
    recargos_total = Column(Numeric(18, 2), default=0)
    comisiones = Column(Numeric(18, 2), default=0)
    otros_devengados = Column(Numeric(18, 2), default=0) # Bonos no salariales, etc.
    total_devengado = Column(Numeric(18, 2), default=0)
    
    # DEDUCCIONES
    salud_empleado = Column(Numeric(18, 2), default=0) # 4%
    pension_empleado = Column(Numeric(18, 2), default=0) # 4%
    fondo_solidaridad = Column(Numeric(18, 2), default=0)
    retencion_fuente = Column(Numeric(18, 2), default=0)
    prestamos = Column(Numeric(18, 2), default=0)
    otras_deducciones = Column(Numeric(18, 2), default=0)
    total_deducciones = Column(Numeric(18, 2), default=0)
    
    # NETO
    neto_pagar = Column(Numeric(18, 2), default=0)

    # Relaciones
    nomina = relationship("Nomina", back_populates="detalles")
    empleado = relationship("Empleado", back_populates="detalles_nomina")

