# app/services/migracion.py (Versión Maestra v7.0 - Modo Fusión Segura / Sin Borrado Masivo)

from sqlalchemy.orm import Session
from sqlalchemy import func, delete, select, or_, and_, case, literal
from datetime import datetime, date
from decimal import Decimal
from fastapi import HTTPException
import traceback
import json
import os
import hmac
import hashlib
from app.core.config import settings

# Modelos
from ..models import (
    Empresa, Tercero, PlanCuenta, CentroCosto, TipoDocumento, Usuario,
    CupoAdicional, UsuarioFavorito, ConceptoFavorito,
    Bodega, GrupoInventario, TasaImpuesto, Producto, StockBodega, MovimientoInventario,
    Documento, MovimientoContable, FormatoImpresion,
    PlantillaMaestra, PlantillaDetalle, ListaPrecio, ReglaPrecioGrupo,
    CaracteristicaDefinicion, CaracteristicaValorProducto,
    DocumentoEliminado, MovimientoEliminado, AplicacionPago,
    LogOperacion
)
from ..schemas import migracion as schemas_migracion
from ..services import cartera as services_cartera

# --- NUEVOS MODELOS SOPORTADOS (v7.5) ---
from ..models.propiedad_horizontal import PHConfiguracion, PHConcepto, PHTorre, PHUnidad, PHVehiculo, PHMascota
from ..models.activo_fijo import ActivoFijo
from ..models.activo_categoria import ActivoCategoria

# --- NUEVOS MODELOS SOPORTADOS (v7.6) ---
from ..models.cotizacion import Cotizacion, CotizacionDetalle
from ..models.produccion import Receta, RecetaDetalle, RecetaRecurso, OrdenProduccion, OrdenProduccionInsumo, OrdenProduccionRecurso
from ..models.configuracion_produccion import ConfiguracionProduccion
from ..models.conciliacion_bancaria import (
    ImportConfig, ImportSession, BankMovement, Reconciliation, 
    ReconciliationMovement, AccountingConfig, ReconciliationAudit
)

# =====================================================================================
# REGISTRO DECLARATIVO DE MÓDULOS (v7.6)
# =====================================================================================
"""
Sistema declarativo para registrar nuevos módulos de migración.

Este sistema permite agregar nuevos módulos de forma consistente sin modificar
el código principal de exportación/restauración. Cada módulo define:

- modelos_principales: Modelos principales del módulo
- modelos_detalle: Modelos de detalle/relación del módulo  
- clave_natural: Campo usado como clave natural para mapeo de IDs
- dependencias: Módulos/maestros requeridos para funcionar
- seccion_backup: Sección en el JSON de backup donde se almacenan los datos
- descripcion: Descripción legible del módulo

Para agregar un nuevo módulo:
1. Agregar entrada en MODULOS_ESPECIALIZADOS_CONFIG
2. Agregar campo booleano en ExportPaquetesModulosEspecializados (schemas/migracion.py)
3. Implementar lógica de exportación en generar_backup_json()
4. Implementar lógica de restauración en ejecutar_restauracion()
5. Agregar análisis en analizar_backup()
"""
MODULOS_ESPECIALIZADOS_CONFIG = {
    'cotizaciones': {
        'modelos_principales': [Cotizacion],
        'modelos_detalle': [CotizacionDetalle],
        'clave_natural': 'numero',
        'dependencias': ['terceros', 'productos', 'bodegas', 'usuarios'],
        'seccion_backup': 'cotizaciones',
        'descripcion': 'Cotizaciones maestras y sus detalles'
    },
    'produccion': {
        'modelos_principales': [Receta, OrdenProduccion, ConfiguracionProduccion],
        'modelos_detalle': [RecetaDetalle, RecetaRecurso, OrdenProduccionInsumo, OrdenProduccionRecurso],
        'clave_natural': 'nombre',  # Para recetas
        'dependencias': ['productos', 'tipos_documento', 'plan_cuentas', 'bodegas'],
        'seccion_backup': 'produccion',
        'descripcion': 'Recetas, órdenes de producción, recursos e insumos'
    },
    'conciliacion_bancaria': {
        'modelos_principales': [ImportConfig, ImportSession, AccountingConfig],
        'modelos_detalle': [BankMovement, Reconciliation, ReconciliationMovement, ReconciliationAudit],
        'clave_natural': 'name',  # Para configuraciones
        'dependencias': ['terceros', 'plan_cuentas', 'centros_costo', 'usuarios'],
        'seccion_backup': 'conciliacion_bancaria',
        'descripcion': 'Configuraciones, sesiones, movimientos y conciliaciones bancarias'
    }
}

def validar_dependencias_modulo(db: Session, modulo_config: dict, empresa_id: int) -> dict:
    """Valida que existan las dependencias necesarias para un módulo."""
    dependencias_faltantes = []
    
    for dep in modulo_config.get('dependencias', []):
        if dep == 'terceros':
            count = db.query(func.count(Tercero.id)).filter(Tercero.empresa_id == empresa_id).scalar()
        elif dep == 'productos':
            count = db.query(func.count(Producto.id)).filter(Producto.empresa_id == empresa_id).scalar()
        elif dep == 'plan_cuentas':
            count = db.query(func.count(PlanCuenta.id)).filter(PlanCuenta.empresa_id == empresa_id).scalar()
        elif dep == 'tipos_documento':
            count = db.query(func.count(TipoDocumento.id)).filter(TipoDocumento.empresa_id == empresa_id).scalar()
        elif dep == 'bodegas':
            count = db.query(func.count(Bodega.id)).filter(Bodega.empresa_id == empresa_id).scalar()
        elif dep == 'centros_costo':
            count = db.query(func.count(CentroCosto.id)).filter(CentroCosto.empresa_id == empresa_id).scalar()
        elif dep == 'usuarios':
            count = db.query(func.count(Usuario.id)).join(Empresa).filter(Empresa.id == empresa_id).scalar()
        else:
            count = 0
            
        if count == 0:
            dependencias_faltantes.append(dep)
    
    return {
        'valido': len(dependencias_faltantes) == 0,
        'dependencias_faltantes': dependencias_faltantes
    }


# =====================================================================================
# 0. UTILIDAD DE SERIALIZACIÓN
# =====================================================================================
class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def serialize_model(model_dict):
    """Convierte tipos complejos a nativos de Python para JSON."""
    new_dict = {}
    for k, v in model_dict.items():
        if k == '_sa_instance_state': continue
        if isinstance(v, (datetime, date)):
            new_dict[k] = v.isoformat()
        elif isinstance(v, Decimal):
            new_dict[k] = float(v)
        else:
            new_dict[k] = v
    return new_dict

# =====================================================================================
# 1. MOTOR DE EXPORTACIÓN (BACKUP)
# =====================================================================================

