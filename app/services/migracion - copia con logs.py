from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from datetime import datetime
from fastapi import HTTPException
import traceback

from ..schemas import migracion as schemas_migracion
from ..models import (
    Tercero, PlanCuenta, CentroCosto, TipoDocumento,
    Documento, MovimientoContable, Usuario,
    Bodega, GrupoInventario, TasaImpuesto, Producto, StockBodega, MovimientoInventario
)
from ..services import cartera as services_cartera

def exportar_datos(db: Session, export_request: schemas_migracion.ExportRequest, empresa_id: int):
    paquetes = export_request.paquetes
    backup_data = {
        "exportInfo": {"fecha": datetime.utcnow().isoformat(), "empresaId": empresa_id},
        "terceros": [], "plan_cuentas": [], "centros_costo": [], "tipos_documento": [],
        "documentos": [], "movimientos_contables": [],
        "bodegas": [], "grupos_inventario": [], "tasas_impuesto": [],
        "productos": [], "stock_bodegas": [], "movimientos_inventario": [],
    }

    # --- INICIO DE LA LÓGICA DE EXPORTACIÓN ---

    # 1. Exportar transacciones primero si se solicitan
    if paquetes.transacciones:
        documentos = db.query(Documento).filter(Documento.empresa_id == empresa_id).all()
        backup_data["documentos"] = [d.__dict__ for d in documentos]
        if documentos:
            doc_ids = [d.id for d in documentos]
            movimientos_contables = db.query(MovimientoContable).filter(MovimientoContable.documento_id.in_(doc_ids)).all()
            backup_data["movimientos_contables"] = [m.__dict__ for m in movimientos_contables]
            movimientos_inventario = db.query(MovimientoInventario).filter(MovimientoInventario.documento_id.in_(doc_ids)).all()
            backup_data["movimientos_inventario"] = [mi.__dict__ for mi in movimientos_inventario]

    # 2. Recolectar TODOS los IDs de maestros necesarios de los datos ya empaquetados
    ids_necesarios = {
        'terceros': {d.get('beneficiario_id') for d in backup_data["documentos"] if d.get('beneficiario_id')},
        'plan_cuentas': {m.get('cuenta_id') for m in backup_data["movimientos_contables"] if m.get('cuenta_id')},
        'centros_costo': {d.get('centro_costo_id') for d in backup_data["documentos"] if d.get('centro_costo_id')},
        'tipos_documento': {d.get('tipo_documento_id') for d in backup_data["documentos"] if d.get('tipo_documento_id')},
        'productos': {m.get('producto_id') for m in backup_data["movimientos_contables"] if m.get('producto_id')} | \
                     {mi.get('producto_id') for mi in backup_data["movimientos_inventario"] if mi.get('producto_id')},
        'bodegas': {mi.get('bodega_id') for mi in backup_data["movimientos_inventario"] if mi.get('bodega_id')}
    }

    # 3. Exportar maestros, combinando la selección del usuario con los IDs necesarios
    maestros_map = {
        'terceros': (Tercero, paquetes.maestros.terceros),
        'plan_cuentas': (PlanCuenta, paquetes.maestros.plan_cuentas),
        'centros_costo': (CentroCosto, paquetes.maestros.centros_costo),
        'tipos_documento': (TipoDocumento, paquetes.maestros.tipos_documento),
        'bodegas': (Bodega, paquetes.maestros.bodegas),
        'grupos_inventario': (GrupoInventario, paquetes.maestros.grupos_inventario),
        'tasas_impuesto': (TasaImpuesto, paquetes.maestros.tasas_impuesto),
        'productos': (Producto, paquetes.maestros.productos),
    }

    for key, (model, exportar_todos) in maestros_map.items():
        ids_a_exportar = set(ids_necesarios.get(key, set()))
        
        if exportar_todos:
            items = db.query(model).filter(model.empresa_id == empresa_id).all()
        elif ids_a_exportar:
            items = db.query(model).filter(model.id.in_(list(ids_a_exportar))).all()
        else:
            items = []
        
        backup_data[key] = [item.__dict__ for item in items]

    # 4. Exportar dependencias de segundo nivel como Stock
    if backup_data.get('productos'):
        producto_ids = [p['id'] for p in backup_data['productos']]
        if producto_ids:
            stocks = db.query(StockBodega).filter(StockBodega.producto_id.in_(producto_ids)).all()
            backup_data['stock_bodegas'] = [s.__dict__ for s in stocks]

    # 5. Limpieza final de metadatos de SQLAlchemy
    for key in backup_data:
        if isinstance(backup_data[key], list):
            for item_dict in backup_data[key]:
                item_dict.pop('_sa_instance_state', None)
    
    return backup_data


