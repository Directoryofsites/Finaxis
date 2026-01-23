from sqlalchemy.orm import Session, joinedload
from app.models.propiedad_horizontal import PHUnidad, PHVehiculo, PHMascota, PHCoeficienteHistorial
from app.schemas.propiedad_horizontal import unidad as schemas
from typing import List, Optional

def get_unidades(db: Session, empresa_id: int, skip: int = 0, limit: int = 100):
    unidades = db.query(PHUnidad).filter(PHUnidad.empresa_id == empresa_id)\
        .options(joinedload(PHUnidad.torre), joinedload(PHUnidad.propietario_principal))\
        .offset(skip).limit(limit).all()
    
    # Manually construct dicts to avoid stale ORM property crash
    results = []
    for u in unidades:
        results.append({
            "id": u.id,
            "empresa_id": u.empresa_id,
            "torre_id": u.torre_id,
            "codigo": u.codigo,
            "tipo": u.tipo,
            "matricula_inmobiliaria": u.matricula_inmobiliaria,
            "area_privada": u.area_privada,
            "coeficiente": u.coeficiente,
            "propietario_principal_id": u.propietario_principal_id,
            "residente_actual_id": u.residente_actual_id,
            "activo": u.activo,
            "observaciones": u.observaciones,
            # Handle computed fields manually
            "torre_nombre": u.torre.nombre if u.torre else None,
            "propietario_nombre": u.propietario_principal.razon_social if u.propietario_principal else None,
            # Nested lists (empty by default for summary view, or can load if needed)
            "vehiculos": u.vehiculos,
            "mascotas": u.mascotas
        })
    return results

# --- TORRES ---
def get_torres(db: Session, empresa_id: int):
    from app.models.propiedad_horizontal import PHTorre
    return db.query(PHTorre).filter(PHTorre.empresa_id == empresa_id).all()

def create_torre(db: Session, torre: schemas.PHTorreCreate, empresa_id: int):
    from app.models.propiedad_horizontal import PHTorre
    db_torre = PHTorre(
        empresa_id=empresa_id,
        nombre=torre.nombre,
        descripcion=torre.descripcion
    )
    db.add(db_torre)
    db.commit()
    db.refresh(db_torre)
    return db_torre

def update_torre(db: Session, torre_id: int, torre: schemas.PHTorreCreate, empresa_id: int):
    from app.models.propiedad_horizontal import PHTorre
    db_torre = db.query(PHTorre).filter(PHTorre.id == torre_id, PHTorre.empresa_id == empresa_id).first()
    if not db_torre:
        return None
    
    db_torre.nombre = torre.nombre
    db_torre.descripcion = torre.descripcion
    db.commit()
    db.refresh(db_torre)
    return db_torre

def delete_torre(db: Session, torre_id: int, empresa_id: int):
    from app.models.propiedad_horizontal import PHTorre
    db_torre = db.query(PHTorre).filter(PHTorre.id == torre_id, PHTorre.empresa_id == empresa_id).first()
    if not db_torre:
        return False
    
    # Optional: Check if used by units? (Foreign key usually protects or sets null depending on config)
    # Assuming DB enforcement or soft handling.
    
    db.delete(db_torre)
    db.commit()
    return True