def compute_signature(data: dict) -> str:
    """Calcula la firma HMAC-SHA256 de un diccionario de datos."""
    # Ordenamos las llaves para asegurar consistencia en la serialización
    json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
    signature = hmac.new(
        settings.SECRET_KEY.encode('utf-8'),
        json_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def generar_backup_json(db: Session, empresa_id: int, filtros: dict = None):
    """Genera el snapshot completo (JSON) de la empresa, FIRMADO DIGITALMENTE."""
    
    print(f"🔍 [EXPORT] Iniciando exportación para Empresa {empresa_id}")
    # print(f"🔍 [EXPORT] Filtros Recibidos: {filtros}") # Debug

    # --- CORRECCIÓN: Manejo de Snapshot de Seguridad (filtros=None) ---
    # Si no se reciben filtros (caso Safety Snapshot), asumimos EXPORTAR TODO.
    if filtros is None:
        filtros = {
            'paquetes': {
                'maestros': {
                    'plan_cuentas': True, 'terceros': True, 'centros_costo': True, 
                    'tipos_documento': True, 'bodegas': True, 'grupos_inventario': True, 
                    'tasas_impuesto': True, 'productos': True
                },
                'modulos_especializados': {
                    'propiedad_horizontal': True, 'activos_fijos': True, 'favoritos': True
                },
                'configuraciones': {
                    'plantillas_documentos': True, 'libreria_conceptos': True
                },
                'transacciones': True
            }
        }

    # Extract flags for easier access
    paquetes = filtros.get('paquetes', {})
    maestros_flags = paquetes.get('maestros', {})
    special_flags = paquetes.get('modulos_especializados', {}) # <--- NUEVO
    config_flags = paquetes.get('configuraciones', {})
    transacciones_flag = paquetes.get('transacciones', False)

    backup_data = {
        "metadata": {
            "fecha_generacion": datetime.utcnow().isoformat(),
            "version_sistema": "7.6",  # Actualizado para incluir nuevos módulos
            "empresa_id_origen": empresa_id
        },
        "empresa": {}, "configuracion": {}, "maestros": {}, "inventario": {}, 
        "propiedad_horizontal": {}, "activos_fijos": {}, # <--- SECCIONES EXISTENTES
        "cotizaciones": {}, "produccion": {}, "conciliacion_bancaria": {}, # <--- NUEVAS SECCIONES
        "transacciones": []
    }

    # A. EMPRESA (Always export basic info for identification, but maybe minimal?)
    # User wants "only plan de cuentas", so maybe we should keep empresa info minimal or always include it?
    # Usually backup needs context. Let's keep it.
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if empresa:
        backup_data["empresa"] = {
            "razon_social": empresa.razon_social, "nit": empresa.nit,
            "direccion": empresa.direccion, "telefono": empresa.telefono,
            "email": empresa.email, "logo_url": empresa.logo_url,
            "limite_registros": empresa.limite_registros,
            "fecha_inicio_operaciones": str(empresa.fecha_inicio_operaciones) if empresa.fecha_inicio_operaciones else None
        }

    # B. CONFIGURACIÓN
    # Cupos (Linked to transacciones flag as per user request)
    if transacciones_flag:
        cupos = db.query(CupoAdicional).filter(CupoAdicional.empresa_id == empresa_id).all()
        backup_data["configuracion"]["cupos_adicionales"] = [
            {"anio": c.anio, "mes": c.mes, "cantidad": c.cantidad_adicional} for c in cupos
        ]

    if config_flags.get('plantillas_documentos', False):
        formatos = db.query(FormatoImpresion).filter(FormatoImpresion.empresa_id == empresa_id).all()
        backup_data["configuracion"]["formatos_impresion"] = []
        tipos_map = {t.id: t.codigo for t in db.query(TipoDocumento).filter(TipoDocumento.empresa_id == empresa_id).all()}
        for f in formatos:
            codigo_tipo = f.tipo_documento.codigo if getattr(f, 'tipo_documento', None) else tipos_map.get(f.tipo_documento_id)
            backup_data["configuracion"]["formatos_impresion"].append({
                "nombre": f.nombre, "tipo_doc_codigo": codigo_tipo,
                "contenido_html": f.contenido_html, "variables_json": f.variables_ejemplo_json
            })

    if config_flags.get('libreria_conceptos', False):
        conceptos = db.query(ConceptoFavorito).filter(ConceptoFavorito.empresa_id == empresa_id).all()
        backup_data["configuracion"]["conceptos_favoritos"] = [serialize_model(c.__dict__) for c in conceptos]

    if config_flags.get('plantillas_documentos', False): # Assuming plantillas contables go with document templates
        plantillas = db.query(PlantillaMaestra).filter(PlantillaMaestra.empresa_id == empresa_id).all()
        backup_data["configuracion"]["plantillas"] = []
        for p in plantillas:
            detalles = []
            for d in p.detalles:
                detalles.append({
                    "cuenta_codigo": d.cuenta.codigo if d.cuenta else None,
                    "centro_costo_codigo": d.centro_costo.codigo if d.centro_costo else None,
                    "concepto": d.concepto, "debito": float(d.debito or 0), "credito": float(d.credito or 0)
                })
            backup_data["configuracion"]["plantillas"].append({
                "nombre": p.nombre_plantilla, "detalles": detalles
            })

    # C. MAESTROS
    if maestros_flags.get('terceros', False):
        terceros = db.query(Tercero).filter(Tercero.empresa_id == empresa_id).all()
        lista_precio_map = {lp.id: lp.nombre for lp in db.query(ListaPrecio).filter(ListaPrecio.empresa_id == empresa_id).all()}
        
        terceros_data = []
        for t in terceros:
            t_dict = serialize_model(t.__dict__)
            if t.lista_precio_id and t.lista_precio_id in lista_precio_map:
                t_dict['lista_precio_nombre'] = lista_precio_map[t.lista_precio_id]
            terceros_data.append(t_dict)
        backup_data["maestros"]["terceros"] = terceros_data
    
    if maestros_flags.get('plan_cuentas', False):
        cuentas = db.query(PlanCuenta).filter(PlanCuenta.empresa_id == empresa_id).all()
        backup_data["maestros"]["plan_cuentas"] = [serialize_model(c.__dict__) for c in cuentas]
    
    if maestros_flags.get('centros_costo', False):
        ccs = db.query(CentroCosto).filter(CentroCosto.empresa_id == empresa_id).all()
        backup_data["maestros"]["centros_costo"] = [serialize_model(c.__dict__) for c in ccs]
    
    if maestros_flags.get('tipos_documento', False):
        tipos = db.query(TipoDocumento).filter(TipoDocumento.empresa_id == empresa_id).all()
        backup_data["maestros"]["tipos_documento"] = [serialize_model(t.__dict__) for t in tipos]

    # D. INVENTARIO
    if maestros_flags.get('bodegas', False):
        bodegas = db.query(Bodega).filter(Bodega.empresa_id == empresa_id).all()
        backup_data["inventario"]["bodegas"] = [{"codigo": b.id, "nombre": b.nombre} for b in bodegas]
    
    if maestros_flags.get('tasas_impuesto', False):
        impuestos = db.query(TasaImpuesto).filter(TasaImpuesto.empresa_id == empresa_id).all()
        backup_data["inventario"]["impuestos"] = []
        for i in impuestos:
            backup_data["inventario"]["impuestos"].append({
                "nombre": i.nombre, 
                "tasa": i.tasa,
                "cuenta_codigo": i.cuenta.codigo if i.cuenta else None,
                "cuenta_iva_descontable_codigo": i.cuenta_iva_descontable.codigo if i.cuenta_iva_descontable else None
            })
    
    # Listas de precio usually go with products or terceros, let's link it to products flag or add a specific one?
    # Frontend has 'productos' and 'grupos_inventario'. 
    # Let's include lists if products or terceros are selected, or maybe just if 'productos' is selected.
    # Actually, the frontend doesn't have a specific checkbox for 'listas_precio'.
    # It seems to be implicit. Let's include it if 'productos' or 'terceros' are selected.
    if maestros_flags.get('productos', False) or maestros_flags.get('terceros', False):
        listas = db.query(ListaPrecio).filter(ListaPrecio.empresa_id == empresa_id).all()
        backup_data["inventario"]["listas_precio"] = [{"nombre": l.nombre, "id_origen": l.id} for l in listas]
    
    if maestros_flags.get('grupos_inventario', False):
        grupos = db.query(GrupoInventario).filter(GrupoInventario.empresa_id == empresa_id).all()
        backup_data["inventario"]["grupos"] = []
        for g in grupos:
            reglas = []
            for r in g.reglas_precio:
                if r.lista_precio:
                    reglas.append({
                        "lista_nombre": r.lista_precio.nombre,
                        "porcentaje": float(r.porcentaje_incremento)
                    })
            caracteristicas = [{"nombre": c.nombre, "es_unidad": c.es_unidad_medida} for c in g.caracteristicas_definidas]

            backup_data["inventario"]["grupos"].append({
                "nombre": g.nombre,
                "cuenta_inventario_codigo": g.cuenta_inventario.codigo if g.cuenta_inventario else None,
                "cuenta_ingreso_codigo": g.cuenta_ingreso.codigo if g.cuenta_ingreso else None,
                "cuenta_costo_venta_codigo": g.cuenta_costo_venta.codigo if g.cuenta_costo_venta else None,
                "cuenta_ajuste_faltante_codigo": g.cuenta_ajuste_faltante.codigo if g.cuenta_ajuste_faltante else None,
                "cuenta_ajuste_sobrante_codigo": g.cuenta_ajuste_sobrante.codigo if g.cuenta_ajuste_sobrante else None,
                "cuentas": {
                    "inventario": g.cuenta_inventario.codigo if g.cuenta_inventario else None,
                    "ingreso": g.cuenta_ingreso.codigo if g.cuenta_ingreso else None,
                    "costo": g.cuenta_costo_venta.codigo if g.cuenta_costo_venta else None,
                    "faltante": g.cuenta_ajuste_faltante.codigo if g.cuenta_ajuste_faltante else None,
                    "sobrante": g.cuenta_ajuste_sobrante.codigo if g.cuenta_ajuste_sobrante else None
                },
                "reglas": reglas,
                "caracteristicas": caracteristicas
            })

    if maestros_flags.get('productos', False):
        backup_data["inventario"]["productos"] = []
        productos = db.query(Producto).filter(Producto.empresa_id == empresa_id).all()
        for p in productos:
            valores = []
            for v in p.valores_caracteristicas:
                definicion_nombre = v.definicion.nombre if v.definicion else None
                if definicion_nombre:
                     valores.append({"definicion": definicion_nombre, "valor": v.valor_texto if v.valor_texto is not None else v.valor_numerico})

            backup_data["inventario"]["productos"].append({
                "codigo": p.codigo, "nombre": p.nombre,
                "referencia": getattr(p, 'referencia', None), "precio_base": getattr(p, 'precio_base_manual', 0),
                "grupo_nombre": p.grupo_inventario.nombre if p.grupo_inventario else None,
                "impuesto_nombre": p.impuesto_iva.nombre if p.impuesto_iva else None,
                "valores": valores
            })

    # E. PROPIEDAD HORIZONTAL
    if special_flags.get('propiedad_horizontal', False):
        # 1. Configuración completa
        ph_conf = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == empresa_id).first()
        if ph_conf:
            config_dict = serialize_model(ph_conf.__dict__)
            # Agregar códigos de cuentas y tipos de documento para mapeo
            if ph_conf.tipo_documento_factura_id:
                tipo_factura = db.query(TipoDocumento).filter(TipoDocumento.id == ph_conf.tipo_documento_factura_id).first()
                config_dict["tipo_documento_factura_codigo"] = tipo_factura.codigo if tipo_factura else None
            if ph_conf.tipo_documento_recibo_id:
                tipo_recibo = db.query(TipoDocumento).filter(TipoDocumento.id == ph_conf.tipo_documento_recibo_id).first()
                config_dict["tipo_documento_recibo_codigo"] = tipo_recibo.codigo if tipo_recibo else None
            if ph_conf.cuenta_cartera_id:
                cuenta_cartera = db.query(PlanCuenta).filter(PlanCuenta.id == ph_conf.cuenta_cartera_id).first()
                config_dict["cuenta_cartera_codigo"] = cuenta_cartera.codigo if cuenta_cartera else None
            if ph_conf.cuenta_caja_id:
                cuenta_caja = db.query(PlanCuenta).filter(PlanCuenta.id == ph_conf.cuenta_caja_id).first()
                config_dict["cuenta_caja_codigo"] = cuenta_caja.codigo if cuenta_caja else None
            if ph_conf.cuenta_ingreso_intereses_id:
                cuenta_intereses = db.query(PlanCuenta).filter(PlanCuenta.id == ph_conf.cuenta_ingreso_intereses_id).first()
                config_dict["cuenta_ingreso_intereses_codigo"] = cuenta_intereses.codigo if cuenta_intereses else None
            backup_data["propiedad_horizontal"]["configuracion"] = config_dict
        
        # 2. Conceptos
        conceptos = db.query(PHConcepto).filter(PHConcepto.empresa_id == empresa_id).all()
        backup_data["propiedad_horizontal"]["conceptos"] = [serialize_model(c.__dict__) for c in conceptos]
        
        # 3. Torres, Unidades y datos relacionados
        torres = db.query(PHTorre).filter(PHTorre.empresa_id == empresa_id).all()
        backup_data["propiedad_horizontal"]["torres"] = []
        for t in torres:
            unidades = []
            for u in t.unidades:
                unidad_dict = {
                    "codigo": u.codigo, "nombre": u.nombre if hasattr(u, 'nombre') else u.codigo, 
                    "tipo": u.tipo, "matricula_inmobiliaria": u.matricula_inmobiliaria,
                    "area_privada": float(u.area_privada or 0), "coeficiente": float(u.coeficiente or 0),
                    "activo": u.activo, "observaciones": u.observaciones,
                    "propietario_principal_nit": u.propietario_principal.nit if u.propietario_principal else None,
                    "residente_actual_nit": u.residente_actual.nit if u.residente_actual else None
                }
                
                # Exportar vehículos
                vehiculos = []
                for v in u.vehiculos:
                    vehiculos.append(serialize_model(v.__dict__))
                unidad_dict["vehiculos"] = vehiculos
                
                # Exportar mascotas
                mascotas = []
                for m in u.mascotas:
                    mascotas.append(serialize_model(m.__dict__))
                unidad_dict["mascotas"] = mascotas
                
                # Exportar historial de coeficientes
                historial = []
                for h in u.historial_coeficientes:
                    hist_dict = serialize_model(h.__dict__)
                    hist_dict["usuario_email"] = h.usuario.email if h.usuario else None
                    historial.append(hist_dict)
                unidad_dict["historial_coeficientes"] = historial
                
                unidades.append(unidad_dict)
            
            backup_data["propiedad_horizontal"]["torres"].append({
                "nombre": t.nombre, "descripcion": t.descripcion,
                "unidades": unidades
            })
            
    # F. ACTIVOS FIJOS
    if special_flags.get('activos_fijos', False):
        cats = db.query(ActivoCategoria).filter(ActivoCategoria.empresa_id == empresa_id).all()
        backup_data["activos_fijos"]["categorias"] = [{"nombre": c.nombre, "vida_util": c.vida_util_niif_meses, "metodo": c.metodo_depreciacion} for c in cats]
        
        activos = db.query(ActivoFijo).filter(ActivoFijo.empresa_id == empresa_id).all()
        backup_data["activos_fijos"]["activos"] = []
        for a in activos:
            a_dict = serialize_model(a.__dict__)
            a_dict["categoria_nombre"] = a.categoria.nombre if a.categoria else None
            a_dict["responsable_nit"] = a.responsable.nit if a.responsable else None
            a_dict["centro_costo_codigo"] = a.centro_costo.codigo if a.centro_costo else None
            backup_data["activos_fijos"]["activos"].append(a_dict)
    
    # G. FAVORITOS
    if special_flags.get('favoritos', False):
         favs = db.query(UsuarioFavorito).join(Usuario).filter(Usuario.empresa_id == empresa_id).all()
         # Nota: Los favoritos son por usuario, al restaurar intentaremos mapear por email si coinciden
         backup_data["configuracion"]["user_favoritos"] = []
         for f in favs:
             backup_data["configuracion"]["user_favoritos"].append({
                 "email_usuario": f.usuario.email,
                 "ruta_enlace": f.ruta_enlace,
                 "nombre_personalizado": f.nombre_personalizado,
                 "orden": f.orden
             })

    # H. COTIZACIONES (v7.6)
    # Exporta cotizaciones maestras con sus detalles, incluyendo relaciones con terceros, productos y bodegas
    if special_flags.get('cotizaciones', False):
        cotizaciones = db.query(Cotizacion).filter(Cotizacion.empresa_id == empresa_id).all()
        backup_data["cotizaciones"]["cotizaciones"] = []
        
        for c in cotizaciones:
            # Exportar cotización maestra
            cotiz_dict = serialize_model(c.__dict__)
            cotiz_dict["tercero_nit"] = c.tercero.nit if c.tercero else None
            cotiz_dict["bodega_nombre"] = c.bodega.nombre if c.bodega else None
            cotiz_dict["usuario_email"] = c.usuario.email if c.usuario else None
            
            # Exportar detalles de la cotización
            detalles = []
            for d in c.detalles:
                detalle_dict = serialize_model(d.__dict__)
                detalle_dict["producto_codigo"] = d.producto.codigo if d.producto else None
                detalles.append(detalle_dict)
            
            cotiz_dict["detalles"] = detalles
            backup_data["cotizaciones"]["cotizaciones"].append(cotiz_dict)

    # I. PRODUCCIÓN (v7.6)
    # Exporta configuración, recetas, órdenes de producción con todos sus componentes
    if special_flags.get('produccion', False):
        # 1. Configuración de Producción
        prod_config = db.query(ConfiguracionProduccion).filter(ConfiguracionProduccion.empresa_id == empresa_id).first()
        if prod_config:
            config_dict = serialize_model(prod_config.__dict__)
            # Agregar códigos de tipos de documento para mapeo
            if prod_config.tipo_documento_orden_id:
                tipo_orden = db.query(TipoDocumento).filter(TipoDocumento.id == prod_config.tipo_documento_orden_id).first()
                config_dict["tipo_documento_orden_codigo"] = tipo_orden.codigo if tipo_orden else None
            if prod_config.tipo_documento_anulacion_id:
                tipo_anulacion = db.query(TipoDocumento).filter(TipoDocumento.id == prod_config.tipo_documento_anulacion_id).first()
                config_dict["tipo_documento_anulacion_codigo"] = tipo_anulacion.codigo if tipo_anulacion else None
            if prod_config.tipo_documento_consumo_id:
                tipo_consumo = db.query(TipoDocumento).filter(TipoDocumento.id == prod_config.tipo_documento_consumo_id).first()
                config_dict["tipo_documento_consumo_codigo"] = tipo_consumo.codigo if tipo_consumo else None
            if prod_config.tipo_documento_entrada_pt_id:
                tipo_entrada = db.query(TipoDocumento).filter(TipoDocumento.id == prod_config.tipo_documento_entrada_pt_id).first()
                config_dict["tipo_documento_entrada_pt_codigo"] = tipo_entrada.codigo if tipo_entrada else None
            backup_data["produccion"]["configuracion"] = config_dict

        # 2. Recetas
        recetas = db.query(Receta).filter(Receta.empresa_id == empresa_id).all()
        backup_data["produccion"]["recetas"] = []
        
        for r in recetas:
            receta_dict = serialize_model(r.__dict__)
            receta_dict["producto_codigo"] = r.producto.codigo if r.producto else None
            
            # Exportar detalles (insumos)
            detalles = []
            for d in r.detalles:
                detalle_dict = serialize_model(d.__dict__)
                detalle_dict["insumo_codigo"] = d.insumo.codigo if d.insumo else None
                detalles.append(detalle_dict)
            receta_dict["detalles"] = detalles
            
            # Exportar recursos
            recursos = []
            for rec in r.recursos:
                recurso_dict = serialize_model(rec.__dict__)
                if rec.cuenta_contable_id:
                    cuenta = db.query(PlanCuenta).filter(PlanCuenta.id == rec.cuenta_contable_id).first()
                    recurso_dict["cuenta_contable_codigo"] = cuenta.codigo if cuenta else None
                recursos.append(recurso_dict)
            receta_dict["recursos"] = recursos
            
            backup_data["produccion"]["recetas"].append(receta_dict)

        # 3. Órdenes de Producción
        ordenes = db.query(OrdenProduccion).filter(OrdenProduccion.empresa_id == empresa_id).all()
        backup_data["produccion"]["ordenes"] = []
        
        for o in ordenes:
            orden_dict = serialize_model(o.__dict__)
            orden_dict["producto_codigo"] = o.producto.codigo if o.producto else None
            orden_dict["receta_nombre"] = o.receta.nombre if o.receta else None
            orden_dict["bodega_destino_nombre"] = o.bodega_destino.nombre if o.bodega_destino else None
            
            # Exportar insumos consumidos
            insumos = []
            for i in o.insumos:
                insumo_dict = serialize_model(i.__dict__)
                insumo_dict["insumo_codigo"] = i.insumo.codigo if i.insumo else None
                insumo_dict["bodega_origen_nombre"] = i.bodega_origen.nombre if i.bodega_origen else None
                insumos.append(insumo_dict)
            orden_dict["insumos"] = insumos
            
            # Exportar recursos utilizados
            recursos = []
            for rec in o.recursos:
                recurso_dict = serialize_model(rec.__dict__)
                recursos.append(recurso_dict)
            orden_dict["recursos"] = recursos
            
            backup_data["produccion"]["ordenes"].append(orden_dict)

    # J. CONCILIACIÓN BANCARIA (v7.6)
    # Exporta configuraciones, sesiones, movimientos bancarios y auditoría
    if special_flags.get('conciliacion_bancaria', False):
        # 1. Configuraciones de Importación
        import_configs = db.query(ImportConfig).filter(ImportConfig.empresa_id == empresa_id).all()
        backup_data["conciliacion_bancaria"]["configuraciones_importacion"] = []
        
        for config in import_configs:
            config_dict = serialize_model(config.__dict__)
            config_dict["bank_nit"] = config.bank.nit if config.bank else None
            config_dict["creator_email"] = config.creator.email if config.creator else None
            config_dict["updater_email"] = config.updater.email if config.updater else None
            backup_data["conciliacion_bancaria"]["configuraciones_importacion"].append(config_dict)

        # 2. Configuraciones Contables
        accounting_configs = db.query(AccountingConfig).filter(AccountingConfig.empresa_id == empresa_id).all()
        backup_data["conciliacion_bancaria"]["configuraciones_contables"] = []
        
        for acc_config in accounting_configs:
            acc_config_dict = serialize_model(acc_config.__dict__)
            acc_config_dict["bank_account_codigo"] = acc_config.bank_account.codigo if acc_config.bank_account else None
            acc_config_dict["commission_account_codigo"] = acc_config.commission_account.codigo if acc_config.commission_account else None
            acc_config_dict["interest_income_account_codigo"] = acc_config.interest_income_account.codigo if acc_config.interest_income_account else None
            acc_config_dict["bank_charges_account_codigo"] = acc_config.bank_charges_account.codigo if acc_config.bank_charges_account else None
            acc_config_dict["adjustment_account_codigo"] = acc_config.adjustment_account.codigo if acc_config.adjustment_account else None
            acc_config_dict["default_cost_center_codigo"] = acc_config.default_cost_center.codigo if acc_config.default_cost_center else None
            acc_config_dict["creator_email"] = acc_config.creator.email if acc_config.creator else None
            acc_config_dict["updater_email"] = acc_config.updater.email if acc_config.updater else None
            backup_data["conciliacion_bancaria"]["configuraciones_contables"].append(acc_config_dict)

        # 3. Sesiones de Importación
        import_sessions = db.query(ImportSession).filter(ImportSession.empresa_id == empresa_id).all()
        backup_data["conciliacion_bancaria"]["sesiones_importacion"] = []
        
        for session in import_sessions:
            session_dict = serialize_model(session.__dict__)
            session_dict["bank_account_codigo"] = session.bank_account.codigo if session.bank_account else None
            session_dict["user_email"] = session.user.email if session.user else None
            backup_data["conciliacion_bancaria"]["sesiones_importacion"].append(session_dict)

        # 4. Movimientos Bancarios
        bank_movements = db.query(BankMovement).filter(BankMovement.empresa_id == empresa_id).all()
        backup_data["conciliacion_bancaria"]["movimientos_bancarios"] = []
        
        for movement in bank_movements:
            movement_dict = serialize_model(movement.__dict__)
            movement_dict["bank_account_codigo"] = movement.bank_account.codigo if movement.bank_account else None
            backup_data["conciliacion_bancaria"]["movimientos_bancarios"].append(movement_dict)

        # 5. Conciliaciones
        reconciliations = db.query(Reconciliation).filter(Reconciliation.empresa_id == empresa_id).all()
        backup_data["conciliacion_bancaria"]["conciliaciones"] = []
        
        for reconciliation in reconciliations:
            reconciliation_dict = serialize_model(reconciliation.__dict__)
            reconciliation_dict["user_email"] = reconciliation.user.email if reconciliation.user else None
            
            # Exportar movimientos contables asociados
            accounting_movements = []
            for acc_mov in reconciliation.accounting_movements:
                acc_mov_dict = serialize_model(acc_mov.__dict__)
                accounting_movements.append(acc_mov_dict)
            reconciliation_dict["movimientos_contables"] = accounting_movements
            
            backup_data["conciliacion_bancaria"]["conciliaciones"].append(reconciliation_dict)

        # 6. Auditoría de Conciliaciones
        reconciliation_audits = db.query(ReconciliationAudit).filter(ReconciliationAudit.empresa_id == empresa_id).all()
        backup_data["conciliacion_bancaria"]["auditoria"] = []
        
        for audit in reconciliation_audits:
            audit_dict = serialize_model(audit.__dict__)
            audit_dict["user_email"] = audit.user.email if audit.user else None
            backup_data["conciliacion_bancaria"]["auditoria"].append(audit_dict)

    # F. TRANSACCIONES
    if transacciones_flag:
        query_docs = db.query(Documento).filter(Documento.empresa_id == empresa_id)

        # --- APLICACIÓN DE FILTROS ---
        if filtros:
            f_tercero = filtros.get('terceroId') # Normalized to camelCase from schema or snake_case from dict? Schema has camelCase.
            if f_tercero:
                query_docs = query_docs.filter(Documento.beneficiario_id == f_tercero)
            
            f_tipo = filtros.get('tipoDocId')
            if f_tipo:
                query_docs = query_docs.filter(Documento.tipo_documento_id == f_tipo)
                
            f_desde = filtros.get('fechaInicio')
            if f_desde:
                query_docs = query_docs.filter(Documento.fecha >= f_desde)
                
            f_hasta = filtros.get('fechaFin')
            if f_hasta:
                query_docs = query_docs.filter(Documento.fecha <= f_hasta)

        docs = query_docs.all()
        print(f"✅ [EXPORT] Documentos encontrados tras filtrar: {len(docs)}")

        for d in docs:
            doc_packet = {
                "tipo_doc_codigo": d.tipo_documento.codigo, "numero": d.numero,
                "fecha": d.fecha.isoformat() if d.fecha else None,
                "tercero_nit": d.beneficiario.nit if d.beneficiario else None,
                "centro_costo_codigo": d.centro_costo.codigo if d.centro_costo else None,
                "anulado": d.anulado, "observaciones": getattr(d, 'observaciones', None),
                "movimientos_contables": [], "movimientos_inventario": []
            }
            for m in d.movimientos:
                doc_packet["movimientos_contables"].append({
                    "cuenta_codigo": m.cuenta.codigo, 
                    "debito": float(m.debito or 0), "credito": float(m.credito or 0), 
                    "concepto": m.concepto,
                    "producto_codigo": m.producto.codigo if m.producto else None,
                    "cantidad": float(m.cantidad or 0)
                })
            movs_inv = db.query(MovimientoInventario).filter(MovimientoInventario.documento_id == d.id).all()
            for mi in movs_inv:
                doc_packet["movimientos_inventario"].append({
                    "producto_codigo": mi.producto.codigo, "bodega_nombre": mi.bodega.nombre,
                    "tipo": mi.tipo_movimiento, "cantidad": float(mi.cantidad),
                    "costo_unitario": float(mi.costo_unitario), "costo_total": float(mi.costo_total)
                })
            backup_data["transacciones"].append(doc_packet)

    # --- FIRMA DIGITAL ---
    signature = compute_signature(backup_data)
    signed_backup = {
        "data": backup_data,
        "signature": signature
    }
    
    return signed_backup