def analizar_backup(db: Session, analysis_request: schemas_migracion.AnalysisRequest):
    backup_data = analysis_request.backupData
    target_empresa_id = analysis_request.targetEmpresaId
    report = {"summary": {}, "conflicts": {"documentos": [], "maestros_faltantes": []}, "sourceEmpresaId": backup_data.get("exportInfo", {}).get("empresaId"), "targetEmpresaId": target_empresa_id}
    maestros_a_analizar = {'terceros': (Tercero, 'nit'),'plan_cuentas': (PlanCuenta, 'codigo'),'centros_costo': (CentroCosto, 'codigo'),'tipos_documento': (TipoDocumento, 'codigo'),'bodegas': (Bodega, 'nombre'),'grupos_inventario': (GrupoInventario, 'nombre'),'tasas_impuesto': (TasaImpuesto, 'nombre'),'productos': (Producto, 'codigo'),}
    for key, (model, natural_key) in maestros_a_analizar.items():
        if not backup_data.get(key): continue
        source_items = backup_data[key]
        target_rows = db.query(getattr(model, natural_key)).filter(model.empresa_id == target_empresa_id).all()
        target_natural_keys = {str(getattr(row, natural_key)) for row in target_rows}
        a_crear = sum(1 for item in source_items if str(item[natural_key]) not in target_natural_keys)
        coincidencias = len(source_items) - a_crear
        report["summary"][key] = {"total": len(source_items), "a_crear": a_crear, "coincidencias": coincidencias}
    if backup_data.get("documentos"):
        docs_source = backup_data["documentos"]
        target_tipos_doc_rows = db.query(TipoDocumento.id, TipoDocumento.codigo).filter(TipoDocumento.empresa_id == target_empresa_id).all()
        target_tipos_doc_map = {row.codigo: row.id for row in target_tipos_doc_rows}
        source_tipos_doc_map = {item['id']: item['codigo'] for item in backup_data.get('tipos_documento', [])}
        target_docs_rows = db.query(Documento.tipo_documento_id, Documento.numero).filter(Documento.empresa_id == target_empresa_id).all()
        target_docs_set = {f"{row.tipo_documento_id}-{row.numero}" for row in target_docs_rows}
        a_crear, coincidencias = 0, 0
        for doc in docs_source:
            source_tipo_doc_codigo = source_tipos_doc_map.get(doc['tipo_documento_id'])
            target_tipo_doc_id = target_tipos_doc_map.get(source_tipo_doc_codigo)
            if target_tipo_doc_id and f"{target_tipo_doc_id}-{doc['numero']}" in target_docs_set: coincidencias += 1
            else: a_crear += 1
        report["summary"]["documentos"] = {"total": len(docs_source), "a_crear": a_crear, "coincidencias": coincidencias}
    return report

def _get_id_translation_map(db: Session, model, natural_key: str, backup_data: dict, target_empresa_id: int):
    table_name = model.__tablename__
    source_rows = backup_data.get(table_name, [])
    if not source_rows: return {}
    target_rows = db.query(model.id, getattr(model, natural_key)).filter(model.empresa_id == target_empresa_id).all()
    target_map = {str(getattr(row, natural_key)): row.id for row in target_rows}
    id_map = {}
    for row in source_rows:
        old_id = row['id']
        natural_key_value = str(row.get(natural_key))
        if natural_key_value in target_map:
            id_map[old_id] = target_map[natural_key_value]
    return id_map

