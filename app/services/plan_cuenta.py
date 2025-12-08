from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..models import plan_cuenta as models
from ..models.movimiento_contable import MovimientoContable
from ..models.documento import Documento
from ..schemas import plan_cuenta as schemas
from typing import List, Optional, Set
from sqlalchemy import func

def _validar_y_obtener_padre(db: Session, cuenta_padre_id: int, empresa_id: int) -> models.PlanCuenta:
    """
    Valida que una cuenta padre exista, pertenezca a la empresa y no permita movimientos.
    Si es válida, devuelve el objeto de la cuenta padre.
    """
    if not cuenta_padre_id:
        return None

    db_padre = get_cuenta(db, cuenta_id=cuenta_padre_id, empresa_id=empresa_id)
    
    if not db_padre:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"La cuenta padre con ID {cuenta_padre_id} no existe o no pertenece a esta empresa."
        )
    
    if db_padre.permite_movimiento:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La cuenta padre seleccionada no puede ser una cuenta que permite movimientos."
        )
        
    return db_padre

# app/services/plan_cuenta.py

# ... (código se mantiene idéntico hasta la función create_cuenta) ...

# --- SERVICIOS CRUD REFACTORIZADOS ---

def create_cuenta(db: Session, cuenta: schemas.PlanCuentaCreate, user_id: int):
    """Crea una nueva cuenta, con toda la lógica de validación y negocio centralizada."""
    db_cuenta_by_codigo = get_cuenta_by_codigo(db, codigo=cuenta.codigo, empresa_id=cuenta.empresa_id)
    if db_cuenta_by_codigo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El código de cuenta ya está registrado")

    db_padre = None
    if cuenta.cuenta_padre_id:
        db_padre = _validar_y_obtener_padre(db, cuenta_padre_id=cuenta.cuenta_padre_id, empresa_id=cuenta.empresa_id)

    nivel = db_padre.nivel + 1 if db_padre else 1
    
    # --- FIX DEFINITIVO: Excluir campos calculados/obsoletos del Pydantic ---
    
    # 1. Calculamos la CLASE a partir del código (primer dígito).
    clase = int(cuenta.codigo[0]) if cuenta.codigo and cuenta.codigo[0].isdigit() else 0
    
    # 2. Desempacamos el Pydantic, excluyendo el campo obsoleto ('clase_cuenta') 
    # y los campos que calculamos nosotros ('nivel', 'clase').
    data_to_pass = cuenta.model_dump(
        exclude={'nivel', 'clase_cuenta', 'clase'},
        exclude_none=True
    )
    
    db_cuenta = models.PlanCuenta(
        **data_to_pass,                         # Pasamos los datos limpios restantes
        nivel=nivel,                            # Proporcionamos el 'nivel' correcto
        clase=clase,                            # Proporcionamos el 'clase' correcto (FIX)
        created_by=user_id,
        updated_by=user_id
    )
    
    db.add(db_cuenta)
    db.commit()
    db.refresh(db_cuenta)
    return db_cuenta


def update_cuenta(db: Session, cuenta_id: int, cuenta_update: schemas.PlanCuentaUpdate, empresa_id: int, user_id: int):
    # ... (El resto del código se mantiene igual) ...



    """Actualiza una cuenta existente, con validaciones de negocio."""
    db_cuenta = get_cuenta(db, cuenta_id=cuenta_id, empresa_id=empresa_id)
    if not db_cuenta:
        return None

    if cuenta_update.cuenta_padre_id and cuenta_update.cuenta_padre_id == cuenta_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Una cuenta no puede ser su propia cuenta padre."
        )

    db_padre = None
    if cuenta_update.cuenta_padre_id:
        db_padre = _validar_y_obtener_padre(db, cuenta_padre_id=cuenta_update.cuenta_padre_id, empresa_id=empresa_id)

    update_data = cuenta_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_cuenta, key, value)
    
    if 'cuenta_padre_id' in update_data:
        db_cuenta.nivel = db_padre.nivel + 1 if db_padre else 1
    
    db_cuenta.updated_by = user_id
    
    db.commit()
    db.refresh(db_cuenta)
    return db_cuenta