# =====================================================================================
# 2. MOTOR DE ANÁLISIS
# =====================================================================================
def analizar_backup(db: Session, analysis_request: schemas_migracion.AnalysisRequest):
    backup_data_wrapper = analysis_request.backupData
    target_empresa_id = analysis_request.targetEmpresaId
    
    # 1. Validar Firma
    data = backup_data_wrapper.get("data")
    signature = backup_data_wrapper.get("signature")
    
    if not data or not signature:
        # Soporte para backups antiguos (sin firma) - Opcional: Rechazar o Advertir
        # Por seguridad estricta, rechazamos.
        raise HTTPException(status_code=400, detail="El archivo de backup no tiene firma digital o formato válido.")
        
    computed_signature = compute_signature(data)
    integrity_valid = True
    if not hmac.compare_digest(computed_signature, signature):
        # En v7.0 permitimos análisis incluso si la firma falla, para diagnosticar
        integrity_valid = False
        print("⚠️ [WARNING] Firma digital inválida en Backup. Se procede condicionallmente.")

    # 2. Proceder con el análisis usando 'data' (el contenido real)
    backup_data = data
    
    # 3. Detectar versión del backup y aplicar compatibilidad
    version_backup = backup_data.get("metadata", {}).get("version_sistema", "7.0")
    compatibilidad = verificar_compatibilidad_version(version_backup)
    
    report = {
        "summary": {}, 
        "conflicts": {"documentos": [], "maestros_faltantes": []}, 
        "sourceEmpresaId": backup_data.get("metadata", {}).get("empresa_id_origen"), 
        "targetEmpresaId": target_empresa_id,
        "integrity_valid": integrity_valid,
        "version_backup": version_backup,
        "compatibilidad": compatibilidad
    }
    
    maestros_map = {
        'terceros': (Tercero, 'nit', 'nit', 'maestros'),
        'plan_cuentas': (PlanCuenta, 'codigo', 'codigo', 'maestros'),
        'centros_costo': (CentroCosto, 'codigo', 'codigo', 'maestros'),
        'tipos_documento': (TipoDocumento, 'codigo', 'codigo', 'maestros'),
        'bodegas': (Bodega, 'nombre', 'nombre', 'inventario'),
        'grupos': (GrupoInventario, 'nombre', 'nombre', 'inventario'),
        'impuestos': (TasaImpuesto, 'nombre', 'nombre', 'inventario'),
        'listas_precio': (ListaPrecio, 'nombre', 'nombre', 'inventario'),
        'productos': (Producto, 'codigo', 'codigo', 'inventario'),
        'formatos_impresion': (FormatoImpresion, 'nombre', 'nombre', 'configuracion'),
        'plantillas': (PlantillaMaestra, 'nombre_plantilla', 'nombre', 'configuracion'),
        'conceptos_favoritos': (ConceptoFavorito, 'descripcion', 'descripcion', 'configuracion'),
        'categorias_activos': (ActivoCategoria, 'nombre', 'nombre', 'activos_fijos'),
        'activos_fijos': (ActivoFijo, 'codigo', 'codigo', 'activos_fijos')
    }

    for key_reporte, (model, db_key, json_key, section) in maestros_map.items():
        source_items = []
        if section in backup_data and key_reporte in backup_data[section]:
            source_items = backup_data[section][key_reporte]
        elif key_reporte in backup_data:
            source_items = backup_data[key_reporte]
        if not source_items: continue
        
        target_rows = db.query(getattr(model, db_key)).filter(getattr(model, 'empresa_id', None) == target_empresa_id).all()
        target_keys = {str(getattr(row, db_key)).strip() for row in target_rows}
        
        # Robust check: Ensure item is a dict before accessing .get()
        a_crear = sum(1 for item in source_items if isinstance(item, dict) and str(item.get(json_key, '')).strip() not in target_keys)
        coincidencias = len(source_items) - a_crear
        
        titulos = {
            'grupos': 'Grupos Inventario', 'impuestos': 'Tasas Impuesto', 'plantillas': 'Plantillas Contables',
            'formatos_impresion': 'Formatos PDF', 'plan_cuentas': 'Plan de Cuentas', 'centros_costo': 'Centros de Costo',
            'conceptos_favoritos': 'Conceptos Favoritos', 'terceros': 'Terceros', 'bodegas': 'Bodegas', 'productos': 'Productos'
        }
        report["summary"][titulos.get(key_reporte, key_reporte)] = {"total": len(source_items), "a_crear": a_crear, "coincidencias": coincidencias}

    cupos_source = backup_data.get("configuracion", {}).get("cupos_adicionales", [])
    if cupos_source:
        target_cupos = db.query(CupoAdicional).filter(CupoAdicional.empresa_id == target_empresa_id).all()
        target_keys_cupos = {f"{c.anio}-{c.mes}" for c in target_cupos}
        a_crear_cupos = sum(1 for c in cupos_source if f"{c['anio']}-{c['mes']}" not in target_keys_cupos)
        report["summary"]["Cupos Mensuales"] = {"total": len(cupos_source), "a_crear": a_crear_cupos, "coincidencias": len(cupos_source) - a_crear_cupos}

    # ANÁLISIS DE DOCUMENTOS
    docs_source = backup_data.get("transacciones") or backup_data.get("documentos") or []
    if docs_source:
        sq_totales = db.query(
            MovimientoContable.documento_id,
            func.sum(MovimientoContable.debito).label('total_debito')
        ).group_by(MovimientoContable.documento_id).subquery()

        existing_docs_query = db.query(
            Documento.id,
            Documento.tipo_documento_id,
            Documento.numero,
            func.coalesce(sq_totales.c.total_debito, 0).label('total_debito')
        ).outerjoin(sq_totales, Documento.id == sq_totales.c.documento_id)\
         .filter(Documento.empresa_id == target_empresa_id).all()

        # En análisis no hacemos nada crítico, solo reportamos
        a_importar_o_corregir = len(docs_source)
        report["summary"]["Documentos y Movimientos"] = {
            "total": len(docs_source), "a_crear": a_importar_o_corregir, "coincidencias": 0
        }

    # ANÁLISIS DE PROPIEDAD HORIZONTAL
    ph_data = backup_data.get("propiedad_horizontal", {})
    if ph_data:
        # Conceptos
        if "conceptos" in ph_data:
            c_src = ph_data["conceptos"]
            c_existing = {c.nombre for c in db.query(PHConcepto).filter(PHConcepto.empresa_id == target_empresa_id).all()}
            a_crear = sum(1 for c in c_src if c["nombre"] not in c_existing)
            report["summary"]["PH Conceptos"] = {"total": len(c_src), "a_crear": a_crear, "coincidencias": len(c_src) - a_crear}
        
        # Torres (y Unidades implícitas en total)
        if "torres" in ph_data:
            t_src = ph_data["torres"]
            t_existing = {t.nombre for t in db.query(PHTorre).filter(PHTorre.empresa_id == target_empresa_id).all()}
            a_crear = sum(1 for t in t_src if t["nombre"] not in t_existing)
            report["summary"]["PH Torres"] = {"total": len(t_src), "a_crear": a_crear, "coincidencias": len(t_src) - a_crear}

    # ANÁLISIS DE FAVORITOS USUARIO
    fav_src = backup_data.get("configuracion", {}).get("user_favoritos", [])
    if fav_src:
        report["summary"]["Favoritos de Usuario"] = {"total": len(fav_src), "a_crear": len(fav_src), "coincidencias": 0}

    # ANÁLISIS DE COTIZACIONES
    cotizaciones_data = backup_data.get("cotizaciones", {})
    if cotizaciones_data:
        if "cotizaciones" in cotizaciones_data:
            c_src = cotizaciones_data["cotizaciones"]
            c_existing = {c.numero for c in db.query(Cotizacion).filter(Cotizacion.empresa_id == target_empresa_id).all()}
            a_crear = sum(1 for c in c_src if c.get("numero") not in c_existing)
            report["summary"]["Cotizaciones"] = {"total": len(c_src), "a_crear": a_crear, "coincidencias": len(c_src) - a_crear}

    # ANÁLISIS DE PRODUCCIÓN
    produccion_data = backup_data.get("produccion", {})
    if produccion_data:
        # Recetas
        if "recetas" in produccion_data:
            r_src = produccion_data["recetas"]
            r_existing = {r.nombre for r in db.query(Receta).filter(Receta.empresa_id == target_empresa_id).all()}
            a_crear = sum(1 for r in r_src if r.get("nombre") not in r_existing)
            report["summary"]["Recetas de Producción"] = {"total": len(r_src), "a_crear": a_crear, "coincidencias": len(r_src) - a_crear}
        
        # Órdenes de Producción
        if "ordenes" in produccion_data:
            o_src = produccion_data["ordenes"]
            o_existing = {o.numero_orden for o in db.query(OrdenProduccion).filter(OrdenProduccion.empresa_id == target_empresa_id).all()}
            a_crear = sum(1 for o in o_src if o.get("numero_orden") not in o_existing)
            report["summary"]["Órdenes de Producción"] = {"total": len(o_src), "a_crear": a_crear, "coincidencias": len(o_src) - a_crear}

    # ANÁLISIS DE CONCILIACIÓN BANCARIA
    conciliacion_data = backup_data.get("conciliacion_bancaria", {})
    if conciliacion_data:
        # Configuraciones de Importación
        if "configuraciones_importacion" in conciliacion_data:
            ci_src = conciliacion_data["configuraciones_importacion"]
            ci_existing = {c.name for c in db.query(ImportConfig).filter(ImportConfig.empresa_id == target_empresa_id).all()}
            a_crear = sum(1 for c in ci_src if c.get("name") not in ci_existing)
            report["summary"]["Configuraciones de Importación Bancaria"] = {"total": len(ci_src), "a_crear": a_crear, "coincidencias": len(ci_src) - a_crear}
        
        # Sesiones de Importación
        if "sesiones_importacion" in conciliacion_data:
            si_src = conciliacion_data["sesiones_importacion"]
            si_existing = {s.id for s in db.query(ImportSession).filter(ImportSession.empresa_id == target_empresa_id).all()}
            a_crear = sum(1 for s in si_src if s.get("id") not in si_existing)
            report["summary"]["Sesiones de Importación Bancaria"] = {"total": len(si_src), "a_crear": a_crear, "coincidencias": len(si_src) - a_crear}
        
        # Movimientos Bancarios
        if "movimientos_bancarios" in conciliacion_data:
            mb_src = conciliacion_data["movimientos_bancarios"]
            report["summary"]["Movimientos Bancarios"] = {"total": len(mb_src), "a_crear": len(mb_src), "coincidencias": 0}
        
        # Conciliaciones
        if "conciliaciones" in conciliacion_data:
            conc_src = conciliacion_data["conciliaciones"]
            report["summary"]["Conciliaciones Bancarias"] = {"total": len(conc_src), "a_crear": len(conc_src), "coincidencias": 0}

    return report

