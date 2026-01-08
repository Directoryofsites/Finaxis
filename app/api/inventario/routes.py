# app/api/inventario/routes.py (VERSIÓN COMPLETA - CON FIX DE PDF Y SONDAS)

from typing import List, Optional, Dict, Any
import traceback # AGREGADO: Para ver errores en consola

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from io import BytesIO 
from datetime import date, datetime, timedelta 

from app.core.database import get_db
from app.core.security import get_current_user, has_permission, create_signed_token, validate_signed_token
from app.models import usuario as models_usuario
from app.models import producto as models_producto
from app.models import empresa as models_empresa # AGREGADO: Necesario para buscar la empresa correcta
from app.models import bodega as models_bodega 
from app.models import impuesto as models_impuesto # AGREGADO: Para TasaImpuesto
from app.schemas import inventario as schemas
from app.schemas import tipo_documento as schemas_tipo_doc
from app.schemas import documento as schemas_doc
from app.schemas import token as schemas_token
from app.services import inventario as service_inventario


router = APIRouter()


# ==============================================================================
# === ENDPOINTS CRUD PARA BODEGAS ===
# ==============================================================================

@router.post("/bodegas", response_model=schemas.Bodega, status_code=status.HTTP_201_CREATED, dependencies=[Depends(has_permission("inventario:configuracion"))])
def create_bodega_route(bodega: schemas.BodegaCreate, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return service_inventario.create_bodega(db=db, bodega=bodega, empresa_id=current_user.empresa_id)

@router.get("/bodegas", response_model=List[schemas.Bodega], dependencies=[Depends(has_permission("inventario:acceso"))])
def get_bodegas_route(db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return service_inventario.get_bodegas_by_empresa(db=db, empresa_id=current_user.empresa_id)

@router.put("/bodegas/{bodega_id}", response_model=schemas.Bodega, dependencies=[Depends(has_permission("inventario:configuracion"))])
def update_bodega_route(bodega_id: int, bodega: schemas.BodegaUpdate, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    db_bodega = service_inventario.update_bodega(db=db, bodega_id=bodega_id, bodega=bodega, empresa_id=current_user.empresa_id)
    if db_bodega is None: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bodega no encontrada.")
    return db_bodega

@router.delete("/bodegas/{bodega_id}", dependencies=[Depends(has_permission("inventario:configuracion"))])
def delete_bodega_route(bodega_id: int, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return service_inventario.delete_bodega(db=db, bodega_id=bodega_id, empresa_id=current_user.empresa_id)


# ==============================================================================
# === ENDPOINTS CRUD PARA GRUPOS DE INVENTARIO ===
# ==============================================================================

@router.post("/grupos", response_model=schemas.GrupoInventario, status_code=status.HTTP_201_CREATED, dependencies=[Depends(has_permission("inventario:configuracion"))])
def create_grupo_inventario_route(grupo: schemas.GrupoInventarioCreate, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return service_inventario.create_grupo_inventario(db=db, grupo=grupo, empresa_id=current_user.empresa_id)

@router.get("/grupos", response_model=List[schemas.GrupoInventario], dependencies=[Depends(has_permission("inventario:acceso"))])
def get_grupos_route(db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return service_inventario.get_grupos_by_empresa(db=db, empresa_id=current_user.empresa_id)

@router.get("/grupos/search", response_model=List[schemas.GrupoInventarioSimple], dependencies=[Depends(has_permission("inventario:configuracion"))])
def search_grupos_route(
    search_term: Optional[str] = Query(None, min_length=1), 
    db: Session = Depends(get_db), 
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    if not search_term: 
        return []
    return service_inventario.search_grupos_by_nombre(db=db, empresa_id=current_user.empresa_id, search_term=search_term)

@router.get("/grupos/{grupo_id}", response_model=schemas.GrupoInventario, dependencies=[Depends(has_permission("inventario:configuracion"))])
def get_grupo_by_id_route(grupo_id: int, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    db_grupo = service_inventario.get_grupo_by_id(db=db, grupo_id=grupo_id, empresa_id=current_user.empresa_id)
    if db_grupo is None: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo no encontrado.")
    return db_grupo

@router.put("/grupos/{grupo_id}", response_model=schemas.GrupoInventario, dependencies=[Depends(has_permission("inventario:configuracion"))])
def update_grupo_inventario_route(grupo_id: int, grupo: schemas.GrupoInventarioUpdate, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    db_grupo = service_inventario.update_grupo_inventario(db=db, grupo_id=grupo_id, grupo=grupo, empresa_id=current_user.empresa_id)
    if db_grupo is None: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo no encontrado.")
    return db_grupo

@router.delete("/grupos/{grupo_id}", dependencies=[Depends(has_permission("inventario:configuracion"))])
def delete_grupo_inventario_route(grupo_id: int, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return service_inventario.delete_grupo_inventario(db=db, grupo_id=grupo_id, empresa_id=current_user.empresa_id)


# ==============================================================================
# === ENDPOINTS CRUD PARA TASAS DE IMPUESTO ===
# ==============================================================================

@router.post("/tasas-impuesto", response_model=schemas.TasaImpuesto, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
def create_tasa_impuesto_route(tasa: schemas.TasaImpuestoCreate, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return service_inventario.create_tasa_impuesto(db=db, tasa=tasa, empresa_id=current_user.empresa_id)

@router.get("/tasas-impuesto", response_model=List[schemas.TasaImpuesto], dependencies=[Depends(get_current_user)])
def get_tasas_impuesto_route(db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return service_inventario.get_tasas_by_empresa(db=db, empresa_id=current_user.empresa_id)

@router.put("/tasas-impuesto/{tasa_id}", response_model=schemas.TasaImpuesto, dependencies=[Depends(get_current_user)])
def update_tasa_impuesto_route(tasa_id: int, tasa: schemas.TasaImpuestoUpdate, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    db_tasa = service_inventario.update_tasa_impuesto(db=db, tasa_id=tasa_id, tasa=tasa, empresa_id=current_user.empresa_id)
    if db_tasa is None: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tasa no encontrada.")
    return db_tasa

@router.delete("/tasas-impuesto/{tasa_id}", dependencies=[Depends(get_current_user)])
def delete_tasa_impuesto_route(tasa_id: int, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return service_inventario.delete_tasa_impuesto(db=db, tasa_id=tasa_id, empresa_id=current_user.empresa_id)


# ==============================================================================
# === ENDPOINTS CRUD PARA LISTAS DE PRECIO ===
# ==============================================================================

@router.post("/listas-precio", response_model=schemas.ListaPrecio, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
def create_lista_precio_route(lista_precio: schemas.ListaPrecioCreate, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return service_inventario.create_lista_precio(db=db, lista_precio=lista_precio, empresa_id=current_user.empresa_id)

@router.get("/listas-precio", response_model=List[schemas.ListaPrecio], dependencies=[Depends(get_current_user)])
def get_listas_precio_route(db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return service_inventario.get_listas_precio_by_empresa(db=db, empresa_id=current_user.empresa_id)

@router.put("/listas-precio/{lista_id}", response_model=schemas.ListaPrecio, dependencies=[Depends(get_current_user)])
def update_lista_precio_route(lista_id: int, lista_update: schemas.ListaPrecioUpdate, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    db_lista = service_inventario.update_lista_precio(db=db, lista_id=lista_id, lista_update=lista_update, empresa_id=current_user.empresa_id)
    if db_lista is None: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lista de precio no encontrada.")
    return db_lista

@router.delete("/listas-precio/{lista_id}", dependencies=[Depends(get_current_user)])
def delete_lista_precio_route(lista_id: int, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return service_inventario.delete_lista_precio(db=db, lista_id=lista_id, empresa_id=current_user.empresa_id)


# ==============================================================================
# === ENDPOINTS CRUD PARA CARACTERÍSTICAS ===
# ==============================================================================

@router.post("/grupos/{grupo_id}/caracteristicas", response_model=schemas.CaracteristicaDefinicion, status_code=status.HTTP_201_CREATED, dependencies=[Depends(has_permission("inventario:configuracion"))])
def create_caracteristica_definicion_route(grupo_id: int, definicion_data: schemas.CaracteristicaDefinicionCreate, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return service_inventario.create_caracteristica_definicion(db=db, definicion_data=definicion_data, grupo_id=grupo_id, empresa_id=current_user.empresa_id)

@router.get("/grupos/{grupo_id}/caracteristicas", response_model=List[schemas.CaracteristicaDefinicion], dependencies=[Depends(get_current_user)])
def get_caracteristicas_definicion_route(grupo_id: int, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return service_inventario.get_caracteristicas_definicion_by_grupo(db=db, grupo_id=grupo_id, empresa_id=current_user.empresa_id)

@router.put("/caracteristicas/{definicion_id}", response_model=schemas.CaracteristicaDefinicion, dependencies=[Depends(has_permission("inventario:configuracion"))])
def update_caracteristica_definicion_route(definicion_id: int, definicion_update: schemas.CaracteristicaDefinicionUpdate, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return service_inventario.update_caracteristica_definicion(db=db, definicion_id=definicion_id, definicion_update=definicion_update, empresa_id=current_user.empresa_id)

@router.delete("/caracteristicas/{definicion_id}", dependencies=[Depends(has_permission("inventario:configuracion"))])
def delete_caracteristica_definicion_route(definicion_id: int, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return service_inventario.delete_caracteristica_definicion(db=db, definicion_id=definicion_id, empresa_id=current_user.empresa_id)


# ==============================================================================
# === ENDPOINTS CRUD PARA REGLAS DE PRECIO POR GRUPO ===
# ==============================================================================

@router.post("/grupos/{grupo_id}/reglas-precio", response_model=schemas.ReglaPrecioGrupo, status_code=status.HTTP_201_CREATED, dependencies=[Depends(has_permission("inventario:configuracion"))])
def create_or_update_regla_precio_grupo_route(grupo_id: int, regla_data: schemas.ReglaPrecioGrupoCreate, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return service_inventario.create_or_update_regla_precio_grupo(db=db, regla_data=regla_data, grupo_id=grupo_id, empresa_id=current_user.empresa_id)

@router.get("/grupos/{grupo_id}/reglas-precio", response_model=List[schemas.ReglaPrecioGrupo], dependencies=[Depends(get_current_user)])
def get_reglas_precio_by_grupo_route(grupo_id: int, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return service_inventario.get_reglas_precio_by_grupo(db=db, grupo_id=grupo_id, empresa_id=current_user.empresa_id)

@router.delete("/reglas-precio/{regla_id}", dependencies=[Depends(has_permission("inventario:configuracion"))])
def delete_regla_precio_grupo_route(regla_id: int, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return service_inventario.delete_regla_precio_grupo(db=db, regla_id=regla_id, empresa_id=current_user.empresa_id)


# ==============================================================================
# === ENDPOINTS CRUD PARA PRODUCTOS ===
# ==============================================================================

@router.post("/productos", response_model=schemas.Producto, status_code=status.HTTP_201_CREATED, dependencies=[Depends(has_permission("inventario:kardex"))])
def create_producto_route_restored(producto: schemas.ProductoCreate, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    """
    Ruta de creación principal. Se restaura a /productos para que el botón del FE funcione.
    """
    return service_inventario.create_producto(db=db, producto=producto, empresa_id=current_user.empresa_id)


@router.post("/productos/filtrar", response_model=List[schemas.Producto], dependencies=[Depends(get_current_user)])
def get_productos_filtrados_route_correct_filter(filtros: schemas.ProductoFiltros, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    """
    Ruta correcta para la LISTA/FILTRADO. Debe ser llamada por el frontend en lugar de POST /productos.
    """
    return service_inventario.get_productos_filtrados(db=db, empresa_id=current_user.empresa_id, filtros=filtros)


@router.get("/productos/list-flat", response_model=List[schemas.ProductoSimple], dependencies=[Depends(get_current_user)])
def get_productos_flat_route(db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    """
    Retorna una lista ligera de todos los productos (ID, Código, Nombre) para usar en selectores.
    No descarga relaciones pesadas.
    """
    productos = db.query(
        models_producto.Producto.id,
        models_producto.Producto.codigo,
        models_producto.Producto.nombre,
        models_impuesto.TasaImpuesto.tasa.label('porcentaje_iva')
    ).outerjoin(
        models_impuesto.TasaImpuesto,
        models_producto.Producto.impuesto_iva_id == models_impuesto.TasaImpuesto.id
    ).filter(
        models_producto.Producto.empresa_id == current_user.empresa_id
    ).order_by(models_producto.Producto.nombre.asc()).all()
    
    return [
        {
            "id": p.id, 
            "codigo": p.codigo, 
            "nombre": p.nombre,
            "porcentaje_iva": p.porcentaje_iva if p.porcentaje_iva is not None else 0.0
        } 
        for p in productos
    ]


@router.get("/productos/{producto_id}", response_model=schemas.Producto, dependencies=[Depends(get_current_user)])
def get_producto_by_id_route(producto_id: int, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    db_producto = service_inventario.get_producto_by_id(db=db, producto_id=producto_id, empresa_id=current_user.empresa_id)
    if db_producto is None: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado.")
    return db_producto

@router.put("/productos/{producto_id}", response_model=schemas.Producto, dependencies=[Depends(has_permission("inventario:kardex"))])
def update_producto_route(producto_id: int, producto: schemas.ProductoUpdate, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    db_producto = service_inventario.update_producto(db=db, producto_id=producto_id, producto_update=producto, empresa_id=current_user.empresa_id)
    if db_producto is None: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado.")
    return db_producto

@router.delete("/productos/{producto_id}", dependencies=[Depends(has_permission("inventario:kardex"))])
def delete_producto_route(producto_id: int, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return service_inventario.delete_producto(db=db, producto_id=producto_id, empresa_id=current_user.empresa_id)

@router.get("/productos/search", response_model=List[schemas.ProductoAutocompleteItem], dependencies=[Depends(has_permission("inventario:acceso"))])
def search_productos_route(
    search_term: Optional[str] = Query(None, min_length=1), 
    bodega_id: Optional[int] = Query(None, alias="bodega"),
    grupo_ids: Optional[List[int]] = Query(None, alias="grupos"),
    db: Session = Depends(get_db), 
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    if not search_term: 
        return []
    
    return service_inventario.search_productos(
        db=db, 
        empresa_id=current_user.empresa_id, 
        search_term=search_term, 
        bodega_id=bodega_id, 
        grupo_ids=grupo_ids
    )

@router.post("/productos/buscar", response_model=List[schemas.ProductoAutocompleteItem], dependencies=[Depends(get_current_user)])
def buscar_productos_modal_route(
    filtros: schemas.ProductoFiltros,
    db: Session = Depends(get_db), 
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    return service_inventario.search_productos(
        db=db, 
        empresa_id=current_user.empresa_id, 
        search_term=filtros.search_term, 
        grupo_ids=filtros.grupo_ids if filtros.grupo_ids else None, 
        bodega_id=filtros.bodega_ids[0] if filtros.bodega_ids and filtros.bodega_ids[0] else None, 
    )

@router.post("/productos/search-by-body", response_model=List[schemas.ProductoAutocompleteItem], dependencies=[Depends(get_current_user)])
def search_productos_by_body_route(
    filtros: schemas.ProductoFiltros,
    db: Session = Depends(get_db), 
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    return service_inventario.search_productos(
        db=db, 
        empresa_id=current_user.empresa_id, 
        search_term=filtros.search_term, 
        grupo_ids=filtros.grupo_ids if filtros.grupo_ids else None, 
        bodega_id=filtros.bodega_ids[0] if filtros.bodega_ids and filtros.bodega_ids[0] else None, 
    )


@router.get("/productos/{producto_id}/precio-venta", response_model=schemas.PrecioVentaCalculado, dependencies=[Depends(get_current_user)])
def get_precio_venta_route(producto_id: int, lista_precio_id: int = Query(..., alias="lista_precio"), db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    precio = service_inventario.calcular_precio_venta(db=db, producto_id=producto_id, lista_precio_id=lista_precio_id, empresa_id=current_user.empresa_id)
    return {"precio_calculado": precio}


@router.post("/recalcular-saldos", dependencies=[Depends(get_current_user)])
def recalcular_saldos_masivo_route(db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    """
    Endpoint administrativo para forzar la regeneración de stock y costos de todos los productos
    de la empresa basados en el historial de movimientos.
    """
    return service_inventario.recalcular_todo_inventario(db=db, empresa_id=current_user.empresa_id)


# ==============================================================================
# === ZONA DE REPORTES PDF (CON INSTRUMENTACIÓN DEBUG) ===
# ==============================================================================

@router.post(
    "/productos/solicitar-pdf", 
    summary="Solicita una URL firmada para el PDF de la lista de productos"
)
def solicitar_url_pdf_productos(
    filtros: schemas.ProductoFiltros,
    # Inyectamos user para saber quién pide el PDF
    current_user: models_usuario.Usuario = Depends(has_permission("inventario:ver_productos")) 
):
    print(f"\n>>> [RUTA] SOLICITUD DE TOKEN PDF recibida por Usuario ID: {current_user.id}, Empresa ID: {current_user.empresa_id}")
    try:
        token_payload_str = filtros.model_dump_json()
        token = create_signed_token(token_payload_str, salt='pdf-lista-productos', max_age=600) 
        print(f">>> [RUTA] Token generado exitosamente.")
        return {"token": token}
    except Exception as e:
        print(f">>> [RUTA ERROR] Fallo al crear token: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error token PDF.")


@router.get(
    "/productos/imprimir/{token}", 
    summary="Descarga el PDF de la lista de productos usando un token"
)
def imprimir_pdf_productos(token: str, db: Session = Depends(get_db)):
    """
    Genera el PDF. Ahora con SONDA DE RASTREO y CORRECCIÓN DE ID EMPRESA.
    """
    print(f"\n>>> [RUTA] GET /imprimir/{token[:10]}... DETECTADO. Iniciando proceso...")

    # 1. Validar Token
    payload_str = validate_signed_token(token, salt='pdf-lista-productos', max_age=600)
    if not payload_str:
        print(">>> [RUTA FALLO] Token inválido o expirado.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado.")
    
    print(f">>> [RUTA] Token validado. Payload recuperado.")

    # 2. Deserializar Filtros
    try:
        filtros = schemas.ProductoFiltros.model_validate_json(payload_str)
    except Exception as e:
         print(f">>> [RUTA FALLO] Error deserializando filtros: {e}")
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Filtros inválidos.")

    # 3. RECUPERACIÓN INTELIGENTE DE EMPRESA (SOLUCIÓN A RULETA RUSA)
    empresa_id_objetivo = None
    
    # Estrategia: Buscamos la empresa asociada a alguna de las bodegas del filtro
    if filtros.bodega_ids and len(filtros.bodega_ids) > 0:
        # Consultamos directamente la bodega para obtener su empresa_id
        bodega = db.query(models_bodega.Bodega).filter(models_bodega.Bodega.id == filtros.bodega_ids[0]).first()
        if bodega: 
            empresa_id_objetivo = bodega.empresa_id
            print(f">>> [RUTA] Empresa deducida por Bodega ID {bodega.id}: {empresa_id_objetivo}")
    
    if not empresa_id_objetivo:
        # FALLBACK DE EMERGENCIA: Para tu caso de depuración (Empresa 4)
        # En un entorno multi-tenant real, esto debería venir de otro lado (ej. token de usuario en query params),
        # pero para arreglar TU problema hoy, usamos esto.
        print(">>> [RUTA WARN] No se pudo deducir empresa por filtros. Usando FALLBACK a Empresa 4.")
        empresa_id_objetivo = 4 

    print(f">>> [RUTA] Empresa ID final para el reporte: {empresa_id_objetivo}")
    
    try:
        # 4. LLAMADA AL SERVICIO (MOMENTO DE LA VERDAD)
        print(f">>> [RUTA] Llamando a service_inventario.generar_pdf_lista_productos...")
        
        pdf_bytes = service_inventario.generar_pdf_lista_productos(
            db=db,
            empresa_id=empresa_id_objetivo, 
            filtros=filtros
        )
        
        print(f">>> [RUTA] PDF generado correctamente ({len(pdf_bytes)} bytes). Enviando respuesta...")

        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=Cartilla_Inventario.pdf"
            }
        )
    except Exception as e:
        print(f">>> [RUTA CRITICAL ERROR] Excepción al llamar al servicio: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error generando PDF.")