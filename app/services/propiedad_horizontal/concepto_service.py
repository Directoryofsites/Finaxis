from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.models.propiedad_horizontal.concepto import PHConcepto
from app.schemas.propiedad_horizontal.concepto import PHConceptoCreate, PHConceptoUpdate
from fastapi import HTTPException

class PHConceptoService:
    def get_all(self, db: Session, empresa_id: int) -> List[PHConcepto]:
        from app.models.propiedad_horizontal.modulo_contribucion import PHModuloContribucion
        conceptos = db.query(PHConcepto).options(
            joinedload(PHConcepto.cuenta_ingreso),
            joinedload(PHConcepto.cuenta_cxc),
            joinedload(PHConcepto.cuenta_interes),
            joinedload(PHConcepto.modulos)  # Cargar módulos del concepto
        ).filter(PHConcepto.empresa_id == empresa_id, PHConcepto.activo == True).order_by(PHConcepto.orden.asc(), PHConcepto.id.asc()).all()
        
        # Forzar carga de torres de cada módulo dentro de la sesión activa
        for c in conceptos:
            for m in c.modulos:
                _ = m.torres  # lazy load mientras la sesión está abierta
        
        return conceptos

    def get_by_id(self, db: Session, id: int) -> Optional[PHConcepto]:
        return db.query(PHConcepto).filter(PHConcepto.id == id).first()

    def create(self, db: Session, obj_in: PHConceptoCreate, empresa_id: int) -> PHConcepto:
        db_obj = PHConcepto(
            empresa_id=empresa_id,
            nombre=obj_in.nombre,
            cuenta_ingreso_id=obj_in.cuenta_ingreso_id,
            cuenta_cxc_id=obj_in.cuenta_cxc_id,
            cuenta_interes_id=obj_in.cuenta_interes_id,
            cuenta_caja_id=obj_in.cuenta_caja_id,
            usa_coeficiente=obj_in.usa_coeficiente,
            es_fijo=obj_in.es_fijo,
            valor_defecto=obj_in.valor_defecto,
            activo=True
        )
        
        # Asignar Módulos
        if obj_in.modulos_ids:
            from app.models.propiedad_horizontal.modulo_contribucion import PHModuloContribucion
            modulos = db.query(PHModuloContribucion).filter(PHModuloContribucion.id.in_(obj_in.modulos_ids)).all()
            db_obj.modulos = modulos

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: PHConcepto, obj_in: PHConceptoUpdate) -> PHConcepto:
        update_data = obj_in.dict(exclude_unset=True)
        
        # Extraer modulos_ids para manejo manual (no es campo directo)
        if 'modulos_ids' in update_data:
            mod_ids = update_data.pop('modulos_ids')
            if mod_ids is not None:
                from app.models.propiedad_horizontal.modulo_contribucion import PHModuloContribucion
                modulos = db.query(PHModuloContribucion).filter(PHModuloContribucion.id.in_(mod_ids)).all()
                db_obj.modulos = modulos

        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> PHConcepto:
        db_obj = self.get_by_id(db, id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Concepto no encontrado")
        
        # Soft delete
        db_obj.activo = False
        db.add(db_obj)
        db.commit()
        return db_obj

    def reorder_concepts(self, db: Session, empresa_id: int, ids_ordenados: List[int]) -> bool:
        """
        Actualiza el campo 'orden' de los conceptos según la lista recibida.
        """
        for i, concepto_id in enumerate(ids_ordenados):
            db.query(PHConcepto).filter(
                PHConcepto.id == concepto_id, 
                PHConcepto.empresa_id == empresa_id
            ).update({"orden": i + 1})
        
        db.commit()
        return True

service = PHConceptoService()