# =====================================================================================
# 3. MOTOR DE RESTAURACIÓN (ATOMICIDAD TOTAL v7.0 - Modo Fusión Segura)
# =====================================================================================
def ejecutar_restauracion(db: Session, request: schemas_migracion.AnalysisRequest, user_id: int):
    backup_data_wrapper = request.backupData
    target_empresa_id = request.targetEmpresaId

    # 0. Validar Existencia de Empresa Destino
    empresa_exists = db.query(Empresa).filter(Empresa.id == target_empresa_id).first()
    if not empresa_exists:
        raise HTTPException(status_code=404, detail=f"La empresa destino con ID {target_empresa_id} no existe. Por favor recargue la página o seleccione una empresa válida.")
    
    # 1. Validar Firma (Nuevamente, por seguridad)
    data = backup_data_wrapper.get("data")
    signature = backup_data_wrapper.get("signature")
    
    if not data or not signature:
        raise HTTPException(status_code=400, detail="El archivo de backup no tiene firma digital.")
        
    computed_signature = compute_signature(data)
    if not hmac.compare_digest(computed_signature, signature):
        if not request.bypass_signature:
            raise HTTPException(status_code=400, detail="ERROR CRÍTICO: Firma inválida. El archivo ha sido modificado o la llave no coincide. Use permisos de administrador para forzar.")
        
    backup_data = data
    
    # 2. Verificar compatibilidad y migrar si es necesario
    version_backup = backup_data.get("metadata", {}).get("version_sistema", "7.0")
    compatibilidad = verificar_compatibilidad_version(version_backup)
    
    if not compatibilidad['compatible']:
        if compatibilidad['requiere_migracion']:
            raise HTTPException(status_code=400, detail=compatibilidad['mensaje'])
        else:
            raise HTTPException(status_code=400, detail=f"Backup incompatible: {compatibilidad['mensaje']}")
    
    # Migrar automáticamente si es necesario
    if version_backup != "7.6":
        backup_data = migrar_backup_version(backup_data, version_backup, "7.6")
    
    resumen = {
        "acciones_realizadas": [],
        "maestros_actualizados": 0,
        "documentos_procesados": 0,
        "version_backup": version_backup,
        "compatibilidad": compatibilidad['mensaje']
    }

    # --- FASE 0: CINTURÓN DE SEGURIDAD ---
    try:
        print(f"🚀 INICIANDO PROTOCOLO ESPEJO ATÓMICO v7.0 PARA EMPRESA {target_empresa_id}")
        
        safety_snapshot = generar_backup_json(db, target_empresa_id)
        filename = f"SAFETY_RESTORE_{target_empresa_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("backups/safety", exist_ok=True)
        with open(f"backups/safety/{filename}", "w", encoding="utf-8") as f:
            json.dump(safety_snapshot, f, cls=AlchemyEncoder)
            
        resumen["acciones_realizadas"].append(f"🔒 Snapshot de seguridad creado: {filename}")

        # 1. RESTAURAR CONFIGURACIÓN DE EMPRESA
        empresa = db.query(Empresa).filter(Empresa.id == target_empresa_id).first()
        if "empresa" in backup_data and empresa:
            emp_data = backup_data["empresa"]
            # BLOQUEADO: No sobreescribir datos de la empresa destino al restaurar.
            # Se preserva la identidad (Nit, Dirección, etc.) de la empresa que recibe el PUC.
            # for field in ["direccion", "telefono", "email", "logo_url"]:
            #     if field in emp_data: setattr(empresa, field, emp_data[field])
            # db.add(empresa)

        # 2. RESTAURAR CUPOS (BLOQUEADO POR SEGURIDAD)
        # No se deben transferir cupos adicionales entre empresas. Cada empresa mantiene sus propios cupos comprados.
        # if "cupos_adicionales" in backup_data.get("configuracion", {}):
        #     db.query(CupoAdicional).filter(CupoAdicional.empresa_id == target_empresa_id).delete()
        #     for c in backup_data["configuracion"]["cupos_adicionales"]:
        #         db.add(CupoAdicional(empresa_id=target_empresa_id, anio=c["anio"], mes=c["mes"], cantidad_adicional=c["cantidad"]))

        # 3. MAESTROS
        maestros_src = backup_data.get("maestros", {})
        inv_src = backup_data.get("inventario", {})
        
        # Restaurar Listas de Precio PRIMERO
        _upsert_manual_seguro(db, ListaPrecio, 'listas_precio', 'nombre', inv_src, target_empresa_id, user_id)
        db.flush()
        
        map_listas = _get_id_translation_map(db, ListaPrecio, 'nombre', inv_src, target_empresa_id)

        # Restauración de Terceros (ID MAP BLINDADO)
        _upsert_manual_seguro(db, Tercero, 'terceros', 'nit', maestros_src, target_empresa_id, user_id, id_maps={'lista_precio_id': map_listas})
        
        _upsert_manual_seguro(db, Bodega, 'bodegas', 'nombre', inv_src, target_empresa_id, user_id)
        _restore_jerarquico(db, PlanCuenta, 'plan_cuentas', 'cuenta_padre_id', maestros_src, target_empresa_id, user_id)
        _restore_jerarquico(db, CentroCosto, 'centros_costo', 'centro_costo_padre_id', maestros_src, target_empresa_id, user_id)
        db.flush()

        map_cuentas = _get_id_translation_map(db, PlanCuenta, 'codigo', maestros_src, target_empresa_id)
        map_ccs = _get_id_translation_map(db, CentroCosto, 'codigo', maestros_src, target_empresa_id)
        map_terceros = _get_id_translation_map(db, Tercero, 'nit', maestros_src, target_empresa_id)
        map_bodegas = _get_id_translation_map(db, Bodega, 'nombre', inv_src, target_empresa_id)
        
        config_src = backup_data.get("configuracion", {})
        _upsert_manual_seguro(db, ConceptoFavorito, 'conceptos_favoritos', 'descripcion', config_src, target_empresa_id, user_id, id_maps={"centro_costo_id": map_ccs})

        id_maps_tipos = {
            "cuenta_caja_id": map_cuentas, 
            "cuenta_debito_cxc_id": map_cuentas, "cuenta_credito_cxc_id": map_cuentas,
            "cuenta_debito_cxp_id": map_cuentas, "cuenta_credito_cxp_id": map_cuentas
        }
        _upsert_manual_seguro(db, TipoDocumento, 'tipos_documento', 'codigo', maestros_src, target_empresa_id, user_id, id_maps=id_maps_tipos)
        
        # --- RESTAURACIÓN DE GRUPOS ---
        if "grupos" in inv_src:
            for g in inv_src["grupos"]:
                if "cuentas" in g and isinstance(g["cuentas"], dict):
                    ctas = g["cuentas"]
                    if "inventario" in ctas: g["cuenta_inventario_codigo"] = ctas["inventario"]
                    if "ingreso" in ctas: g["cuenta_ingreso_codigo"] = ctas["ingreso"]
                    if "costo" in ctas: g["cuenta_costo_venta_codigo"] = ctas["costo"]
                    if "faltante" in ctas: g["cuenta_ajuste_faltante_codigo"] = ctas["faltante"]
                    if "sobrante" in ctas: g["cuenta_ajuste_sobrante_codigo"] = ctas["sobrante"]

        id_maps_grupos = {
            "cuenta_inventario_id": map_cuentas, "cuenta_ingreso_id": map_cuentas, "cuenta_costo_venta_id": map_cuentas,
            "cuenta_ajuste_faltante_id": map_cuentas, "cuenta_ajuste_sobrante_id": map_cuentas
        }
        _upsert_manual_seguro(db, GrupoInventario, 'grupos', 'nombre', inv_src, target_empresa_id, user_id, id_maps=id_maps_grupos)
        db.flush()
        
        # Sub-tablas de Grupos
        if "grupos" in inv_src:
            if not map_listas:
                listas_db = db.query(ListaPrecio).filter(ListaPrecio.empresa_id == target_empresa_id).all()
                map_listas = {l.nombre: l.id for l in listas_db}

            target_grupos = db.query(GrupoInventario).filter(GrupoInventario.empresa_id == target_empresa_id).all()
            map_grupos_obj = {g.nombre: g for g in target_grupos}

            for grp_data in inv_src["grupos"]:
                grupo_db = map_grupos_obj.get(grp_data["nombre"])
                if not grupo_db: continue

                if "caracteristicas" in grp_data:
                    subq = db.query(CaracteristicaDefinicion.id).filter(CaracteristicaDefinicion.grupo_inventario_id == grupo_db.id).subquery()
                    # Borrar valores
                    db.query(CaracteristicaValorProducto).filter(CaracteristicaValorProducto.definicion_id.in_(select(subq))).delete(synchronize_session=False)
                    # Borrar definiciones
                    db.query(CaracteristicaDefinicion).filter(CaracteristicaDefinicion.grupo_inventario_id == grupo_db.id).delete(synchronize_session=False)
                    
                    for c in grp_data["caracteristicas"]:
                        db.add(CaracteristicaDefinicion(grupo_inventario_id=grupo_db.id, nombre=c["nombre"], es_unidad_medida=c["es_unidad"]))
                
                if "reglas" in grp_data:
                    db.query(ReglaPrecioGrupo).filter(ReglaPrecioGrupo.grupo_inventario_id == grupo_db.id).delete(synchronize_session=False)
                    for r in grp_data["reglas"]:
                        lista_id = map_listas.get(r.get("lista_nombre"))
                        if lista_id:
                            db.add(ReglaPrecioGrupo(grupo_inventario_id=grupo_db.id, lista_precio_id=lista_id, porcentaje_incremento=r["porcentaje"]))

        # --- IMPUESTOS Y PRODUCTOS ---
        id_maps_impuestos = {"cuenta_id": map_cuentas, "cuenta_iva_descontable_id": map_cuentas}
        _upsert_manual_seguro(db, TasaImpuesto, 'impuestos', 'nombre', inv_src, target_empresa_id, user_id, id_maps=id_maps_impuestos)
        db.flush()

        map_grupos = _get_id_translation_map(db, GrupoInventario, 'nombre', inv_src, target_empresa_id)
        map_impuestos = _get_id_translation_map(db, TasaImpuesto, 'nombre', inv_src, target_empresa_id)
        _upsert_manual_seguro(db, Producto, 'productos', 'codigo', inv_src, target_empresa_id, user_id, id_maps={"grupo_id": map_grupos, "impuesto_iva_id": map_impuestos})
        db.flush()
        map_productos = _get_id_translation_map(db, Producto, 'codigo', inv_src, target_empresa_id)

        # 5. FORMATOS Y PLANTILLAS
        if "formatos_impresion" in config_src:
            # Eliminar formatos existentes (defaults) para evitar colisión de Nombres Únicos
            db.query(FormatoImpresion).filter(FormatoImpresion.empresa_id == target_empresa_id).delete()
            db.flush()

            map_tipos_final = _get_id_translation_map(db, TipoDocumento, 'codigo', maestros_src, target_empresa_id)
            id_maps_fmt = {"tipo_documento_id": map_tipos_final}
            
            # Modificar nombres para garantizar unicidad global (la tabla tiene unique en nombre)
            for fmt in config_src["formatos_impresion"]:
                if "nombre" in fmt:
                    # Append suffix only if not present (though restoring usually brings clean names)
                    suffix = f" - {target_empresa_id}"
                    if not str(fmt["nombre"]).endswith(suffix):
                        fmt["nombre"] = f"{fmt['nombre']}{suffix}"

            _upsert_manual_seguro(db, FormatoImpresion, 'formatos_impresion', 'nombre', config_src, target_empresa_id, user_id, id_maps=id_maps_fmt)

        if "plantillas" in config_src:
            db.query(PlantillaMaestra).filter(PlantillaMaestra.empresa_id == target_empresa_id).delete(synchronize_session=False)
            db.flush()
            for p in config_src["plantillas"]:
                maestra = PlantillaMaestra(empresa_id=target_empresa_id, nombre_plantilla=p["nombre"], created_at=datetime.utcnow(), created_by=user_id)
                db.add(maestra)
                db.flush()
                for d in p["detalles"]:
                    cuenta_id = map_cuentas.get(d["cuenta_codigo"])
                    cc_id = map_ccs.get(d.get("centro_costo_codigo"))
                    if cuenta_id:
                        db.add(PlantillaDetalle(plantilla_maestra_id=maestra.id, cuenta_id=cuenta_id, centro_costo_id=cc_id, concepto=d["concepto"], debito=d["debito"], credito=d["credito"]))
        db.flush()

        # 6. MÓDULOS ESPECIALIZADOS
        
        # --- PROPIEDAD HORIZONTAL ---
        ph_data = backup_data.get("propiedad_horizontal", {})
        if ph_data:
            # Config
            if "configuracion" in ph_data:
                conf_data = ph_data["configuracion"]
                # Upsert PH Config
                ph_conf = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == target_empresa_id).first()
                if not ph_conf:
                    ph_conf = PHConfiguracion(empresa_id=target_empresa_id)
                    db.add(ph_conf)
                # Actualizar campos simples
                # Generar mapas de traducción de ID (Old ID -> New ID)
                map_tipos_code = _get_id_translation_map(db, TipoDocumento, 'codigo', maestros_src, target_empresa_id)
                map_tipos_id = {}
                for item in maestros_src.get('tipos_documento', []):
                    if str(item.get('codigo')) in map_tipos_code:
                        map_tipos_id[str(item['id'])] = map_tipos_code[str(item['codigo'])]

                map_cuentas_id = {}
                for item in maestros_src.get('plan_cuentas', []):
                     if str(item.get('codigo')) in map_cuentas:
                         map_cuentas_id[str(item['id'])] = map_cuentas[str(item['codigo'])]

                # Actualizar campos con mapeo
                for k, v in conf_data.items():
                    if not hasattr(ph_conf, k) or k in ['id', 'empresa_id']: continue
                    
                    val_to_set = v
                    
                    # Mapear Foreign Keys
                    if k in ['tipo_documento_factura_id', 'tipo_documento_recibo_id'] and v is not None:
                         val_to_set = map_tipos_id.get(str(v))
                    elif k in ['cuenta_cartera_id', 'cuenta_caja_id', 'cuenta_ingreso_intereses_id'] and v is not None:
                         val_to_set = map_cuentas_id.get(str(v))
                    
                    setattr(ph_conf, k, val_to_set)
            
            # Conceptos
            _upsert_manual_seguro(db, PHConcepto, 'conceptos', 'nombre', ph_data, target_empresa_id, user_id, 
                                id_maps={"cuenta_cxc_id": map_cuentas, "cuenta_caja_id": map_cuentas,
                                         "cuenta_ingreso_id": map_cuentas, "cuenta_interes_id": map_cuentas})
            
            # Torres y Unidades
            if "torres" in ph_data:
                for t_data in ph_data["torres"]:
                    torre = db.query(PHTorre).filter(PHTorre.empresa_id == target_empresa_id, PHTorre.nombre == t_data["nombre"]).first()
                    if not torre:
                        torre = PHTorre(empresa_id=target_empresa_id, nombre=t_data["nombre"])
                        db.add(torre)
                        db.flush()
                    
                    for u_data in t_data["unidades"]:
                        unidad = db.query(PHUnidad).filter(PHUnidad.empresa_id == target_empresa_id, PHUnidad.codigo == u_data["codigo"]).first()
                        prop_id = map_terceros.get(u_data.get("propietario_nit"))
                        arr_id = map_terceros.get(u_data.get("arrendatario_nit"))
                        
                        if not unidad:
                             unidad = PHUnidad(empresa_id=target_empresa_id, torre_id=torre.id, codigo=u_data["codigo"], nombre=u_data["nombre"])
                             db.add(unidad)
                        
                        unidad.coeficiente = u_data["coeficiente"]
                        unidad.propietario_id = prop_id
                        unidad.arrendatario_id = arr_id
            
        # --- ACTIVOS FIJOS ---
        activos_data = backup_data.get("activos_fijos", {})
        if activos_data:
             _upsert_manual_seguro(db, ActivoCategoria, 'categorias', 'nombre', activos_data, target_empresa_id, user_id, 
                                   id_maps={'cuenta_activo_id': map_cuentas, 'cuenta_depreciacion_acumulada_id': map_cuentas, 'cuenta_gasto_depreciacion_id': map_cuentas})
             db.flush()
             map_cats = _get_id_translation_map(db, ActivoCategoria, 'nombre', activos_data, target_empresa_id)
             
             # --- AUTO-CREATE MISSING CATEGORIES (Prevent FK Error) ---
             # If an asset refers to a category that wasn't in the categories list (or failed restore), we create it.
             existing_cat_names = set(map_cats.keys())
             cats_to_create = set()
             for a in activos_data.get("activos", []):
                 c_name = str(a.get("categoria_nombre", "")).strip()
                 if c_name and c_name not in existing_cat_names:
                     cats_to_create.add(c_name)
             
             if cats_to_create:
                 print(f"⚠️ Auto-creating {len(cats_to_create)} missing categories for assets: {cats_to_create}")
                 for c_name in cats_to_create:
                     new_cat = ActivoCategoria(
                         empresa_id=target_empresa_id, 
                         nombre=c_name, 
                         vida_util_niif_meses=60, # Default safe value
                         metodo_depreciacion="LINEA_RECTA"
                     )
                     db.add(new_cat)
                 db.flush()
                 # Rebuild Map
                 map_cats = _get_id_translation_map(db, ActivoCategoria, 'nombre', activos_data, target_empresa_id)
                 # Add newly created ones manually to map if not found by source check (since source didn't have them)
                 for c_name in cats_to_create:
                        # Fetch ID
                        mat_cat = db.query(ActivoCategoria).filter(ActivoCategoria.empresa_id == target_empresa_id, ActivoCategoria.nombre == c_name).first()
                        if mat_cat: map_cats[c_name] = mat_cat.id

             _upsert_manual_seguro(db, ActivoFijo, 'activos', 'codigo', activos_data, target_empresa_id, user_id,
                                   id_maps={'categoria_id': map_cats, 'responsable_id': map_terceros, 'centro_costo_id': map_ccs})

        # --- COTIZACIONES ---
        cotizaciones_data = backup_data.get("cotizaciones", {})
        if cotizaciones_data and "cotizaciones" in cotizaciones_data:
            for cotiz_data in cotizaciones_data["cotizaciones"]:
                # Mapear dependencias
                tercero_id = map_terceros.get(cotiz_data.get("tercero_nit"))
                bodega_id = None
                if cotiz_data.get("bodega_nombre"):
                    bodega_id = map_bodegas.get(cotiz_data["bodega_nombre"])
                
                usuario_id_cotiz = user_id  # Por defecto usar el usuario actual
                if cotiz_data.get("usuario_email"):
                    usuario_db = db.query(Usuario).filter(Usuario.email == cotiz_data["usuario_email"]).first()
                    if usuario_db:
                        usuario_id_cotiz = usuario_db.id

                # Verificar si la cotización ya existe
                existing_cotiz = db.query(Cotizacion).filter(
                    Cotizacion.empresa_id == target_empresa_id,
                    Cotizacion.numero == cotiz_data["numero"]
                ).first()

                if existing_cotiz:
                    # Actualizar cotización existente
                    cotizacion = existing_cotiz
                    # Limpiar detalles existentes
                    db.query(CotizacionDetalle).filter(CotizacionDetalle.cotizacion_id == cotizacion.id).delete()
                else:
                    # Crear nueva cotización
                    cotizacion = Cotizacion(
                        empresa_id=target_empresa_id,
                        numero=cotiz_data["numero"]
                    )
                    db.add(cotizacion)

                # Actualizar campos de la cotización
                for field in ['fecha', 'fecha_vencimiento', 'estado', 'observaciones', 'total_estimado']:
                    if field in cotiz_data:
                        if field in ['fecha', 'fecha_vencimiento'] and cotiz_data[field]:
                            try:
                                setattr(cotizacion, field, datetime.fromisoformat(cotiz_data[field]).date())
                            except:
                                pass
                        else:
                            setattr(cotizacion, field, cotiz_data[field])

                cotizacion.tercero_id = tercero_id
                cotizacion.bodega_id = bodega_id
                cotizacion.usuario_id = usuario_id_cotiz

                db.flush()  # Para obtener el ID de la cotización

                # Restaurar detalles
                for detalle_data in cotiz_data.get("detalles", []):
                    producto_id = map_productos.get(detalle_data.get("producto_codigo"))
                    if producto_id:
                        detalle = CotizacionDetalle(
                            cotizacion_id=cotizacion.id,
                            producto_id=producto_id,
                            cantidad=detalle_data.get("cantidad", 0),
                            precio_unitario=detalle_data.get("precio_unitario", 0),
                            cantidad_facturada=detalle_data.get("cantidad_facturada", 0)
                        )
                        db.add(detalle)

            resumen["acciones_realizadas"].append(f"📋 Cotizaciones restauradas: {len(cotizaciones_data['cotizaciones'])} cotizaciones procesadas")

        db.flush()

        # --- PRODUCCIÓN ---
        produccion_data = backup_data.get("produccion", {})
        if produccion_data:
            # 1. Restaurar Configuración de Producción
            if "configuracion" in produccion_data:
                config_data = produccion_data["configuracion"]
                prod_config = db.query(ConfiguracionProduccion).filter(ConfiguracionProduccion.empresa_id == target_empresa_id).first()
                if not prod_config:
                    prod_config = ConfiguracionProduccion(empresa_id=target_empresa_id)
                    db.add(prod_config)
                
                # Mapear tipos de documento
                map_tipos_doc = _get_id_translation_map(db, TipoDocumento, 'codigo', maestros_src, target_empresa_id)
                if config_data.get("tipo_documento_orden_codigo"):
                    prod_config.tipo_documento_orden_id = map_tipos_doc.get(config_data["tipo_documento_orden_codigo"])
                if config_data.get("tipo_documento_anulacion_codigo"):
                    prod_config.tipo_documento_anulacion_id = map_tipos_doc.get(config_data["tipo_documento_anulacion_codigo"])
                if config_data.get("tipo_documento_consumo_codigo"):
                    prod_config.tipo_documento_consumo_id = map_tipos_doc.get(config_data["tipo_documento_consumo_codigo"])
                if config_data.get("tipo_documento_entrada_pt_codigo"):
                    prod_config.tipo_documento_entrada_pt_id = map_tipos_doc.get(config_data["tipo_documento_entrada_pt_codigo"])
                
                db.flush()

            # 2. Restaurar Recetas
            if "recetas" in produccion_data:
                for receta_data in produccion_data["recetas"]:
                    producto_id = map_productos.get(receta_data.get("producto_codigo"))
                    if not producto_id:
                        continue  # Skip si no existe el producto

                    # Verificar si la receta ya existe
                    existing_receta = db.query(Receta).filter(
                        Receta.empresa_id == target_empresa_id,
                        Receta.nombre == receta_data["nombre"]
                    ).first()

                    if existing_receta:
                        receta = existing_receta
                        # Limpiar detalles y recursos existentes
                        db.query(RecetaDetalle).filter(RecetaDetalle.receta_id == receta.id).delete()
                        db.query(RecetaRecurso).filter(RecetaRecurso.receta_id == receta.id).delete()
                    else:
                        receta = Receta(
                            empresa_id=target_empresa_id,
                            nombre=receta_data["nombre"]
                        )
                        db.add(receta)

                    # Actualizar campos
                    receta.producto_id = producto_id
                    receta.descripcion = receta_data.get("descripcion")
                    receta.cantidad_base = receta_data.get("cantidad_base", 1.0)
                    receta.activa = receta_data.get("activa", True)

                    db.flush()

                    # Restaurar detalles (insumos)
                    for detalle_data in receta_data.get("detalles", []):
                        insumo_id = map_productos.get(detalle_data.get("insumo_codigo"))
                        if insumo_id:
                            detalle = RecetaDetalle(
                                receta_id=receta.id,
                                insumo_id=insumo_id,
                                cantidad=detalle_data.get("cantidad", 0)
                            )
                            db.add(detalle)

                    # Restaurar recursos
                    for recurso_data in receta_data.get("recursos", []):
                        cuenta_id = None
                        if recurso_data.get("cuenta_contable_codigo"):
                            cuenta_id = map_cuentas.get(recurso_data["cuenta_contable_codigo"])
                        
                        recurso = RecetaRecurso(
                            receta_id=receta.id,
                            descripcion=recurso_data.get("descripcion", ""),
                            tipo=recurso_data.get("tipo", "MOD"),
                            costo_estimado=recurso_data.get("costo_estimado", 0),
                            cuenta_contable_id=cuenta_id
                        )
                        db.add(recurso)

            # 3. Restaurar Órdenes de Producción
            if "ordenes" in produccion_data:
                for orden_data in produccion_data["ordenes"]:
                    producto_id = map_productos.get(orden_data.get("producto_codigo"))
                    bodega_destino_id = map_bodegas.get(orden_data.get("bodega_destino_nombre"))
                    
                    if not producto_id or not bodega_destino_id:
                        continue  # Skip si faltan dependencias críticas

                    # Buscar receta por nombre si existe
                    receta_id = None
                    if orden_data.get("receta_nombre"):
                        receta = db.query(Receta).filter(
                            Receta.empresa_id == target_empresa_id,
                            Receta.nombre == orden_data["receta_nombre"]
                        ).first()
                        if receta:
                            receta_id = receta.id

                    # Verificar si la orden ya existe
                    existing_orden = db.query(OrdenProduccion).filter(
                        OrdenProduccion.empresa_id == target_empresa_id,
                        OrdenProduccion.numero_orden == orden_data["numero_orden"]
                    ).first()

                    if existing_orden:
                        orden = existing_orden
                        # Limpiar insumos y recursos existentes
                        db.query(OrdenProduccionInsumo).filter(OrdenProduccionInsumo.orden_id == orden.id).delete()
                        db.query(OrdenProduccionRecurso).filter(OrdenProduccionRecurso.orden_id == orden.id).delete()
                    else:
                        orden = OrdenProduccion(
                            empresa_id=target_empresa_id,
                            numero_orden=orden_data["numero_orden"]
                        )
                        db.add(orden)

                    # Actualizar campos
                    orden.producto_id = producto_id
                    orden.receta_id = receta_id
                    orden.bodega_destino_id = bodega_destino_id
                    orden.cantidad_planeada = orden_data.get("cantidad_planeada", 0)
                    orden.cantidad_real = orden_data.get("cantidad_real", 0)
                    orden.estado = orden_data.get("estado", "PLANIFICADA")
                    orden.observaciones = orden_data.get("observaciones")
                    orden.archivada = orden_data.get("archivada", False)
                    orden.motivo_anulacion = orden_data.get("motivo_anulacion")
                    
                    # Fechas
                    if orden_data.get("fecha_inicio"):
                        try:
                            orden.fecha_inicio = datetime.fromisoformat(orden_data["fecha_inicio"]).date()
                        except:
                            pass
                    if orden_data.get("fecha_fin"):
                        try:
                            orden.fecha_fin = datetime.fromisoformat(orden_data["fecha_fin"]).date()
                        except:
                            pass

                    # Costos
                    orden.costo_total_mp = orden_data.get("costo_total_mp", 0)
                    orden.costo_total_mod = orden_data.get("costo_total_mod", 0)
                    orden.costo_total_cif = orden_data.get("costo_total_cif", 0)
                    orden.costo_unitario_final = orden_data.get("costo_unitario_final", 0)

                    db.flush()

                    # Restaurar insumos consumidos
                    for insumo_data in orden_data.get("insumos", []):
                        insumo_id = map_productos.get(insumo_data.get("insumo_codigo"))
                        bodega_origen_id = map_bodegas.get(insumo_data.get("bodega_origen_nombre"))
                        
                        if insumo_id and bodega_origen_id:
                            insumo = OrdenProduccionInsumo(
                                orden_id=orden.id,
                                insumo_id=insumo_id,
                                bodega_origen_id=bodega_origen_id,
                                cantidad=insumo_data.get("cantidad", 0),
                                costo_unitario_historico=insumo_data.get("costo_unitario_historico", 0),
                                costo_total=insumo_data.get("costo_total", 0)
                            )
                            if insumo_data.get("fecha_despacho"):
                                try:
                                    insumo.fecha_despacho = datetime.fromisoformat(insumo_data["fecha_despacho"])
                                except:
                                    pass
                            db.add(insumo)

                    # Restaurar recursos utilizados
                    for recurso_data in orden_data.get("recursos", []):
                        recurso = OrdenProduccionRecurso(
                            orden_id=orden.id,
                            descripcion=recurso_data.get("descripcion", ""),
                            tipo=recurso_data.get("tipo", "MOD"),
                            valor=recurso_data.get("valor", 0)
                        )
                        if recurso_data.get("fecha_registro"):
                            try:
                                recurso.fecha_registro = datetime.fromisoformat(recurso_data["fecha_registro"])
                            except:
                                pass
                        db.add(recurso)

            # Contar elementos restaurados para el resumen
            recetas_count = len(produccion_data.get("recetas", []))
            ordenes_count = len(produccion_data.get("ordenes", []))
            if recetas_count > 0 or ordenes_count > 0:
                resumen["acciones_realizadas"].append(f"🏭 Producción restaurada: {recetas_count} recetas, {ordenes_count} órdenes de producción")

        db.flush()

        # --- CONCILIACIÓN BANCARIA ---
        conciliacion_data = backup_data.get("conciliacion_bancaria", {})
        if conciliacion_data:
            # 1. Restaurar Configuraciones de Importación
            map_import_configs = {} # Mapa OldID -> NewID
            
            if "configuraciones_importacion" in conciliacion_data:
                for config_data in conciliacion_data["configuraciones_importacion"]:
                    bank_id = map_terceros.get(config_data.get("bank_nit"))
                    creator_id = user_id  # Por defecto usar el usuario actual
                    updater_id = user_id
                    
                    if config_data.get("creator_email"):
                        creator = db.query(Usuario).filter(Usuario.email == config_data["creator_email"]).first()
                        if creator:
                            creator_id = creator.id
                    
                    if config_data.get("updater_email"):
                        updater = db.query(Usuario).filter(Usuario.email == config_data["updater_email"]).first()
                        if updater:
                            updater_id = updater.id

                    # Verificar si la configuración ya existe
                    existing_config = db.query(ImportConfig).filter(
                        ImportConfig.empresa_id == target_empresa_id,
                        ImportConfig.name == config_data["name"]
                    ).first()

                    if existing_config:
                        config = existing_config
                    else:
                        config = ImportConfig(
                            empresa_id=target_empresa_id,
                            name=config_data["name"]
                        )
                        db.add(config)

                    # Actualizar campos
                    config.bank_id = bank_id
                    config.file_format = config_data.get("file_format", "CSV")
                    config.delimiter = config_data.get("delimiter", ",")
                    config.date_format = config_data.get("date_format", "%Y-%m-%d")
                    config.field_mapping = config_data.get("field_mapping", {})
                    config.header_rows = config_data.get("header_rows", 1)
                    config.is_active = config_data.get("is_active", True)
                    config.created_by = creator_id
                    config.updated_by = updater_id
                    
                    db.flush() # Importante: Generar ID
                    
                    # Guardar mapeo si tiene ID origen (para ImportSession)
                    if "id" in config_data:
                        map_import_configs[str(config_data["id"])] = config.id
                        
            # 2. Restaurar Configuraciones Contables
            if "configuraciones_contables" in conciliacion_data:
                for acc_config_data in conciliacion_data["configuraciones_contables"]:
                    bank_account_id = map_cuentas.get(acc_config_data.get("bank_account_codigo"))
                    if not bank_account_id:
                        continue  # Skip si no existe la cuenta bancaria

                    creator_id = user_id
                    updater_id = user_id
                    
                    if acc_config_data.get("creator_email"):
                        creator = db.query(Usuario).filter(Usuario.email == acc_config_data["creator_email"]).first()
                        if creator:
                            creator_id = creator.id
                    
                    if acc_config_data.get("updater_email"):
                        updater = db.query(Usuario).filter(Usuario.email == acc_config_data["updater_email"]).first()
                        if updater:
                            updater_id = updater.id

                    # Verificar si la configuración ya existe
                    existing_acc_config = db.query(AccountingConfig).filter(
                        AccountingConfig.empresa_id == target_empresa_id,
                        AccountingConfig.bank_account_id == bank_account_id
                    ).first()

                    if existing_acc_config:
                        acc_config = existing_acc_config
                    else:
                        acc_config = AccountingConfig(
                            empresa_id=target_empresa_id,
                            bank_account_id=bank_account_id
                        )
                        db.add(acc_config)

                    # Mapear cuentas contables
                    acc_config.commission_account_id = map_cuentas.get(acc_config_data.get("commission_account_codigo"))
                    acc_config.interest_income_account_id = map_cuentas.get(acc_config_data.get("interest_income_account_codigo"))
                    acc_config.bank_charges_account_id = map_cuentas.get(acc_config_data.get("bank_charges_account_codigo"))
                    acc_config.adjustment_account_id = map_cuentas.get(acc_config_data.get("adjustment_account_codigo"))
                    acc_config.default_cost_center_id = map_ccs.get(acc_config_data.get("default_cost_center_codigo"))
                    acc_config.is_active = acc_config_data.get("is_active", True)
                    acc_config.created_by = creator_id
                    acc_config.updated_by = updater_id

            # 3. Restaurar Sesiones de Importación
            if "sesiones_importacion" in conciliacion_data:
                for session_data in conciliacion_data["sesiones_importacion"]:
                    bank_account_id = map_cuentas.get(session_data.get("bank_account_codigo"))
                    user_session_id = user_id
                    
                    if session_data.get("user_email"):
                        user_session = db.query(Usuario).filter(Usuario.email == session_data["user_email"]).first()
                        if user_session:
                            user_session_id = user_session.id
                    
                    # Mapear import_config_id usando el mapa generado
                    import_config_id = None
                    if session_data.get("import_config_id"):
                         import_config_id = map_import_configs.get(str(session_data["import_config_id"]))

                    # Verificar si la sesión ya existe
                    existing_session = db.query(ImportSession).filter(
                        ImportSession.id == session_data["id"]
                    ).first()

                    if not existing_session and bank_account_id:
                        session = ImportSession(
                            id=session_data["id"],
                            empresa_id=target_empresa_id,
                            bank_account_id=bank_account_id,
                            file_name=session_data.get("file_name", ""),
                            file_hash=session_data.get("file_hash", ""),
                            import_config_id=import_config_id,
                            total_movements=session_data.get("total_movements", 0),
                            successful_imports=session_data.get("successful_imports", 0),
                            errors=session_data.get("errors"),
                            user_id=user_session_id,
                            status=session_data.get("status", "COMPLETED")
                        )
                        if session_data.get("import_date"):
                            try:
                                session.import_date = datetime.fromisoformat(session_data["import_date"])
                            except:
                                pass
                        db.add(session)

            # 4. Restaurar Movimientos Bancarios
            if "movimientos_bancarios" in conciliacion_data:
                for movement_data in conciliacion_data["movimientos_bancarios"]:
                    bank_account_id = map_cuentas.get(movement_data.get("bank_account_codigo"))
                    if not bank_account_id:
                        continue

                    # Los movimientos bancarios normalmente no se duplican por ID, 
                    # pero podemos verificar por combinación de campos únicos
                    existing_movement = db.query(BankMovement).filter(
                        BankMovement.empresa_id == target_empresa_id,
                        BankMovement.import_session_id == movement_data.get("import_session_id"),
                        BankMovement.reference == movement_data.get("reference"),
                        BankMovement.amount == movement_data.get("amount")
                    ).first()

                    if not existing_movement:
                        movement = BankMovement(
                            empresa_id=target_empresa_id,
                            import_session_id=movement_data.get("import_session_id"),
                            bank_account_id=bank_account_id,
                            amount=movement_data.get("amount", 0),
                            description=movement_data.get("description", ""),
                            reference=movement_data.get("reference"),
                            transaction_type=movement_data.get("transaction_type"),
                            balance=movement_data.get("balance"),
                            status=movement_data.get("status", "PENDING")
                        )
                        
                        # Fechas
                        if movement_data.get("transaction_date"):
                            try:
                                movement.transaction_date = datetime.fromisoformat(movement_data["transaction_date"]).date()
                            except:
                                pass
                        if movement_data.get("value_date"):
                            try:
                                movement.value_date = datetime.fromisoformat(movement_data["value_date"]).date()
                            except:
                                pass
                        
                        db.add(movement)

            # 5. Restaurar Conciliaciones y Auditoría
            # Nota: Las conciliaciones y auditoría son más complejas y dependen de movimientos contables existentes
            # Por simplicidad, las omitimos en esta implementación inicial
            # Se pueden agregar en una versión futura si es necesario

            # Contar elementos restaurados para el resumen
            configs_count = len(conciliacion_data.get("configuraciones_importacion", []))
            sessions_count = len(conciliacion_data.get("sesiones_importacion", []))
            movements_count = len(conciliacion_data.get("movimientos_bancarios", []))
            if configs_count > 0 or sessions_count > 0 or movements_count > 0:
                resumen["acciones_realizadas"].append(f"🏦 Conciliación Bancaria restaurada: {configs_count} configuraciones, {sessions_count} sesiones, {movements_count} movimientos")

        db.flush()

        # 7. TRANSACCIONES
        docs_source = backup_data.get("transacciones") or backup_data.get("documentos") or []
        if docs_source:
            map_tipos_final = _get_id_translation_map(db, TipoDocumento, 'codigo', maestros_src, target_empresa_id)
            tipos_db = db.query(TipoDocumento).filter(TipoDocumento.empresa_id == target_empresa_id).all()
            for t in tipos_db: map_tipos_final[t.codigo] = t.id

            existing_docs = db.query(Documento).filter(Documento.empresa_id == target_empresa_id).all()
            map_existing_key_to_obj = {f"{d.tipo_documento_id}-{d.numero}": d for d in existing_docs}
            
            deleted_docs = db.query(DocumentoEliminado).filter(DocumentoEliminado.empresa_id == target_empresa_id).all()
            map_deleted = {f"{d.tipo_documento_id}-{str(d.numero)}": d for d in deleted_docs}

            ids_vivos_en_backup = set()
            creados_count = 0
            actualizados_count = 0
            exorcizados_count = 0
            terceros_afectados = set()

            for doc_data in docs_source:
                tipo_codigo = doc_data.get('tipo_doc_codigo')
                tipo_id = map_tipos_final.get(tipo_codigo)
                if not tipo_id: continue
                
                natural_key = f"{tipo_id}-{str(doc_data['numero'])}"
                
                fantasma = map_deleted.get(natural_key)
                if fantasma:
                    db.delete(fantasma)
                    exorcizados_count += 1

                documento_bd = map_existing_key_to_obj.get(natural_key)
                tercero_id = map_terceros.get(doc_data.get('tercero_nit'))
                if tercero_id: terceros_afectados.add(tercero_id)
                cc_id = map_ccs.get(doc_data.get('centro_costo_codigo'))

                val_anulado = doc_data.get('anulado', False)
                val_estado = 'ANULADO' if val_anulado else 'ACTIVO'
                
                fecha_doc = None
                if doc_data.get('fecha'):
                    try:
                        fecha_doc = datetime.fromisoformat(doc_data['fecha'])
                    except:
                        fecha_doc = datetime.utcnow()
                else:
                    fecha_doc = datetime.utcnow()

                if documento_bd:
                    documento_bd.fecha = fecha_doc
                    documento_bd.beneficiario_id = tercero_id
                    documento_bd.observaciones = doc_data.get('observaciones')
                    documento_bd.anulado = val_anulado
                    documento_bd.estado = val_estado
                    
                    db.query(MovimientoContable).filter(MovimientoContable.documento_id == documento_bd.id).delete()
                    db.query(MovimientoInventario).filter(MovimientoInventario.documento_id == documento_bd.id).delete()
                    actualizados_count += 1
                    ids_vivos_en_backup.add(documento_bd.id)
                else:
                    documento_bd = Documento(
                        empresa_id=target_empresa_id, tipo_documento_id=tipo_id, numero=doc_data['numero'],
                        fecha=fecha_doc, beneficiario_id=tercero_id, centro_costo_id=cc_id,
                        anulado=val_anulado, estado=val_estado,
                        usuario_creador_id=user_id, fecha_operacion=datetime.utcnow()
                    )
                    db.add(documento_bd)
                    db.flush()
                    creados_count += 1
                    ids_vivos_en_backup.add(documento_bd.id)

                for mov in doc_data.get('movimientos_contables', []):
                    cta_id = map_cuentas.get(mov['cuenta_codigo'])
                    prod_id = None
                    if mov.get('producto_codigo'):
                        prod_id = map_productos.get(mov['producto_codigo'])

                    if cta_id:
                        db.add(MovimientoContable(
                            documento_id=documento_bd.id, 
                            cuenta_id=cta_id, 
                            concepto=mov['concepto'], 
                            debito=mov['debito'], 
                            credito=mov['credito'],
                            producto_id=prod_id,
                            cantidad=mov.get('cantidad', 0)
                        ))
                
                for mov_inv in doc_data.get('movimientos_inventario', []):
                    prod_id = map_productos.get(mov_inv['producto_codigo'])
                    bod_id = map_bodegas.get(mov_inv['bodega_nombre'])
                    if prod_id and bod_id:
                        db.add(MovimientoInventario(
                            documento_id=documento_bd.id, producto_id=prod_id, bodega_id=bod_id, 
                            tipo_movimiento=mov_inv['tipo'], cantidad=mov_inv['cantidad'], 
                            costo_unitario=mov_inv['costo_unitario'], costo_total=mov_inv['costo_total'], 
                            fecha=fecha_doc
                        ))
            
            if exorcizados_count > 0:
                resumen["acciones_realizadas"].append(f"👻 EXORCISMO: {exorcizados_count} documentos recuperados.")

            # --- CORRECCIÓN v7.0: Se eliminó el bloque de BORRADO de documentos sobrantes ---
            # Esto evita que se borre el historial existente al importar copias parciales.

            resumen["acciones_realizadas"].append(f"📥 {creados_count} Documentos Creados")
            resumen["acciones_realizadas"].append(f"✏️ {actualizados_count} Documentos Corregidos")

            _reconstruir_saldos_inventario(db, target_empresa_id)
            resumen["acciones_realizadas"].append("📦 Stocks y COSTOS de inventario reconstruidos.")

            if terceros_afectados:
                for tid in terceros_afectados:
                    services_cartera.recalcular_aplicaciones_tercero(db, tercero_id=tid, empresa_id=target_empresa_id)
                resumen["acciones_realizadas"].append(f"💰 Saldos de cartera recalculados para {len(terceros_afectados)} terceros.")

        # --- ATOMICIDAD: EL ÚNICO COMMIT DE TODA LA OPERACIÓN ---
        db.commit()
        
        # Verificar integridad referencial después del commit
        integridad = verificar_integridad_referencial(db, target_empresa_id)
        if not integridad['integridad_valida']:
            resumen["acciones_realizadas"].append(f"⚠️ Advertencias de integridad: {'; '.join(integridad['errores'])}")
        else:
            resumen["acciones_realizadas"].append("✅ Verificación de integridad referencial: OK")
        
        return {"message": "Restauración Protocolo Fusión v7.6 Finalizada - Nuevos módulos incluidos (Datos existentes preservados)", "resumen": resumen}

    except Exception as e:
        # --- ROLLBACK TOTAL ---
        print(f"❌ [ERROR] Error crítico durante restauración para empresa {target_empresa_id}: {str(e)}")
        print(f"📊 [ROLLBACK] Revirtiendo todos los cambios...")
        
        db.rollback()
        
        # Verificar que el rollback fue exitoso
        try:
            # Intentar una consulta simple para verificar que la conexión sigue funcionando
            db.execute(select(func.count()).select_from(Empresa).where(Empresa.id == target_empresa_id))
            print(f"✅ [ROLLBACK] Rollback completado exitosamente")
        except Exception as rollback_error:
            print(f"⚠️ [ROLLBACK] Error durante verificación post-rollback: {str(rollback_error)}")
        
        traceback.print_exc()
        
        # Agregar información del contexto al error
        error_context = {
            "empresa_id": target_empresa_id,
            "user_id": user_id,
            "backup_version": backup_data.get("metadata", {}).get("version_sistema", "unknown"),
            "backup_source": backup_data.get("metadata", {}).get("empresa_id_origen", "unknown")
        }
        
        raise HTTPException(
            status_code=500, 
            detail=f"Error fatal durante restauración (Operación Revertida Completamente): {str(e)}. Contexto: {error_context}"
        )