def _restore_simple_master(db: Session, model, table_name: str, natural_key: str, backup_data: dict, target_empresa_id: int, user_id: int, id_maps: dict = None):
    data = backup_data.get(table_name, [])
    if not data: return 0
    values_to_insert = []
    for row_data in data:
        new_row = row_data.copy()
        for key in ['id', '_sa_instance_state', 'created_at', 'updated_at', 'fecha_creacion', 'fecha_operacion']: new_row.pop(key, None)
        new_row['empresa_id'] = target_empresa_id
        if hasattr(model, 'created_by'): new_row['created_by'] = user_id
        if hasattr(model, 'updated_by'): new_row['updated_by'] = user_id
        if id_maps:
            for fk_field, id_map in id_maps.items():
                old_id = new_row.get(fk_field)
                if old_id is not None: new_row[fk_field] = id_map.get(old_id)
        values_to_insert.append(new_row)
    if not values_to_insert: return 0
    stmt = pg_insert(model).values(values_to_insert).on_conflict_do_nothing(index_elements=['empresa_id', natural_key])
    result = db.execute(stmt)
    return result.rowcount

def _restore_jerarquico(db: Session, model, table_name: str, parent_fk_name: str, backup_data: dict, target_empresa_id: int, user_id: int):
    data = backup_data.get(table_name, [])
    if not data: return 0
    items_por_nivel = {}
    for item in data:
        nivel = item.get('nivel', 1)
        if nivel not in items_por_nivel: items_por_nivel[nivel] = []
        items_por_nivel[nivel].append(item)
    map_old_id_to_new_id, total_creados = {}, 0
    for nivel in sorted(items_por_nivel.keys()):
        items_del_nivel = items_por_nivel[nivel]
        values_to_insert = []
        for item in items_del_nivel:
            old_parent_id = item.get(parent_fk_name)
            new_parent_id = map_old_id_to_new_id.get(old_parent_id) if old_parent_id else None
            new_row = item.copy()
            for key in ['id', '_sa_instance_state', 'created_at', 'updated_at']: new_row.pop(key, None)
            new_row.update({'empresa_id': target_empresa_id, 'created_by': user_id, 'updated_by': user_id, parent_fk_name: new_parent_id})
            values_to_insert.append(new_row)
        if not values_to_insert: continue
        stmt = pg_insert(model).values(values_to_insert).on_conflict_do_nothing(index_elements=['empresa_id', 'codigo'])
        db.execute(stmt)
        db.flush()
        codigos_insertados = [item['codigo'] for item in items_del_nivel]
        items_recien_creados = db.query(model.id, model.codigo).filter(model.empresa_id == target_empresa_id, model.codigo.in_(codigos_insertados)).all()
        map_codigo_a_nuevo_id = {c.codigo: c.id for c in items_recien_creados}
        for item in items_del_nivel:
            old_id, codigo = item['id'], item['codigo']
            if codigo in map_codigo_a_nuevo_id:
                if old_id not in map_old_id_to_new_id:
                    map_old_id_to_new_id[old_id] = map_codigo_a_nuevo_id[codigo]
                    total_creados += 1
    return total_creados