def crear_unidad(db: Session, unidad: schemas.PHUnidadCreate, empresa_id: int):
    # 1. Crear Unidad base
    db_unidad = PHUnidad(
        empresa_id=empresa_id,
        codigo=unidad.codigo,
        tipo=unidad.tipo,
        torre_id=unidad.torre_id,
        matricula_inmobiliaria=unidad.matricula_inmobiliaria,
        area_privada=unidad.area_privada,
        coeficiente=unidad.coeficiente,
        propietario_principal_id=unidad.propietario_principal_id,
        residente_actual_id=unidad.residente_actual_id,
        observaciones=unidad.observaciones
    )
    db.add(db_unidad)
    db.flush() # Para obtener ID
    
    # 2. Agregar Vehículos
    if unidad.vehiculos:
        for v in unidad.vehiculos:
            db_vehiculo = PHVehiculo(
                unidad_id=db_unidad.id,
                placa=v.placa,
                tipo=v.tipo,
                marca=v.marca,
                color=v.color,
                propietario_nombre=v.propietario_nombre
            )
            db.add(db_vehiculo)
            
    # 3. Agregar Mascotas
    if unidad.mascotas:
        for m in unidad.mascotas:
            db_mascota = PHMascota(
                unidad_id=db_unidad.id,
                nombre=m.nombre,
                especie=m.especie,
                raza=m.raza,
                vacunas_al_dia=m.vacunas_al_dia
            )
            db.add(db_mascota)
            
    # 4. Asignar Módulos de Contribución
    if unidad.modulos_ids:
        from app.models.propiedad_horizontal.modulo_contribucion import PHModuloContribucion
        modulos = db.query(PHModuloContribucion).filter(PHModuloContribucion.id.in_(unidad.modulos_ids)).all()
        db_unidad.modulos_contribucion = modulos
            
    db.commit()
    db.refresh(db_unidad)
    return db_unidad

def get_unidad_by_id(db: Session, unidad_id: int, empresa_id: int):
    return db.query(PHUnidad).filter(PHUnidad.id == unidad_id, PHUnidad.empresa_id == empresa_id)\
        .options(joinedload(PHUnidad.vehiculos), joinedload(PHUnidad.mascotas), joinedload(PHUnidad.modulos_contribucion))\
        .first()

def update_unidad(db: Session, unidad_id: int, unidad_update: schemas.PHUnidadCreate, empresa_id: int, usuario_id: Optional[int] = None):
    db_unidad = get_unidad_by_id(db, unidad_id, empresa_id)
    if not db_unidad:
        return None
    
    # Check for Coefficient Change
    try:
        old_coef = float(db_unidad.coeficiente) if db_unidad.coeficiente else 0.0
        new_coef = float(unidad_update.coeficiente) if unidad_update.coeficiente else 0.0
        
        if abs(old_coef - new_coef) > 0.000001: # Check difference with tolerance
            history = PHCoeficienteHistorial(
                unidad_id=db_unidad.id,
                valor_anterior=old_coef,
                valor_nuevo=new_coef,
                usuario_id=usuario_id,
                motivo=f"Actualización manual"
            )
            db.add(history)
    except Exception as e:
        print(f"Error calculando historial coeficiente: {e}")

    # 1. Update basic fields
    db_unidad.codigo = unidad_update.codigo
    db_unidad.tipo = unidad_update.tipo
    db_unidad.torre_id = unidad_update.torre_id
    db_unidad.matricula_inmobiliaria = unidad_update.matricula_inmobiliaria
    db_unidad.area_privada = unidad_update.area_privada
    db_unidad.coeficiente = unidad_update.coeficiente
    db_unidad.observaciones = unidad_update.observaciones
    db_unidad.propietario_principal_id = unidad_update.propietario_principal_id
    db_unidad.residente_actual_id = unidad_update.residente_actual_id
    
    # 2. Update nested (Simple Strategy: Delete all and recreate)
    # Vehicles
    for v in db_unidad.vehiculos:
        db.delete(v)
    if unidad_update.vehiculos:
        for v in unidad_update.vehiculos:
            new_v = PHVehiculo(
                unidad_id=db_unidad.id,
                placa=v.placa,
                tipo=v.tipo,
                marca=v.marca,
                color=v.color
            )
            db.add(new_v)
            
    # Pets
    for m in db_unidad.mascotas:
        db.delete(m)
    if unidad_update.mascotas:
        for m in unidad_update.mascotas:
            new_m = PHMascota(
                unidad_id=db_unidad.id,
                nombre=m.nombre,
                especie=m.especie,
                raza=m.raza,
                vacunas_al_dia=m.vacunas_al_dia
            )
            db.add(new_m)
            
    # Modules Assignment (Many-to-Many - Replace List)
    if unidad_update.modulos_ids is not None:
        from app.models.propiedad_horizontal.modulo_contribucion import PHModuloContribucion
        modulos = db.query(PHModuloContribucion).filter(PHModuloContribucion.id.in_(unidad_update.modulos_ids)).all()
        db_unidad.modulos_contribucion = modulos
            
    db.commit()
    db.refresh(db_unidad)
    return db_unidad

