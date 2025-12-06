# app/services/soporte.py
from sqlalchemy.orm import Session, selectinload
from typing import List

# Importamos los modelos que necesitamos consultar
from app.models import empresa as models_empresa
from app.models import usuario as models_usuario

# Importamos los schemas que acabamos de crear para dar forma a la respuesta
from app.schemas import soporte as schemas_soporte
from app.schemas import usuario as schemas_usuario

def get_dashboard_data(db: Session) -> schemas_soporte.DashboardData:
    """
    Función orquestadora que obtiene todos los datos necesarios para el 
    Panel de Mando de Soporte en una sola operación eficiente.
    """
    
    # 1. Obtener todos los usuarios de soporte
    usuarios_soporte = db.query(models_usuario.Usuario)\
        .filter(models_usuario.Usuario.empresa_id == None)\
        .options(selectinload(models_usuario.Usuario.roles))\
        .order_by(models_usuario.Usuario.email)\
        .all()

    # 2. Obtener todas las empresas, precargando eficientemente 
    #    sus usuarios y los roles de esos usuarios.
    #    Esto resuelve el problema "1+N".
    todas_las_empresas = db.query(models_empresa.Empresa)\
        .options(
            selectinload(models_empresa.Empresa.usuarios)
            .selectinload(models_usuario.Usuario.roles)
        )\
        .order_by(models_empresa.Empresa.razon_social)\
        .all()

    # 3. Empaquetar todo en nuestro schema DashboardData y devolverlo.
    return schemas_soporte.DashboardData(
        empresas=todas_las_empresas,
        usuarios_soporte=usuarios_soporte
    )