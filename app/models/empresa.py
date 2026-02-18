from sqlalchemy import Column, Integer, String, TIMESTAMP, text, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref
from ..core.database import Base

class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True)
    razon_social = Column(String(255), nullable=False)
    nit = Column(String(20), unique=True, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    fecha_inicio_operaciones = Column(Date, nullable=True)
    limite_registros = Column(Integer, nullable=True, default=None)
    precio_por_registro = Column(Integer, nullable=True, default=None) # Precio personalizado por registro (NULL = Usa Global)
    modo_operacion = Column(String(50), nullable=False, default='STANDARD') # STANDARD, AUDITORIA_READONLY

    # --- AGREGAR ESTAS LÍNEAS ---
    direccion = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    email = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)
    
    # Configuración Contable
    prefijo_cxc = Column(String(10), nullable=False, default='13')
    prefijo_cxp = Column(String(10), nullable=False, default='2')
    
    # --- FACTURACIÓN ELECTRÓNICA (DIAN / UBL 2.1) ---
    dv = Column(String(1), nullable=True, comment="Dígito de Verificación")
    tipo_documento = Column(String(5), nullable=True, default='31', comment="31=NIT, 13=Cedula")
    tipo_persona = Column(String(1), nullable=True, default='1', comment="1=Juridica, 2=Natural")
    regimen_fiscal = Column(String(5), nullable=True, default='48', comment="48=IVA, 49=No IVA")
    responsabilidad_fiscal = Column(String(20), nullable=True, default='R-99-PN', comment="Codigo Resp. Fiscal")
    municipio_dane = Column(String(10), nullable=True, comment="Codigo DANE Municipio")
    codigo_postal = Column(String(10), nullable=True)
    # ------------------------------------------------


    periodos_cerrados = relationship("PeriodoContableCerrado", back_populates="empresa")

    # --- INICIO: RELACIÓN FALTANTE AÑADIDA ---
    # Esta línea completa la relación con el modelo Usuario, resolviendo el error.
    # Specify foreign_keys to resolve ambiguity with owner_id
    usuarios = relationship("Usuario", back_populates="empresa", foreign_keys="[Usuario.empresa_id]")
    
    # Configuración de Correo (One-to-One)
    config_email = relationship("EmpresaConfigEmail", back_populates="empresa", uselist=False, cascade="all, delete-orphan")
    
    # Esto completa la relación con el modelo CupoAdicional
    # This completes the relationship with the CupoAdicional model
    cupos_adicionales = relationship("CupoAdicional", back_populates="empresa", cascade="all, delete-orphan")

    # --- CAMPOS MULTI-TENANCY Y CONTADOR ---
    # Jerarquía (Holding/Contador)
    padre_id = Column(Integer, ForeignKey('empresas.id'), nullable=True)
    hijas = relationship("Empresa", 
                        backref=backref('padre', remote_side=[id]),
                        foreign_keys=[padre_id])

    # Control de Cupos (Administrativo)
    limite_registros_mensual = Column(Integer, nullable=True, default=1000)

    # Plantillas (Standardization)
    is_template = Column(Boolean, default=False)
    template_category = Column(String(50), nullable=True) # 'RETAIL', 'SERVICIOS', 'PH'

    # --- MODO EXPRESS / LITE (FACTURACIÓN POR PAQUETES) ---
    is_lite_mode = Column(Boolean, default=False, nullable=False)
    saldo_facturas_venta = Column(Integer, default=0, nullable=False)
    saldo_documentos_soporte = Column(Integer, default=0, nullable=False)
    saldo_notas_credito = Column(Integer, default=0, nullable=False)
    fecha_vencimiento_plan = Column(Date, nullable=True)
    # ------------------------------------------------------

    # Propiedad y Desacople
    owner_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    owner = relationship("Usuario", foreign_keys=[owner_id], backref="empresas_propiedad")

    # --- RELACIONES DE CASCADA PARA DEBORRADO LIMPIO ---
    configuraciones_reportes = relationship("app.models.configuracion_reporte.ConfiguracionReporte", back_populates="empresa", cascade="all, delete-orphan")
    ph_configuracion = relationship("app.models.propiedad_horizontal.configuracion.PHConfiguracion", back_populates="empresa", uselist=False, cascade="all, delete-orphan")
    ph_conceptos = relationship("app.models.propiedad_horizontal.concepto.PHConcepto", back_populates="empresa", cascade="all, delete-orphan")
    
    # --- PH ESTRUCTURA (CASCADA) ---
    ph_torres = relationship("app.models.propiedad_horizontal.unidad.PHTorre", backref="empresa_ph_torre", cascade="all, delete-orphan")
    ph_unidades = relationship("app.models.propiedad_horizontal.unidad.PHUnidad", backref="empresa_ph_unidad", cascade="all, delete-orphan")

    
    # Corregido: Backrefs únicos para evitar colisiones
    configuracion_nomina = relationship("app.models.nomina.ConfiguracionNomina", backref="empresa_conf_nomina", cascade="all, delete-orphan")
    # tipos_nomina (MOVIDO AL FINAL)
    empleados = relationship("app.models.nomina.Empleado", backref="empresa_empleado", cascade="all, delete-orphan")
    nominas_documentos = relationship("app.models.nomina.Nomina", backref="empresa_nomina_doc", cascade="all, delete-orphan")

    # Inventario & Activos
    grupos_inventario = relationship("app.models.grupo_inventario.GrupoInventario", backref="empresa_grupo_inv", cascade="all, delete-orphan")
    activos_categorias = relationship("app.models.activo_categoria.ActivoCategoria", backref="empresa_activo_cat", cascade="all, delete-orphan")
    activos_fijos = relationship("app.models.activo_fijo.ActivoFijo", backref="empresa_activo_fijo", cascade="all, delete-orphan")
    
    # Produccion
    configuracion_produccion = relationship("app.models.configuracion_produccion.ConfiguracionProduccion", backref="empresa_conf_prod", uselist=False, cascade="all, delete-orphan")

    # --- RELACIONES OPERATIVAS (CASCADA) ---
    # plan_cuentas (MOVIDO AL FINAL)
    documentos = relationship("app.models.documento.Documento", back_populates="empresa", cascade="all, delete-orphan")
    documentos_eliminados = relationship("app.models.documento.DocumentoEliminado", backref="empresa_doc_elim", cascade="all, delete-orphan")
    terceros = relationship("app.models.tercero.Tercero", backref="empresa_tercero", cascade="all, delete-orphan")
    
    # Produccion Operativa
    ordenes_produccion = relationship("app.models.produccion.OrdenProduccion", backref="empresa_orden_prod", cascade="all, delete-orphan")
    recetas = relationship("app.models.produccion.Receta", backref="empresa_receta", cascade="all, delete-orphan")

    # --- CONFIGURACION CONTABLE (CASCADA) ---
    tasas_impuesto = relationship("app.models.impuesto.TasaImpuesto", backref="empresa_tasa_imp", cascade="all, delete-orphan")
    tipos_documento = relationship("app.models.tipo_documento.TipoDocumento", backref="empresa_tipo_doc", cascade="all, delete-orphan")
    # centros_costo (MOVIDO AL FINAL)
    bodegas = relationship("app.models.bodega.Bodega", backref="empresa_bodega", cascade="all, delete-orphan")
    productos = relationship("app.models.producto.Producto", backref="empresa_producto", cascade="all, delete-orphan")
    formatos_impresion = relationship("app.models.formato_impresion.FormatoImpresion", backref="empresa_fmt_impr", cascade="all, delete-orphan")
    plantillas_maestras = relationship("app.models.plantilla_maestra.PlantillaMaestra", backref="empresa_plantilla_maestra", cascade="all, delete-orphan")

    # --- CONSUMO Y CUPO (CASCADA) ---
    historial_consumo = relationship("app.models.consumo_registros.HistorialConsumo", backref="empresa_hist_consumo", cascade="all, delete-orphan")
    control_planes = relationship("app.models.consumo_registros.ControlPlanMensual", backref="empresa_ctrl_plan", cascade="all, delete-orphan")
    bolsas_excedentes = relationship("app.models.consumo_registros.BolsaExcedente", backref="empresa_bolsa_exc", cascade="all, delete-orphan")
    recargas_adicionales = relationship("app.models.consumo_registros.RecargaAdicional", backref="empresa_recarga", cascade="all, delete-orphan")

    # --- AUDITORIA Y LOGS (CASCADA) ---
    logs_operaciones = relationship("app.models.log_operacion.LogOperacion", backref="empresa_log_op", cascade="all, delete-orphan")
    
    # --- MAESTROS CRÍTICOS (Orden de Eliminación: Últimos) ---
    # Se ponen al final para que sean los "padres" que sobreviven hasta que sus hijos (TiposDoc, Documentos) mueran.
    plan_cuentas = relationship("app.models.plan_cuenta.PlanCuenta", backref="empresa_plan_cuenta", cascade="all, delete-orphan")
    centros_costo = relationship("app.models.centro_costo.CentroCosto", backref="empresa_centro_costo", cascade="all, delete-orphan")
    tipos_nomina = relationship("app.models.nomina.TipoNomina", backref="empresa_tipo_nomina", cascade="all, delete-orphan")