# =====================================================================================
# AUXILIARES
# =====================================================================================
def _reconstruir_saldos_inventario(db: Session, empresa_id: int):
    productos = db.query(Producto.id).filter(Producto.empresa_id == empresa_id).all()
    prod_ids = [p.id for p in productos]
    if not prod_ids: return

    db.query(StockBodega).filter(StockBodega.producto_id.in_(prod_ids)).delete(synchronize_session=False)
    
    stmt = (
        select(
            MovimientoInventario.producto_id,
            MovimientoInventario.bodega_id,
            func.sum(
                case(
                    (MovimientoInventario.tipo_movimiento.like('SALIDA%'), -MovimientoInventario.cantidad),
                    else_=MovimientoInventario.cantidad
                )
            ).label('nuevo_stock'),
            func.sum(
                case(
                    (MovimientoInventario.tipo_movimiento.like('SALIDA%'), -MovimientoInventario.costo_total),
                    else_=MovimientoInventario.costo_total
                )
            ).label('nuevo_valor_total')
        )
        .join(Producto, MovimientoInventario.producto_id == Producto.id)
        .filter(Producto.empresa_id == empresa_id)
        .group_by(MovimientoInventario.producto_id, MovimientoInventario.bodega_id)
    )
    resultados = db.execute(stmt).all()
    
    nuevos_stocks = []
    global_prod_stats = {} 

    for row in resultados:
        if row.nuevo_stock != 0:
            nuevos_stocks.append(StockBodega(producto_id=row.producto_id, bodega_id=row.bodega_id, stock_actual=row.nuevo_stock))
        
        if row.producto_id not in global_prod_stats:
            global_prod_stats[row.producto_id] = {"qty": 0, "val": 0}
        
        global_prod_stats[row.producto_id]["qty"] += row.nuevo_stock
        global_prod_stats[row.producto_id]["val"] += (row.nuevo_valor_total or 0)

    if nuevos_stocks:
        db.bulk_save_objects(nuevos_stocks)
    
    for pid, stats in global_prod_stats.items():
        qty = stats["qty"]
        val = stats["val"]
        costo_promedio = 0
        if qty > 0:
            costo_promedio = val / qty
        db.query(Producto).filter(Producto.id == pid).update({"costo_promedio": costo_promedio})

