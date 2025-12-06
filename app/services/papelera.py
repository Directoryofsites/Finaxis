# app/services/papelera.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from datetime import datetime, timedelta

from ..models.documento import Documento, DocumentoEliminado
from ..models.movimiento_contable import MovimientoContable, MovimientoEliminado
from ..models.usuario import Usuario
from ..models.tipo_documento import TipoDocumento

# --- IMPORTACIÓN CRÍTICA: EL GUARDIÁN DE PERIODOS ---
from app.services import periodo as periodo_service
# ----------------------------------------------------

def get_documentos_eliminados(db: Session, empresa_id: int):
    """
    Obtiene una lista de todos los documentos en la papelera para una empresa.
    """
    subquery_valor = db.query(
        MovimientoEliminado.documento_eliminado_id,
        func.sum(MovimientoEliminado.debito).label("valor_documento")
    ).group_by(MovimientoEliminado.documento_eliminado_id).subquery()

    query = db.query(
        DocumentoEliminado.id,
        DocumentoEliminado.id_original,
        DocumentoEliminado.fecha,
        DocumentoEliminado.numero,
        DocumentoEliminado.fecha_eliminacion,
        Usuario.email.label("usuario_eliminacion"),
        TipoDocumento.nombre.label("tipo_documento_nombre"),
        func.coalesce(subquery_valor.c.valor_documento, 0).label("valor_documento")
    ).select_from(DocumentoEliminado) \
    .outerjoin(subquery_valor, DocumentoEliminado.id == subquery_valor.c.documento_eliminado_id) \
    .outerjoin(TipoDocumento, DocumentoEliminado.tipo_documento_id == TipoDocumento.id) \
    .outerjoin(Usuario, DocumentoEliminado.usuario_eliminacion_id == Usuario.id) \
    .filter(
        DocumentoEliminado.empresa_id == empresa_id
    ).order_by(
        DocumentoEliminado.fecha_eliminacion.desc()
    )
    
    return query.all()


def restaurar_documento(db: Session, doc_eliminado_id: int, empresa_id: int):
    """
    Restaura un documento desde la papelera a las tablas activas.
    BLINDADO: Verifica si el período contable está cerrado.
    """
    # 1. Buscamos el documento en la papelera (Lectura)
    doc_para_restaurar = db.query(DocumentoEliminado).filter(
        DocumentoEliminado.id == doc_eliminado_id,
        DocumentoEliminado.empresa_id == empresa_id
    ).first()

    if not doc_para_restaurar:
        raise HTTPException(status_code=404, detail="El documento no se encuentra en la papelera.")

    # --- PROTOCOLO DE CAJA NEGRA: DIAGNÓSTICO EN CONSOLA ---
    print(f"\n🚨 INTENTO DE RESTAURACIÓN DETECTADO")
    print(f"📄 Documento ID: {doc_eliminado_id} | Fecha: {doc_para_restaurar.fecha}")
    print(f"🔒 Verificando si el período {doc_para_restaurar.fecha.month}/{doc_para_restaurar.fecha.year} está cerrado...")
    # -------------------------------------------------------

    # 2. BLINDAJE CONTABLE: Validar período cerrado ANTES de proceder
    # Si esta línea falla, lanzará la excepción 409 y detendrá todo.
    periodo_service.validar_periodo_abierto(db, empresa_id, doc_para_restaurar.fecha)
    
    print("✅ Período ABIERTO. Procediendo con la restauración...\n") # Solo sale si no está cerrado

    try:
        # 3. Validación de conflicto (número repetido)
        conflicto = db.query(Documento).filter(
            Documento.empresa_id == empresa_id,
            Documento.tipo_documento_id == doc_para_restaurar.tipo_documento_id,
            Documento.numero == doc_para_restaurar.numero,
            Documento.anulado == False
        ).first()

        if conflicto:
            raise HTTPException(status_code=409, detail=f"No se puede restaurar. Ya existe un documento activo con el mismo tipo y número ({doc_para_restaurar.numero}).")

        # 4. Proceso de restauración (Escritura)
        nuevo_doc_activo = Documento(
            empresa_id=doc_para_restaurar.empresa_id,
            tipo_documento_id=doc_para_restaurar.tipo_documento_id,
            numero=doc_para_restaurar.numero,
            fecha=doc_para_restaurar.fecha,
            fecha_vencimiento=doc_para_restaurar.fecha_vencimiento,
            beneficiario_id=doc_para_restaurar.beneficiario_id,
            centro_costo_id=doc_para_restaurar.centro_costo_id,
            usuario_creador_id=doc_para_restaurar.usuario_creador_id,
            anulado=False,
            estado='ACTIVO'
        )

        for mov_elim in doc_para_restaurar.movimientos:
            nuevo_mov_activo = MovimientoContable(
                cuenta_id=mov_elim.cuenta_id,
                concepto=mov_elim.concepto,
                debito=mov_elim.debito,
                credito=mov_elim.credito,
                centro_costo_id=mov_elim.centro_costo_id,
                producto_id=getattr(mov_elim, 'producto_id', None)
            )
            nuevo_doc_activo.movimientos.append(nuevo_mov_activo)
        
        db.add(nuevo_doc_activo)
        db.delete(doc_para_restaurar)
        
        db.commit()
        db.refresh(nuevo_doc_activo)
        
        return nuevo_doc_activo

    except HTTPException as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al restaurar el documento: {str(e)}")

def vaciar_papelera_por_antiguedad(db: Session, empresa_id: int, dias_antiguedad: int = 30):
    """
    Elimina permanentemente los documentos de la papelera de una empresa.
    NOTA: Vaciar la papelera NO requiere validación de período, ya que eliminar
    algo que YA estaba eliminado no afecta los saldos contables activos.
    """
    try:
        fecha_limite = datetime.now() - timedelta(days=dias_antiguedad)
        
        query = db.query(DocumentoEliminado).filter(
            DocumentoEliminado.empresa_id == empresa_id,
            DocumentoEliminado.fecha_eliminacion < fecha_limite
        )
        
        num_docs_eliminados = query.count()
        
        if num_docs_eliminados == 0:
            return {"message": "No hay documentos antiguos que purgar en la papelera."}

        query.delete(synchronize_session=False)
        
        db.commit()
        
        return {"message": f"{num_docs_eliminados} documento(s) han sido eliminados permanentemente de la papelera."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al vaciar la papelera: {str(e)}")