from sqlalchemy import create_engine, text
from app.core.config import settings

def clean_duplicates():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        print("Buscando duplicados de NIT...")
        # Identificar duplicados
        query = text("""
            SELECT nit, COUNT(*) 
            FROM empresas 
            GROUP BY nit 
            HAVING COUNT(*) > 1;
        """)
        result = conn.execute(query).fetchall()
        
        if not result:
            print("No se encontraron duplicados.")
            return

        for row in result:
            nit = row[0]
            print(f"Resolviendo duplicados para NIT: {nit}")
            
            # Obtener IDs duplicados
            ids_query = text("SELECT id FROM empresas WHERE nit = :nit ORDER BY id ASC")
            ids = [r[0] for r in conn.execute(ids_query, {"nit": nit}).fetchall()]
            
            # Mantener el primero (o el último, según preferencia. Usualmente el primero es el 'original')
            keep_id = ids[0]
            delete_ids = ids[1:]
            
            print(f"Manteniendo ID: {keep_id}. Eliminando IDs: {delete_ids}")
            
            # Eliminación segura (cascade debe estar configurado en DB, o borrar hijos primero)
            # Asumimos que es una DB de prueba/desarrollo por ahora y forzamos el borrado.
            # Nota: Si hay claves foráneas sin CASCADE, esto fallará. 
            # Intentaremos borrar.
            try:
                if delete_ids:
                    # 1. Delete Dependencies (Plan Cuentas)
                    print(f"Eliminando Plan de Cuentas para empresas: {delete_ids}")
                    del_puc_query = text("DELETE FROM plan_cuentas WHERE empresa_id IN :ids")
                    conn.execute(del_puc_query, {"ids": tuple(delete_ids)})
                    
                    # 2. Delete Company
                    # Convert list to tuple for SQL IN clause
                    del_query = text("DELETE FROM empresas WHERE id IN :ids")
                    conn.execute(del_query, {"ids": tuple(delete_ids)})
                    conn.commit()
                    print("Eliminación exitosa.")
            except Exception as e:
                print(f"Error eliminando: {e}")
                # Si falla, probablemente hay FKs. En ese caso tendríamos que reasignar los hijos al keep_id.
                # Para este caso de 'Empresa de Demostración' duplicada por seeder, suele estar vacía la copia.

if __name__ == "__main__":
    clean_duplicates()