def _get_id_translation_map(db, model, natural_key, data_source, target_empresa_id):
    """Crea un mapa de traducción de IDs entre backup y base de datos destino."""
    target_rows = db.query(model.id, getattr(model, natural_key)).filter(model.empresa_id == target_empresa_id).all()
    target_map = {str(getattr(r, natural_key)).strip(): r.id for r in target_rows}
    id_map = target_map.copy() 
    
    # Mapeo mejorado de nombres de tablas a claves JSON
    table_to_json_key = {
        'grupos_inventario': 'grupos',
        'plan_cuentas': 'plan_cuentas',
        'centros_costo': 'centros_costo',
        'tipos_documento': 'tipos_documento',
        'cotizaciones': 'cotizaciones',
        'recetas': 'recetas',
        'ordenes_produccion': 'ordenes',
        'import_configs': 'configuraciones_importacion',
        'import_sessions': 'sesiones_importacion',
        'bank_movements': 'movimientos_bancarios'
    }
    
    json_key = table_to_json_key.get(model.__tablename__, model.__tablename__)
    
    # Buscar en diferentes secciones del backup
    source_rows = []
    if json_key in data_source:
        source_rows = data_source[json_key]
    else:
        # Buscar en subsecciones para módulos especializados
        for section in ['cotizaciones', 'produccion', 'conciliacion_bancaria']:
            if section in data_source and json_key in data_source[section]:
                source_rows = data_source[section][json_key]
                break
    
    # Crear mapeos bidireccionales para mayor robustez
    for row in source_rows:
        if not isinstance(row, dict):
            continue
            
        key_val = str(row.get(natural_key, '')).strip()
        if key_val and key_val in target_map:
            nuevo_id = target_map[key_val]
            
            # Mapear ID original si existe
            old_id = row.get('id')
            if old_id: 
                id_map[str(old_id)] = nuevo_id
            
            # Mapear código si existe y es diferente de natural_key
            codigo = row.get('codigo')
            if codigo and codigo != key_val:
                id_map[str(codigo)] = nuevo_id
                
            # Mapear clave natural
            id_map[str(key_val)] = nuevo_id
            
            # Mapear ID de origen si existe (para compatibilidad)
            if 'id_origen' in row:
                id_map[str(row['id_origen'])] = nuevo_id
                
    return id_map

