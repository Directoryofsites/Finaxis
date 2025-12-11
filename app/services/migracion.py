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
            "version_sistema": "7.5", 
            "empresa_id_origen": empresa_id
        },
        "empresa": {}, "configuracion": {}, "maestros": {}, "inventario": {}, 
        "propiedad_horizontal": {}, "activos_fijos": {}, # <--- NUEVAS SECCIONES
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
        # 1. Configuración
        ph_conf = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == empresa_id).first()
        if ph_conf:
            backup_data["propiedad_horizontal"]["configuracion"] = serialize_model(ph_conf.__dict__)
        
        # 2. Conceptos
        conceptos = db.query(PHConcepto).filter(PHConcepto.empresa_id == empresa_id).all()
        backup_data["propiedad_horizontal"]["conceptos"] = [serialize_model(c.__dict__) for c in conceptos]
        
        # 3. Torres y Unidades
        torres = db.query(PHTorre).filter(PHTorre.empresa_id == empresa_id).all()
        backup_data["propiedad_horizontal"]["torres"] = []
        for t in torres:
            unidades = []
            for u in t.unidades:
                unidades.append({
                    "codigo": u.codigo, "nombre": u.nombre, 
                    "coeficiente": float(u.coeficiente or 0),
                    "propietario_nit": u.propietario.nit if u.propietario else None,
                    "arrendatario_nit": u.arrendatario.nit if u.arrendatario else None
                })
            backup_data["propiedad_horizontal"]["torres"].append({
                "nombre": t.nombre,
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
    
    report = {
        "summary": {}, 
        "conflicts": {"documentos": [], "maestros_faltantes": []}, 
        "sourceEmpresaId": backup_data.get("metadata", {}).get("empresa_id_origen"), 
        "targetEmpresaId": target_empresa_id,
        "integrity_valid": integrity_valid
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

    return report

# =====================================================================================
# 3. MOTOR DE RESTAURACIÓN (ATOMICIDAD TOTAL v7.0 - Modo Fusión Segura)
# =====================================================================================
def ejecutar_restauracion(db: Session, request: schemas_migracion.AnalysisRequest, user_id: int):
    backup_data_wrapper = request.backupData
    target_empresa_id = request.targetEmpresaId
    
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
    resumen = {
        "acciones_realizadas": [],
        "maestros_actualizados": 0,
        "documentos_procesados": 0
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

        # 2. RESTAURAR CUPOS
        if "cupos_adicionales" in backup_data.get("configuracion", {}):
            db.query(CupoAdicional).filter(CupoAdicional.empresa_id == target_empresa_id).delete()
            for c in backup_data["configuracion"]["cupos_adicionales"]:
                db.add(CupoAdicional(empresa_id=target_empresa_id, anio=c["anio"], mes=c["mes"], cantidad_adicional=c["cantidad"]))

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
            map_tipos_final = _get_id_translation_map(db, TipoDocumento, 'codigo', maestros_src, target_empresa_id)
            id_maps_fmt = {"tipo_documento_id": map_tipos_final}
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
                for k, v in conf_data.items():
                    if hasattr(ph_conf, k) and k not in ['id', 'empresa_id']:
                        setattr(ph_conf, k, v)
            
            # Conceptos
            _upsert_manual_seguro(db, PHConcepto, 'conceptos', 'nombre', ph_data, target_empresa_id, user_id, 
                                id_maps={"cuenta_cartera_id": map_cuentas, "cuenta_caja_id": map_cuentas, 
                                        "tipo_documento_id": _get_id_translation_map(db, TipoDocumento, 'codigo', maestros_src, target_empresa_id)})
            
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
                                   id_maps={'cuenta_activo_id': map_cuentas, 'cuenta_depreciacion_id': map_cuentas, 'cuenta_gasto_id': map_cuentas})
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
        return {"message": "Restauración Protocolo Fusión v7.0 Finalizada (Datos existentes preservados)", "resumen": resumen}

    except Exception as e:
        # --- ROLLBACK TOTAL ---
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fatal (Operación Revertida): {str(e)}")

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
    target_rows = db.query(model.id, getattr(model, natural_key)).filter(model.empresa_id == target_empresa_id).all()
    target_map = {str(getattr(r, natural_key)).strip(): r.id for r in target_rows}
    id_map = target_map.copy() 
    json_key = 'grupos' if model.__tablename__ == 'grupos_inventario' else model.__tablename__
    if model.__tablename__ == 'plan_cuentas': json_key = 'plan_cuentas'
    source_rows = data_source.get(json_key, [])
    for row in source_rows:
        key_val = str(row.get(natural_key)).strip()
        if key_val in target_map:
            nuevo_id = target_map[key_val]
            old_id = row.get('id') or row.get('codigo') 
            if old_id: id_map[str(old_id)] = nuevo_id
            id_map[str(key_val)] = nuevo_id
            if 'id_origen' in row:
                id_map[str(row['id_origen'])] = nuevo_id
    return id_map

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
                for k in ['id', '_sa_instance_state', 'created_at']: new_item.pop(k, None)
                new_item['empresa_id'] = target_empresa_id
                new_item[parent_field] = None 
                if hasattr(model, 'created_by'): new_item['created_by'] = user_id
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
                    # db.add(existing_obj) # Not strictly necessary as it's attached to session, but good for clarity

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
        for k in ['id', '_sa_instance_state', 'created_at', 'updated_at', 'fecha_creacion']: data.pop(k, None)
        
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