def ejecutar_restauracion(db: Session, request: schemas_migracion.AnalysisRequest, user_id: int):
    backup_data = request.backupData
    target_empresa_id = request.targetEmpresaId
    resumen = {}
    print("\n--- INICIO DE LA MISIÓN DE DIAGNÓSTICO FORENSE ---")
    try:
        # FASE 1: Restaurar maestros basicos
        resumen["terceros_creados"] = _restore_simple_master(db, Tercero, 'terceros', 'nit', backup_data, target_empresa_id, user_id)
        resumen["bodegas_creadas"] = _restore_simple_master(db, Bodega, 'bodegas', 'nombre', backup_data, target_empresa_id, user_id)
        resumen["plan_cuentas_creados"] = _restore_jerarquico(db, PlanCuenta, 'plan_cuentas', 'cuenta_padre_id', backup_data, target_empresa_id, user_id)
        resumen["centros_costo_creados"] = _restore_jerarquico(db, CentroCosto, 'centros_costo', 'centro_costo_padre_id', backup_data, target_empresa_id, user_id)
        db.commit()

        # FASE 2: Construir mapas de traduccion para los maestros basicos
        map_terceros = _get_id_translation_map(db, Tercero, 'nit', backup_data, target_empresa_id)
        map_cuentas = _get_id_translation_map(db, PlanCuenta, 'codigo', backup_data, target_empresa_id)
        map_ccs = _get_id_translation_map(db, CentroCosto, 'codigo', backup_data, target_empresa_id)
        map_bodegas = _get_id_translation_map(db, Bodega, 'nombre', backup_data, target_empresa_id)
        
        # FASE 3: Restaurar maestros dependientes
        id_maps_tipos_doc = {"cuenta_caja_id": map_cuentas, "cuenta_debito_cxc_id": map_cuentas, "cuenta_credito_cxc_id": map_cuentas, "cuenta_debito_cxp_id": map_cuentas, "cuenta_credito_cxp_id": map_cuentas}
        resumen["tipos_documento_creados"] = _restore_simple_master(db, TipoDocumento, 'tipos_documento', 'codigo', backup_data, target_empresa_id, user_id, id_maps=id_maps_tipos_doc)
        id_maps_grupos_inv = {"cuenta_inventario_id": map_cuentas, "cuenta_ingreso_id": map_cuentas, "cuenta_costo_venta_id": map_cuentas}
        resumen["grupos_inventario_creados"] = _restore_simple_master(db, GrupoInventario, 'grupos_inventario', 'nombre', backup_data, target_empresa_id, user_id, id_maps=id_maps_grupos_inv)
        id_maps_tasas_imp = {"cuenta_id": map_cuentas, "cuenta_iva_descontable_id": map_cuentas}
        resumen["tasas_impuesto_creadas"] = _restore_simple_master(db, TasaImpuesto, 'tasas_impuesto', 'nombre', backup_data, target_empresa_id, user_id, id_maps=id_maps_tasas_imp)
        db.commit()

        # FASE 4: Construir mas mapas y restaurar maestros de segundo nivel
        map_tipos_doc = _get_id_translation_map(db, TipoDocumento, 'codigo', backup_data, target_empresa_id)
        map_grupos_inv = _get_id_translation_map(db, GrupoInventario, 'nombre', backup_data, target_empresa_id)
        map_tasas_imp = _get_id_translation_map(db, TasaImpuesto, 'nombre', backup_data, target_empresa_id)
        id_maps_productos = {"grupo_id": map_grupos_inv, "impuesto_iva_id": map_tasas_imp}
        resumen["productos_creados"] = _restore_simple_master(db, Producto, 'productos', 'codigo', backup_data, target_empresa_id, user_id, id_maps=id_maps_productos)
        db.commit()
        
        # FASE 5: Restaurar stock y construir mapa final de productos
        map_productos = _get_id_translation_map(db, Producto, 'codigo', backup_data, target_empresa_id)
        
        print(f"\nSONDA 1: MAPAS DE MAESTROS CARGADOS")
        print(f" - Mapa de Bodegas contiene {len(map_bodegas)} registros.")
        print(f" - Mapa de Productos contiene {len(map_productos)} registros.")
        print(f" - Mapa de Tipos de Doc contiene {len(map_tipos_doc)} registros.")

        # ... (código de stock sin cambios) ...
        stocks_a_crear = []
        for stock_data in backup_data.get('stock_bodegas', []):
            new_producto_id = map_productos.get(stock_data.get('producto_id'))
            new_bodega_id = map_bodegas.get(stock_data.get('bodega_id'))
            if new_producto_id and new_bodega_id: stocks_a_crear.append({"producto_id": new_producto_id, "bodega_id": new_bodega_id, "stock_actual": stock_data.get('stock_actual', 0)})
        if stocks_a_crear: db.execute(pg_insert(StockBodega).values(stocks_a_crear).on_conflict_do_nothing(index_elements=['producto_id', 'bodega_id']))
        resumen["stock_bodegas_creados"] = len(stocks_a_crear)

        # FASE 6: Proceso de Documentos
        map_documentos_antiguo_a_nuevo = {}
        documentos_a_insertar, map_old_id_to_doc_data = [], {}

        existing_docs_rows = db.query(Documento.id, Documento.tipo_documento_id, Documento.numero).filter(Documento.empresa_id == target_empresa_id).all()
        map_existing_natural_key_to_new_id = {f"{row.tipo_documento_id}-{row.numero}": row.id for row in existing_docs_rows}
        print(f"\nSONDA 2: Documentos preexistentes en la empresa destino: {len(map_existing_natural_key_to_new_id)} encontrados.")

        for doc_data in backup_data.get('documentos', []):
            old_doc_id = doc_data['id']
            target_tipo_doc_id = map_tipos_doc.get(doc_data['tipo_documento_id'])
            
            if not target_tipo_doc_id: continue

            natural_key = f"{target_tipo_doc_id}-{doc_data['numero']}"

            if natural_key in map_existing_natural_key_to_new_id:
                new_id = map_existing_natural_key_to_new_id[natural_key]
                map_documentos_antiguo_a_nuevo[old_doc_id] = new_id
            else:
                new_beneficiario_id = map_terceros.get(doc_data.get('beneficiario_id'))
                doc_insert_data = {
                    "empresa_id": target_empresa_id, "tipo_documento_id": target_tipo_doc_id, "numero": doc_data['numero'], "fecha": doc_data['fecha'], "fecha_vencimiento": doc_data.get('fecha_vencimiento'), "beneficiario_id": new_beneficiario_id, "centro_costo_id": map_ccs.get(doc_data.get('centro_costo_id')), "anulado": doc_data.get('anulado', False), "estado": doc_data.get('estado', 'ACTIVO'), "usuario_creador_id": user_id, "fecha_operacion": datetime.utcnow()
                }
                documentos_a_insertar.append(doc_insert_data)
                map_old_id_to_doc_data[old_doc_id] = doc_insert_data
        
        print(f"SONDA 3: Procesamiento de documentos del backup finalizado.")
        print(f" - Documentos a crear: {len(documentos_a_insertar)}")
        print(f" - Documentos existentes mapeados: {len(map_documentos_antiguo_a_nuevo)}")

        if documentos_a_insertar:
            db.bulk_insert_mappings(Documento, documentos_a_insertar)
            db.commit()
            
            map_natural_key_to_new_id_actualizada = {f"{d.tipo_documento_id}-{d.numero}": d.id for d in db.query(Documento.id, Documento.tipo_documento_id, Documento.numero).filter(Documento.empresa_id == target_empresa_id).all()}
            for old_id, doc_data in map_old_id_to_doc_data.items():
                natural_key = f"{doc_data['tipo_documento_id']}-{doc_data['numero']}"
                new_id = map_natural_key_to_new_id_actualizada.get(natural_key)
                if new_id: map_documentos_antiguo_a_nuevo[old_id] = new_id
        
        resumen["documentos_creados"] = len(documentos_a_insertar)
        print(f"SONDA 4: Creación de nuevos docs y actualización de mapa finalizada.")
        print(f" - Tamaño final del mapa de traducción de documentos: {len(map_documentos_antiguo_a_nuevo)}")

        # FASE 7: Restaurar movimientos
        movimientos_contables_a_crear = []
        for mov_data in backup_data.get('movimientos_contables', []):
            # ... (código de contabilidad sin cambios) ...
            new_doc_id = map_documentos_antiguo_a_nuevo.get(mov_data.get('documento_id'))
            new_cuenta_id = map_cuentas.get(mov_data.get('cuenta_id'))
            if not new_doc_id or not new_cuenta_id: continue
            movimientos_contables_a_crear.append({"documento_id": new_doc_id, "cuenta_id": new_cuenta_id, "centro_costo_id": map_ccs.get(mov_data.get('centro_costo_id')), "producto_id": map_productos.get(mov_data.get('producto_id')), "concepto": mov_data.get('concepto'), "debito": mov_data.get('debito', 0), "credito": mov_data.get('credito', 0)})

        movimientos_inv_a_crear = []
        total_mov_inv_backup = len(backup_data.get('movimientos_inventario', []))
        print(f"\nSONDA 5: INICIANDO PROCESAMIENTO DE {total_mov_inv_backup} MOVIMIENTOS DE INVENTARIO...")

        for mov_inv_data in backup_data.get('movimientos_inventario', []):
            old_doc_id = mov_inv_data.get('documento_id')
            new_doc_id = map_documentos_antiguo_a_nuevo.get(old_doc_id)
            new_producto_id = map_productos.get(mov_inv_data.get('producto_id'))
            new_bodega_id = map_bodegas.get(mov_inv_data.get('bodega_id'))
            
            # --- SONDA DE DIAGNÓSTICO DETALLADO ---
            if not new_doc_id or not new_producto_id or not new_bodega_id:
                print(f"  - ADVERTENCIA: Saltando movimiento de inventario (Doc ID Antiguo: {old_doc_id}) por dependencia faltante:")
                print(f"    - ID Documento: {old_doc_id} -> {'ENCONTRADO' if new_doc_id else 'FALLÓ LA TRADUCCIÓN'}")
                print(f"    - ID Producto: {mov_inv_data.get('producto_id')} -> {'ENCONTRADO' if new_producto_id else 'FALLÓ LA TRADUCCIÓN'}")
                print(f"    - ID Bodega: {mov_inv_data.get('bodega_id')} -> {'ENCONTRADO' if new_bodega_id else 'FALLÓ LA TRADUCCIÓN'}")
                continue
            
            movimientos_inv_a_crear.append({"documento_id": new_doc_id, "producto_id": new_producto_id, "bodega_id": new_bodega_id, "fecha": mov_inv_data.get('fecha'), "tipo_movimiento": mov_inv_data.get('tipo_movimiento'), "cantidad": mov_inv_data.get('cantidad', 0), "costo_unitario": mov_inv_data.get('costo_unitario', 0), "costo_total": mov_inv_data.get('costo_total', 0)})
        
        print(f"SONDA 6: FINALIZADO PROCESAMIENTO DE MOVIMIENTOS DE INVENTARIO.")
        print(f" - Movimientos a crear: {len(movimientos_inv_a_crear)} de {total_mov_inv_backup}")

        if movimientos_contables_a_crear: db.bulk_insert_mappings(MovimientoContable, movimientos_contables_a_crear)
        if movimientos_inv_a_crear: db.bulk_insert_mappings(MovimientoInventario, movimientos_inv_a_crear)
        resumen["movimientos_contables_creados"] = len(movimientos_contables_a_crear)
        resumen["movimientos_inventario_creados"] = len(movimientos_inv_a_crear)
        
        # ... (código de recálculo de cartera sin cambios) ...
        terceros_afectados_ids = set() # Re-inicializar por si acaso
        if terceros_afectados_ids:
            for tercero_id in terceros_afectados_ids:
                try: services_cartera.recalcular_aplicaciones_tercero(db=db, tercero_id=tercero_id, empresa_id=target_empresa_id)
                except Exception as e: print(f"ADVERTENCIA: Falló el recálculo para el tercero ID {tercero_id}: {e}")
            resumen["terceros_recalculados"] = len(terceros_afectados_ids)
        
        db.commit()
        print("\n--- MISIÓN DE DIAGNÓSTICO FORENSE FINALIZADA ---\n")
        return {"message": "Restauración completada con éxito.", "resumen": resumen}
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fatal durante la restauración: {str(e)}")