def verificar_integridad_referencial(db: Session, empresa_id: int) -> dict:
    """Verifica la integridad referencial después de una restauración."""
    errores = []
    
    try:
        # Verificar cotizaciones
        cotizaciones_huerfanas = db.query(Cotizacion).filter(
            Cotizacion.empresa_id == empresa_id,
            Cotizacion.tercero_id.isnot(None)
        ).outerjoin(Tercero, Cotizacion.tercero_id == Tercero.id).filter(
            Tercero.id.is_(None)
        ).count()
        
        if cotizaciones_huerfanas > 0:
            errores.append(f"Cotizaciones con terceros inexistentes: {cotizaciones_huerfanas}")
        
        # Verificar recetas
        recetas_huerfanas = db.query(Receta).filter(
            Receta.empresa_id == empresa_id
        ).outerjoin(Producto, Receta.producto_id == Producto.id).filter(
            Producto.id.is_(None)
        ).count()
        
        if recetas_huerfanas > 0:
            errores.append(f"Recetas con productos inexistentes: {recetas_huerfanas}")
        
        # Verificar configuraciones bancarias
        configs_huerfanas = db.query(AccountingConfig).filter(
            AccountingConfig.empresa_id == empresa_id
        ).outerjoin(PlanCuenta, AccountingConfig.bank_account_id == PlanCuenta.id).filter(
            PlanCuenta.id.is_(None)
        ).count()
        
        if configs_huerfanas > 0:
            errores.append(f"Configuraciones bancarias con cuentas inexistentes: {configs_huerfanas}")
            
    except Exception as e:
        errores.append(f"Error durante verificación: {str(e)}")
    
    return {
        'integridad_valida': len(errores) == 0,
        'errores': errores
    }