def delete_cuenta(db: Session, cuenta_id: int, empresa_id: int):
    """
    Elimina una cuenta y sus descendientes de forma recursiva e inteligente.
    Regla: Se borra todo lo que NO tenga movimientos ni dependa de cuentas con movimientos.
    Si la cuenta principal tiene movimientos o hijos con movimientos, se preserva.
    """
    db_cuenta = get_cuenta(db, cuenta_id=cuenta_id, empresa_id=empresa_id)
    if not db_cuenta:
        return None
        
    # Usamos la lógica de análisis para determinar qué se puede borrar y qué no
    ids_a_eliminar, ids_a_conservar = _identificar_cuentas_borrables(db, cuenta_id, empresa_id)
    
    if not ids_a_eliminar:
        # Si no hay nada que borrar (porque todo tiene movimientos), lanzamos error
        # O si la única cuenta a borrar es la propia y tiene movimientos (ya cubierto por la lógica)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="No se puede eliminar la cuenta ni sus subcuentas porque todas tienen movimientos o saldos asociados."
        )

    # Procedemos a borrar
    # Importante: Borrar desde el nivel más profundo hacia arriba para evitar problemas de FK (aunque cascade set null podría ayudar, mejor explícito)
    cuentas_a_borrar = db.query(models.PlanCuenta).filter(
        models.PlanCuenta.id.in_(ids_a_eliminar)
    ).order_by(models.PlanCuenta.nivel.desc()).all()

    count = len(cuentas_a_borrar)
    for cuenta in cuentas_a_borrar:
        db.delete(cuenta)
    
    db.commit()
    
    # Si la cuenta original NO fue borrada (porque se debía conservar), retornamos el objeto
    # para indicar que "algo quedó". Pero el endpoint devuelve 204, así que esto es interno.
    # Si el endpoint espera un return, devolvemos algo.
    if cuenta_id in ids_a_conservar:
        return db_cuenta # La cuenta sigue existiendo
    
    return db_cuenta # Retornamos el objeto borrado (o una referencia) para cumplir con la firma anterior

# --- SERVICIOS DE CONSULTA Y HERRAMIENTAS (SIN CAMBIOS) ---
# (El resto del código es idéntico al anterior y se omite por brevedad)

from ..models.impuesto import TasaImpuesto
from ..models.tipo_documento import TipoDocumento

