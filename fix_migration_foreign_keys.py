#!/usr/bin/env python3
# Script para arreglar el problema de foreign keys en migración

from app.services.migracion import _upsert_manual_seguro
from app.core.database import SessionLocal
from app.models.usuario import Usuario

def patch_upsert_function():
    """
    Parcha la función _upsert_manual_seguro para manejar correctamente 
    los campos created_by y updated_by
    """
    
    # Función parcheada que maneja correctamente los foreign keys de usuarios
    def _upsert_manual_seguro_fixed(db, model, json_key, natural_key, data_source, target_empresa_id, user_id, id_maps=None):
        rows = data_source.get(json_key, [])
        if not rows: return 0

        existing_records = db.query(model).filter(model.empresa_id == target_empresa_id).all()
        existing_map = {str(getattr(r, natural_key)).strip(): r for r in existing_records}

        valid_columns = {c.name for c in model.__table__.columns}
        immutable_cols = {'id', 'empresa_id', 'created_at', 'fecha_creacion', 'created_by', 'usuario_creador_id'}
        if natural_key: immutable_cols.add(natural_key)

        # OBTENER USUARIOS VÁLIDOS EN LA BASE DE DATOS DESTINO
        usuarios_validos = db.query(Usuario.id).all()
        ids_usuarios_validos = {u.id for u in usuarios_validos}
        
        # Usar el primer usuario válido como fallback
        fallback_user_id = min(ids_usuarios_validos) if ids_usuarios_validos else user_id

        count = 0
        for r in rows:
            data = r.copy()
            for k in ['id', '_sa_instance_state', 'created_at', 'updated_at', 'fecha_creacion']: 
                data.pop(k, None)
            
            clean_data = {k: v for k, v in data.items() if k in valid_columns}
            
            # ARREGLAR FOREIGN KEYS DE USUARIOS
            for user_field in ['created_by', 'updated_by', 'usuario_creador_id', 'usuario_modificador_id']:
                if user_field in clean_data:
                    original_user_id = clean_data[user_field]
                    if original_user_id and original_user_id not in ids_usuarios_validos:
                        print(f"⚠️  Corrigiendo {user_field}: {original_user_id} → {fallback_user_id}")
                        clean_data[user_field] = fallback_user_id
            
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
                if hasattr(model, 'created_by'): 
                    clean_data['created_by'] = fallback_user_id
                if hasattr(model, 'updated_by'): 
                    clean_data['updated_by'] = fallback_user_id
                    
                new_obj = model(**clean_data)
                db.add(new_obj)
                existing_map[key_val] = new_obj
                
            count += 1
        return count
    
    # Reemplazar la función original
    import app.services.migracion as migracion_module
    migracion_module._upsert_manual_seguro = _upsert_manual_seguro_fixed
    
    print("✅ Función de migración parcheada para manejar foreign keys de usuarios")

if __name__ == "__main__":
    patch_upsert_function()
    print("🔧 Parche aplicado. Ahora puedes intentar la restauración nuevamente.")