def verificar_compatibilidad_version(version_backup: str) -> dict:
    """Verifica la compatibilidad de una versión de backup con el sistema actual."""
    version_actual = "7.6"
    
    # Parsear versiones
    try:
        version_backup_parts = [int(x) for x in version_backup.split('.')]
        version_actual_parts = [int(x) for x in version_actual.split('.')]
    except:
        return {
            'compatible': False,
            'requiere_migracion': False,
            'mensaje': f"Versión de backup inválida: {version_backup}"
        }
    
    # Verificar compatibilidad
    if version_backup_parts[0] < 7:
        return {
            'compatible': False,
            'requiere_migracion': True,
            'mensaje': f"Backup v{version_backup} requiere migración manual. Contacte soporte técnico."
        }
    elif version_backup_parts == version_actual_parts:
        return {
            'compatible': True,
            'requiere_migracion': False,
            'mensaje': f"Backup v{version_backup} es totalmente compatible"
        }
    elif version_backup_parts[0] == version_actual_parts[0] and version_backup_parts[1] <= version_actual_parts[1]:
        return {
            'compatible': True,
            'requiere_migracion': False,
            'mensaje': f"Backup v{version_backup} es compatible con v{version_actual} (compatibilidad hacia atrás)"
        }
    else:
        return {
            'compatible': False,
            'requiere_migracion': False,
            'mensaje': f"Backup v{version_backup} es más nuevo que el sistema v{version_actual}. Actualice el sistema."
        }

def migrar_backup_version(backup_data: dict, version_origen: str, version_destino: str) -> dict:
    """Migra un backup de una versión anterior al formato actual."""
    print(f"🔄 [MIGRATION] Migrando backup de v{version_origen} a v{version_destino}")
    
    # Migración de v7.0-7.5 a v7.6
    if version_origen.startswith("7.") and version_destino == "7.6":
        # Agregar secciones faltantes si no existen
        if "cotizaciones" not in backup_data:
            backup_data["cotizaciones"] = {}
        if "produccion" not in backup_data:
            backup_data["produccion"] = {}
        if "conciliacion_bancaria" not in backup_data:
            backup_data["conciliacion_bancaria"] = {}
        
        # Actualizar metadata
        if "metadata" in backup_data:
            backup_data["metadata"]["version_sistema"] = version_destino
            backup_data["metadata"]["migrado_desde"] = version_origen
        
        print(f"✅ [MIGRATION] Migración completada de v{version_origen} a v{version_destino}")
    
    return backup_data

def _restore_jerarquico(db, model, json_key, parent_field, data_source, target_empresa_id, user_id):
    rows = data_source.get(json_key, [])
    if not rows: return 0
    
    existing = db.query(model).filter(model.empresa_id == target_empresa_id).all()
    exist_map = {str(r.codigo).strip(): r for r in existing}
    
    by_level = {}
    for r in rows:
        lvl = r.get('nivel', 1)
        if lvl not in by_level: by_level[lvl] = []
        by_level[lvl].append(r)
    
    count = 0
    for lvl in sorted(by_level.keys()):
        for item in by_level[lvl]:
            key = str(item.get('codigo')).strip()
            if key not in exist_map:
                new_item = item.copy()
                # CORRECCIÓN COMBINADA: Limpiar campos de auditoría antiguos (Antigravity + Kiro)
                for k in ['id', '_sa_instance_state', 'created_at', 'updated_at']: new_item.pop(k, None)
                
                # ARREGLO KIRO: Validar y corregir foreign keys de usuarios antes de procesar
                for user_field in ['created_by', 'updated_by', 'usuario_creador_id', 'usuario_modificador_id']:
                    if user_field in new_item and new_item[user_field] is not None:
                        # Verificar si el usuario existe, si no, usar el usuario actual
                        user_exists = db.query(Usuario).filter(Usuario.id == new_item[user_field]).first()
                        if not user_exists:
                            new_item[user_field] = user_id
                
                new_item['empresa_id'] = target_empresa_id
                new_item[parent_field] = None 
                
                # ARREGLO COMBINADO: Manejar todos los campos de foreign key a usuarios
                if hasattr(model, 'created_by'): new_item['created_by'] = user_id
                if hasattr(model, 'updated_by'): new_item['updated_by'] = user_id
                obj = model(**new_item)
                db.add(obj)
                exist_map[key] = obj
                count += 1
            else:
                # UPDATE LOGIC: If account exists, check if name needs update (e.g. sanitization fix)
                existing_obj = exist_map[key]
                new_name = item.get('nombre')
                if new_name and existing_obj.nombre != new_name:
                    existing_obj.nombre = new_name
                
                # ARREGLO COMBINADO: Validar campos de usuario en actualizaciones (Kiro + Antigravity)
                for user_field in ['updated_by']:
                    if user_field in item and item[user_field] is not None:
                        user_exists = db.query(Usuario).filter(Usuario.id == item[user_field]).first()
                        if not user_exists:
                            setattr(existing_obj, user_field, user_id)
                        else:
                            setattr(existing_obj, user_field, item[user_field])
                    elif hasattr(model, user_field):
                        # Si no hay valor en item, usar user_id actual (mejora de Antigravity)
                        setattr(existing_obj, user_field, user_id)

    return count

def _upsert_manual_seguro(db, model, json_key, natural_key, data_source, target_empresa_id, user_id, id_maps=None):
    rows = data_source.get(json_key, [])
    if not rows: return 0

    existing_records = db.query(model).filter(model.empresa_id == target_empresa_id).all()
    existing_map = {str(getattr(r, natural_key)).strip(): r for r in existing_records}

    valid_columns = {c.name for c in model.__table__.columns}
    immutable_cols = {'id', 'empresa_id', 'created_at', 'fecha_creacion', 'created_by', 'usuario_creador_id'}
    if natural_key: immutable_cols.add(natural_key)

    count = 0
    for r in rows:
        data = r.copy()
        # CORRECCIÓN: Eliminar updated_by del diccionario origen para evitar FK Error
        for k in ['id', '_sa_instance_state', 'created_at', 'updated_at', 'fecha_creacion', 'updated_by']: data.pop(k, None)
        
        clean_data = {k: v for k, v in data.items() if k in valid_columns}
        
        # ARREGLO: Validar y corregir foreign keys de usuarios antes de procesar
        for user_field in ['created_by', 'updated_by', 'usuario_creador_id', 'usuario_modificador_id']:
            if user_field in clean_data and clean_data[user_field] is not None:
                # Verificar si el usuario existe, si no, usar el usuario actual
                user_exists = db.query(Usuario).filter(Usuario.id == clean_data[user_field]).first()
                if not user_exists:
                    clean_data[user_field] = user_id
        
        if id_maps:
            for field, mapping in id_maps.items():
                old_val = clean_data.get(field)
                mapped_id = None
                
                # 1. Try mapping the primary field (usually an ID)
                if old_val is not None:
                    mapped_id = mapping.get(str(old_val).strip())
                
                # 2. If valid mapping not found, try fallback fields (Code or Name)
                if mapped_id is None:
                    code_field = field.replace('_id', '_codigo')
                    alt_val = r.get(code_field)
                    if alt_val is not None:
                        mapped_id = mapping.get(str(alt_val).strip())
                
                if mapped_id is None:
                     name_field = field.replace('_id', '_nombre')
                     alt_val = r.get(name_field)
                     if alt_val is not None:
                         mapped_id = mapping.get(str(alt_val).strip())

                if mapped_id:
                    clean_data[field] = mapped_id
                else:
                    # If strictly required foreign key and we failed to map, explicitly set None 
                    # (This will cause IntegrityError, but better than silent wrong ID)
                    clean_data[field] = None

        key_val = str(clean_data.get(natural_key)).strip()
        
        if key_val in existing_map:
            obj = existing_map[key_val]
            for k, v in clean_data.items():
                if k not in immutable_cols:
                    setattr(obj, k, v)
            if hasattr(model, 'updated_by'): obj.updated_by = user_id
        else:
            clean_data['empresa_id'] = target_empresa_id
            # ARREGLO: Manejar todos los campos de foreign key a usuarios
            if hasattr(model, 'created_by'): clean_data['created_by'] = user_id
            if hasattr(model, 'updated_by'): clean_data['updated_by'] = user_id
            new_obj = model(**clean_data)
            db.add(new_obj)
            existing_map[key_val] = new_obj
            
        count += 1
    return count

def exportar_datos(db: Session, export_request: schemas_migracion.ExportRequest, empresa_id: int):
    # CORRECCIÓN v6.6: Usamos exclude_none en lugar de exclude_unset y convertimos
    # para asegurar que el diccionario tenga todas las llaves posibles
    filtros = export_request.dict(exclude_none=True)
    return generar_backup_json(db, empresa_id, filtros)

def obtener_modulos_disponibles(db: Session, empresa_id: int):
    """
    Obtiene información sobre módulos disponibles y sus dependencias.
    
    Esta función utiliza el sistema declarativo de módulos para:
    - Validar dependencias de cada módulo
    - Contar registros existentes
    - Determinar disponibilidad para exportación
    
    Returns:
        dict: Información detallada de cada módulo configurado
    """
    modulos_info = {}
    
    for modulo_name, config in MODULOS_ESPECIALIZADOS_CONFIG.items():
        validacion = validar_dependencias_modulo(db, config, empresa_id)
        
        # Contar registros existentes
        count_principales = 0
        for modelo in config.get('modelos_principales', []):
            if hasattr(modelo, 'empresa_id'):
                count_principales += db.query(func.count(modelo.id)).filter(modelo.empresa_id == empresa_id).scalar()
        
        modulos_info[modulo_name] = {
            'descripcion': config['descripcion'],
            'dependencias_validas': validacion['valido'],
            'dependencias_faltantes': validacion['dependencias_faltantes'],
            'registros_existentes': count_principales,
            'disponible': validacion['valido']
        }
    
    return modulos_info

# =====================================================================================
# RESUMEN DE ACTUALIZACIÓN v7.6
# =====================================================================================
"""
ACTUALIZACIÓN DEL SISTEMA DE MIGRACIÓN DE DATOS v7.6

Nuevos módulos agregados:
✅ Cotizaciones - Cotizaciones maestras y detalles con relaciones completas
✅ Producción - Recetas, órdenes, recursos e insumos con configuración
✅ Conciliación Bancaria - Configuraciones, sesiones y movimientos bancarios

Mejoras implementadas:
✅ Sistema declarativo de registro de módulos
✅ Validación automática de dependencias
✅ Verificación de integridad referencial post-restauración
✅ Compatibilidad hacia atrás con versiones anteriores
✅ Migración automática de formatos de backup
✅ Logging mejorado y mensajes de feedback detallados
✅ Interfaz de usuario actualizada con descripciones claras

Características técnicas:
- Mantiene atomicidad total en restauración
- Preserva datos existentes (modo fusión segura)
- Firma digital para validación de integridad
- Mapeo robusto de IDs entre empresas
- Manejo de errores con rollback automático

Para usar los nuevos módulos:
1. Seleccionar en la interfaz de exportación
2. El sistema validará dependencias automáticamente
3. La restauración manejará las relaciones correctamente
4. Verificación de integridad al finalizar
"""