def _identificar_cuentas_borrables(db: Session, cuenta_id: int, empresa_id: int):
    """
    Retorna una tupla (set_ids_a_eliminar, set_ids_a_conservar)
    analizando la jerarquía desde cuenta_id hacia abajo.
    
    VERSION ROBUSTA (v2):
    No confía en `cuenta_padre_id` para subir en la jerarquía, ya que pueden estar rotos.
    Usa la lógica de PREFIJOS DE CÓDIGO para identificar ancestros.
    
    VERSION ROBUSTA (v3):
    Protege cuentas usadas en tablas de configuración (Impuestos, Tipos Doc, etc.)
    para evitar ForeignKeyViolation.
    """
    todas_las_cuentas_empresa = db.query(models.PlanCuenta).filter(models.PlanCuenta.empresa_id == empresa_id).all()
    cuentas_map = {c.id: c for c in todas_las_cuentas_empresa}
    
    # Mapa inverso: Código -> ID (para buscar ancestros por código)
    codigo_to_id = {c.codigo: c.id for c in todas_las_cuentas_empresa}
    
    if cuenta_id not in cuentas_map:
        return set(), set() # Cuenta no encontrada
        
    cuenta_raiz = cuentas_map[cuenta_id]
    codigo_raiz = str(cuenta_raiz.codigo)
    
    # 1. Identificar todos los descendientes (incluyendo la cuenta misma) usando PREFIJO DE CÓDIGO
    descendientes_ids = set()
    for c in todas_las_cuentas_empresa:
        if str(c.codigo).startswith(codigo_raiz):
            descendientes_ids.add(c.id)
            
    # --- PROTECCIÓN DE CONFIGURACIÓN (FKs) ---
    ids_protegidos = set()
    
    # A. Cuentas con Movimientos
    cuentas_con_movimiento_q = db.query(MovimientoContable.cuenta_id).join(
        Documento, MovimientoContable.documento_id == Documento.id
    ).filter(
        Documento.empresa_id == empresa_id,
        MovimientoContable.cuenta_id.in_(list(descendientes_ids))
    ).distinct().all()
    ids_protegidos.update({item[0] for item in cuentas_con_movimiento_q})
    
    # B. Cuentas usadas en Impuestos (TasaImpuesto)
    # TasaImpuesto usa cuenta_id (venta) y cuenta_iva_descontable_id (compra)
    impuestos_q = db.query(TasaImpuesto.cuenta_id, TasaImpuesto.cuenta_iva_descontable_id).filter(
        TasaImpuesto.empresa_id == empresa_id
    ).all()
    for t in impuestos_q:
        if t.cuenta_id in descendientes_ids: ids_protegidos.add(t.cuenta_id)
        if t.cuenta_iva_descontable_id in descendientes_ids: ids_protegidos.add(t.cuenta_iva_descontable_id)
        
    # C. Cuentas usadas en Tipos de Documento
    # TipoDocumento usa cuenta_debito_cxc_id, cuenta_credito_cxc_id, cuenta_debito_cxp_id, cuenta_credito_cxp_id
    tipos_doc_q = db.query(
        TipoDocumento.cuenta_debito_cxc_id, TipoDocumento.cuenta_credito_cxc_id,
        TipoDocumento.cuenta_debito_cxp_id, TipoDocumento.cuenta_credito_cxp_id
    ).filter(TipoDocumento.empresa_id == empresa_id).all()
    
    for td in tipos_doc_q:
        if td.cuenta_debito_cxc_id in descendientes_ids: ids_protegidos.add(td.cuenta_debito_cxc_id)
        if td.cuenta_credito_cxc_id in descendientes_ids: ids_protegidos.add(td.cuenta_credito_cxc_id)
        if td.cuenta_debito_cxp_id in descendientes_ids: ids_protegidos.add(td.cuenta_debito_cxp_id)
        if td.cuenta_credito_cxp_id in descendientes_ids: ids_protegidos.add(td.cuenta_credito_cxp_id)

    # 3. Identificar cuentas a conservar (las protegidas + sus ancestros)
    cuentas_a_conservar_ids = set(ids_protegidos)
    
    # Para cada cuenta protegida, salvamos a todos sus "padres lógicos" (por código)
    for id_protegido in ids_protegidos:
        cuenta_prot = cuentas_map.get(id_protegido)
        if not cuenta_prot: continue
        
        codigo_actual = str(cuenta_prot.codigo)
        
        # Subimos quitando caracteres hasta llegar a la longitud del código raíz
        while len(codigo_actual) >= len(codigo_raiz):
            if codigo_actual in codigo_to_id:
                ancestor_id = codigo_to_id[codigo_actual]
                if ancestor_id in descendientes_ids: 
                    cuentas_a_conservar_ids.add(ancestor_id)
            codigo_actual = codigo_actual[:-1]
                
    # 4. Las que se pueden borrar son: Todos los descendientes - Las que se deben conservar
    cuentas_a_eliminar_ids = descendientes_ids - cuentas_a_conservar_ids
    
    return cuentas_a_eliminar_ids, cuentas_a_conservar_ids

def analizar_depuracion_jerarquica(db: Session, cuenta_id: int, empresa_id: int):
    # Reutilizamos la lógica centralizada
    ids_a_eliminar, ids_a_conservar = _identificar_cuentas_borrables(db, cuenta_id, empresa_id)
    
    todas_las_cuentas_empresa = db.query(models.PlanCuenta).filter(models.PlanCuenta.empresa_id == empresa_id).all()
    cuentas_map = {c.id: c for c in todas_las_cuentas_empresa}
    
    cuentas_a_eliminar_obj = [
        schemas.CuentaDepurable(id=c.id, codigo=c.codigo, nombre=c.nombre, nivel=c.nivel)
        for c in todas_las_cuentas_empresa if c.id in ids_a_eliminar
    ]
    cuentas_a_eliminar_obj.sort(key=lambda x: x.codigo)
    
    mensaje = f"Análisis completo. Se pueden eliminar {len(cuentas_a_eliminar_obj)} cuentas. Se conservarán {len(ids_a_conservar)} cuentas por tener movimientos o ser padres de cuentas con movimientos."
    
    return schemas.AnalisisDepuracionResponse(
        cuentas_a_eliminar=cuentas_a_eliminar_obj,
        cuentas_a_conservar_conteo=len(ids_a_conservar),
        mensaje=mensaje
    )

def ejecutar_depuracion_jerarquica(db: Session, ids_a_eliminar: List[int], empresa_id: int):
    # ... (código existente sin cambios)
    if not ids_a_eliminar:
        raise HTTPException(status_code=400, detail="No se proporcionaron IDs para eliminar.")
    cuentas_a_borrar = db.query(models.PlanCuenta).filter(
        models.PlanCuenta.id.in_(ids_a_eliminar),
        models.PlanCuenta.empresa_id == empresa_id
    ).order_by(models.PlanCuenta.nivel.desc()).all()
    if len(cuentas_a_borrar) != len(ids_a_eliminar):
        raise HTTPException(status_code=400, detail="Algunas de las cuentas a eliminar no se encontraron o no pertenecen a la empresa.")
    for cuenta in cuentas_a_borrar:
        db.delete(cuenta)
    db.commit()
    return {"message": f"{len(cuentas_a_borrar)} cuentas han sido eliminadas exitosamente."}