def delete_unidad(db: Session, unidad_id: int, empresa_id: int):
    db_unidad = get_unidad_by_id(db, unidad_id, empresa_id)
    if not db_unidad:
        return False
    

def get_propietarios_resumen(db: Session, empresa_id: int):
    """
    Retorna una lista consolidada de propietarios (Terceros) que tienen unidades asociadas.
    Incluye el resumen de sus unidades y coeficientes.
    """
    from app.models.tercero import Tercero
    
    # query join units -> owners
    propietarios_query = db.query(Tercero).join(PHUnidad, PHUnidad.propietario_principal_id == Tercero.id)\
        .filter(PHUnidad.empresa_id == empresa_id)\
        .distinct()
        
    resultados = []
    
    for tercero in propietarios_query.all():
        # Get units for this owner
        unidades = db.query(PHUnidad).filter(
            PHUnidad.empresa_id == empresa_id,
            PHUnidad.propietario_principal_id == tercero.id
        ).all()
        
        info_unidades = [{"id": u.id, "codigo": u.codigo} for u in unidades]
        total_coeficiente = sum(float(u.coeficiente) if u.coeficiente else 0 for u in unidades)
        
        resultados.append({
            "id": tercero.id,
            "nombre": tercero.razon_social,
            "documento": f"{tercero.nit}-{tercero.dv}" if tercero.dv else tercero.nit,
            "contacto_telefono": tercero.telefono or "N/A",
            "contacto_email": tercero.email or "N/A",
            "unidades": info_unidades,
            "total_unidades": len(unidades),
            "total_coeficiente": total_coeficiente,
            "es_moroso": False # Placeholder logic for future wallet integration
        })
        
    return resultados

def masive_update_modules(db: Session, mass_update: schemas.PHUnidadMassUpdateModules, empresa_id: int):
    """
    Actualiza masivamente los módulos de contribución para una lista de unidades.
    - add_modules_ids: Módulos a AGREGAR (si no existen)
    - remove_modules_ids: Módulos a REMOVER (si existen)
    """
    from app.models.propiedad_horizontal.modulo_contribucion import PHModuloContribucion
    
    # 1. Validar Módulos
    modulos_to_add = []
    if mass_update.add_modules_ids:
        modulos_to_add = db.query(PHModuloContribucion).filter(
            PHModuloContribucion.id.in_(mass_update.add_modules_ids),
            PHModuloContribucion.empresa_id == empresa_id
        ).all()
        
    modulos_to_remove_ids = set(mass_update.remove_modules_ids)
    
    # 2. Buscar Unidades
    unidades = db.query(PHUnidad).filter(
        PHUnidad.id.in_(mass_update.unidades_ids),
        PHUnidad.empresa_id == empresa_id
    ).all()
    
    count_updated = 0
    
    for unidad in unidades:
        current_modules = {m.id for m in unidad.modulos_contribucion}
        modified = False
        
        # ADD
        for mod in modulos_to_add:
            if mod.id not in current_modules:
                unidad.modulos_contribucion.append(mod)
                modified = True
                
        # REMOVE
        if modulos_to_remove_ids:
            # Rebuild list excluding removed ones
            # (Modifying relationship list in place while iterating can be tricky in some ORMs, using reconstruction)
            new_list = [m for m in unidad.modulos_contribucion if m.id not in modulos_to_remove_ids]
            if len(new_list) != len(unidad.modulos_contribucion):
                unidad.modulos_contribucion = new_list
                modified = True
        
        if modified:
            count_updated += 1
            
    db.commit()
    return count_updated
