from sqlalchemy.orm import Session, joinedload
from app.models.propiedad_horizontal import PHUnidad, PHVehiculo, PHMascota, PHCoeficienteHistorial
from app.schemas.propiedad_horizontal import unidad as schemas
from typing import List, Optional

def get_unidades(db: Session, empresa_id: int, skip: int = 0, limit: int = 100):
    return db.query(PHUnidad).filter(PHUnidad.empresa_id == empresa_id)\
        .options(joinedload(PHUnidad.torre), joinedload(PHUnidad.propietario_principal))\
        .offset(skip).limit(limit).all()

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
            
    db.commit()
    db.refresh(db_unidad)
    return db_unidad

def get_unidad_by_id(db: Session, unidad_id: int, empresa_id: int):
    return db.query(PHUnidad).filter(PHUnidad.id == unidad_id, PHUnidad.empresa_id == empresa_id)\
        .options(joinedload(PHUnidad.vehiculos), joinedload(PHUnidad.mascotas))\
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
            
    db.commit()
    db.refresh(db_unidad)
    return db_unidad

def delete_unidad(db: Session, unidad_id: int, empresa_id: int):
    db_unidad = get_unidad_by_id(db, unidad_id, empresa_id)
    if not db_unidad:
        return False
    
    db.delete(db_unidad)
    db.commit()
    return True