def get_cuenta(db: Session, cuenta_id: int, empresa_id: int):
    # ... (código existente sin cambios)
    return db.query(models.PlanCuenta).filter(
        models.PlanCuenta.id == cuenta_id,
        models.PlanCuenta.empresa_id == empresa_id
    ).first()

def get_cuenta_by_codigo(db: Session, codigo: str, empresa_id: int):
    # ... (código existente sin cambios)
    return db.query(models.PlanCuenta).filter(
        models.PlanCuenta.codigo == codigo,
        models.PlanCuenta.empresa_id == empresa_id
    ).first()

def get_cuentas(db: Session, empresa_id: int, skip: int = 0, limit: int = 100) -> List[models.PlanCuenta]:
    # ... (código existente sin cambios)
    return db.query(models.PlanCuenta).filter(
        models.PlanCuenta.empresa_id == empresa_id
    ).order_by(models.PlanCuenta.codigo).offset(skip).limit(limit).all()
    
def get_plan_cuentas_flat(db: Session, empresa_id: int, permite_movimiento: Optional[bool] = None) -> List[schemas.PlanCuentaSimple]:
    """
    Retorna lista plana de cuentas con su saldo actual calculado.
    Saldo = Suma(Débitos) - Suma(Créditos)
    """
    query = db.query(
        models.PlanCuenta,
        func.coalesce(func.sum(MovimientoContable.debito), 0).label("total_debito"),
        func.coalesce(func.sum(MovimientoContable.credito), 0).label("total_credito")
    ).outerjoin(
        MovimientoContable, models.PlanCuenta.id == MovimientoContable.cuenta_id
    ).filter(
        models.PlanCuenta.empresa_id == empresa_id
    )

    if permite_movimiento is not None:
        query = query.filter(models.PlanCuenta.permite_movimiento == permite_movimiento)
    
    results = query.group_by(models.PlanCuenta.id).order_by(models.PlanCuenta.codigo).all()
    
    # Mapeamos a objetos que cumplan con el schema PlanCuentaSimple + saldo
    cuentas_con_saldo = []
    for cuenta, debito, credito in results:
        # Creamos una instancia del schema (o un dict) enriquecido
        saldo = float(debito) - float(credito)
        cuenta_simple = schemas.PlanCuentaSimple(
            id=cuenta.id,
            codigo=cuenta.codigo,
            nombre=cuenta.nombre,
            permite_movimiento=cuenta.permite_movimiento,
            saldo=saldo
        )
        cuentas_con_saldo.append(cuenta_simple)
        
    return cuentas_con_saldo

def has_children(db: Session, cuenta_id: int, empresa_id: int) -> bool:
    # ... (código existente sin cambios)
    return db.query(models.PlanCuenta).filter(
        models.PlanCuenta.cuenta_padre_id == cuenta_id,
        models.PlanCuenta.empresa_id == empresa_id
    ).first() is not None

def has_movimientos(db: Session, cuenta_id: int) -> bool:
    # ... (código existente sin cambios)
    return db.query(MovimientoContable).filter(MovimientoContable.cuenta_id == cuenta_id).first() is not None

