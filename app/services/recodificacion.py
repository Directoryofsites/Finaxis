from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

from ..schemas import recodificacion as schemas

def recodificar_datos(
    db: Session, 
    campo_afectado: str, 
    tabla_afectada: str, 
    request_data: schemas.RecodificacionRequest, 
    empresa_id: int
):
    """
    Función genérica que realiza la recodificación masiva de forma transaccional.
    """
    filtros = request_data.filtros
    recodificacion = request_data.recodificacion

    # Parámetros para la consulta SQL, previene inyección SQL
    params = {
        "destino_id": recodificacion.destinoId,
        "origen_id": recodificacion.origenId,
        "empresa_id": empresa_id,
        "tipo_doc_id": filtros.tipoDocId
    }
    
    # Construcción dinámica de la cláusula WHERE para la subconsulta
    where_clauses = ["empresa_id = :empresa_id", "tipo_documento_id = :tipo_doc_id"]

    if filtros.numero:
        # Se convierte la cadena de números separados por coma en una lista de enteros
        try:
            numeros_array = [int(n.strip()) for n in filtros.numero.split(',')]
            params["numeros_array"] = tuple(numeros_array)
            where_clauses.append("numero IN :numeros_array")
        except ValueError:
            raise HTTPException(status_code=400, detail="El campo 'numero' contiene valores no numéricos.")

    if filtros.fechaInicio and filtros.fechaFin:
        params["fecha_inicio"] = filtros.fechaInicio
        params["fecha_fin"] = filtros.fechaFin
        where_clauses.append("fecha BETWEEN :fecha_inicio AND :fecha_fin")
    
    subquery_where = " AND ".join(where_clauses)
    
    # Construcción de la consulta de actualización principal
    # Usamos text() de SQLAlchemy para ejecutar SQL crudo de forma segura
    if tabla_afectada == 'movimientos_contables':
        update_query = text(f"""
            UPDATE movimientos_contables
            SET {campo_afectado} = :destino_id
            WHERE {campo_afectado} = :origen_id
            AND documento_id IN (SELECT id FROM documentos WHERE {subquery_where})
        """)
    else: # tabla 'documentos'
        update_query = text(f"""
            UPDATE documentos
            SET {campo_afectado} = :destino_id
            WHERE {campo_afectado} = :origen_id
            AND id IN (SELECT id FROM documentos WHERE {subquery_where})
        """)

    try:
        result = db.execute(update_query, params)
        db.commit()
        
        tabla_nombre = 'movimientos' if tabla_afectada == 'movimientos_contables' else 'documentos'
        return {"message": f"Operación completada. Se actualizaron {result.rowcount} {tabla_nombre}."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno del servidor durante la recodificación: {str(e)}")