def reparar_jerarquia_puc(db: Session, empresa_id: int):
    """
    Recorre todas las cuentas y asigna el cuenta_padre_id correcto
    basándose en la estructura del código.
    Optimizado para O(N) usando diccionario.
    """
    print(f"--- Iniciando reparación de jerarquía para empresa ID: {empresa_id} ---")
    cuentas = db.query(models.PlanCuenta).filter(models.PlanCuenta.empresa_id == empresa_id).all()
    
    if not cuentas:
        print("--- No se encontraron cuentas para reparar. ---")
        return {"message": "No se encontraron cuentas para reparar."}
        
    # Mapa Código -> ID
    # Es vital que los códigos sean strings limpios
    mapa_codigo_id = {str(c.codigo).strip(): c.id for c in cuentas}
    
    updates_count = 0
    
    for cuenta in cuentas:
        codigo_actual = str(cuenta.codigo).strip()
        if len(codigo_actual) <= 1:
            # Las cuentas de 1 dígito (Clases) no tienen padre
            if cuenta.cuenta_padre_id is not None:
                cuenta.cuenta_padre_id = None
                updates_count += 1
            continue
            
        # Buscar el padre "ideal" recortando el código
        # Ej: 111005 -> probamos 11100 (no), 1110 (si)
        padre_encontrado_id = None
        
        # Intentamos encontrar el ancestro más cercano
        # Recortamos de a 1 caracter hasta encontrar un match
        prefijo = codigo_actual[:-1]
        while len(prefijo) > 0:
            if prefijo in mapa_codigo_id:
                padre_encontrado_id = mapa_codigo_id[prefijo]
                break
            prefijo = prefijo[:-1]
            
        # Actualizar si es diferente
        if cuenta.cuenta_padre_id != padre_encontrado_id:
            cuenta.cuenta_padre_id = padre_encontrado_id
            updates_count += 1
            
    if updates_count > 0:
        db.commit()
        print(f"--- Jerarquía reparada. Se actualizaron {updates_count} vínculos. ---")
        return {"message": f"Jerarquía reparada. Se actualizaron {updates_count} vínculos."}
    else:
        print("--- La jerarquía ya era correcta. No se realizaron cambios. ---")
        return {"message": "La jerarquía ya era correcta. No se realizaron cambios."}

# --- IMPORTACIÓN INTELIGENTE ---

def analizar_importacion_puc(db: Session, cuentas_input: List[schemas.ImportarCuentaInput], empresa_id: int):
    # 1. Obtener todas las cuentas existentes de la empresa
    existentes = db.query(models.PlanCuenta.codigo).filter(models.PlanCuenta.empresa_id == empresa_id).all()
    codigos_existentes = {c.codigo for c in existentes}
    
    resultados = []
    nuevas_count = 0
    existentes_count = 0
    
    for c in cuentas_input:
        codigo_limpio = str(c.codigo).strip()
        es_nueva = codigo_limpio not in codigos_existentes
        
        item = schemas.AnalisisImportacionItem(
            codigo=codigo_limpio,
            nombre=c.nombre,
            nivel_calculado=0, # Se recalcula al insertar
            es_nueva=es_nueva,
            permite_movimiento=c.permite_movimiento if c.permite_movimiento is not None else (len(codigo_limpio) > 4),
            razon_rechazo="Código duplicado" if not es_nueva else None
        )
        
        resultados.append(item)
        if es_nueva: nuevas_count += 1
        else: existentes_count += 1
        
    return schemas.AnalisisImportacionResponse(
        cuentas_analizadas=resultados,
        total_nuevas=nuevas_count,
        total_existentes=existentes_count
    )

def importar_cuentas_lote(db: Session, cuentas: List[schemas.ImportarCuentaInput], empresa_id: int, user_id: int):
    # 1. Ordenar por longitud de código para asegurar que se creen primero los padres
    cuentas_ordenadas = sorted(cuentas, key=lambda x: len(str(x.codigo)))
    
    creadas = 0
    
    # Cache local para evitar queries repetidos de padres
    cuentas_db = db.query(models.PlanCuenta).filter(models.PlanCuenta.empresa_id == empresa_id).all()
    mapa_codigo_id = {c.codigo: c.id for c in cuentas_db}
    
    for c in cuentas_ordenadas:
        codigo = str(c.codigo).strip()
        
        if codigo in mapa_codigo_id:
            continue
            
        # Buscar padre en el mapa
        padre_id = None
        prefijo = codigo[:-1]
        while len(prefijo) > 0:
            if prefijo in mapa_codigo_id:
                padre_id = mapa_codigo_id[prefijo]
                break
            prefijo = prefijo[:-1]
            
        # Crear Objeto
        nueva_cuenta = models.PlanCuenta(
            empresa_id=empresa_id,
            codigo=codigo,
            nombre=c.nombre,
            permite_movimiento=c.permite_movimiento if c.permite_movimiento is not None else False,
            cuenta_padre_id=padre_id,
            nivel=0, 
            created_by=user_id,
            updated_by=user_id,
            clase=int(codigo[0]) if codigo and codigo[0].isdigit() else 0
        )
        
        db.add(nueva_cuenta)
        db.flush()
        
        mapa_codigo_id[codigo] = nueva_cuenta.id
        creadas += 1
        
    db.commit()
    
    # Paso final: Reparar jerarquía completa para ajustar niveles
    reparar_jerarquia_puc(db, empresa_id)
    
    return {"message": f"Proceso finalizado. Se crearon {creadas} cuentas nuevas."}