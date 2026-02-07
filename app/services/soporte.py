# app/services/soporte.py
from sqlalchemy.orm import Session, selectinload
from typing import List

# Importamos los modelos que necesitamos consultar
from app.models import empresa as models_empresa
from app.models import usuario as models_usuario
from app.models import permiso as models_permiso  # <--- NUEVO IMPORT

# Importamos los schemas que acabamos de crear para dar forma a la respuesta
from app.schemas import soporte as schemas_soporte
from app.schemas import usuario as schemas_usuario

def get_dashboard_data(db: Session) -> schemas_soporte.DashboardData:
    """
    Función orquestadora que obtiene todos los datos necesarios para el 
    Panel de Mando de Soporte en una sola operación eficiente.
    """
    
    # 1. Obtener todos los usuarios de soporte (Que tengan rol 'soporte')
    # Nota: empresa_id=None es típica de soporte, pero también de contadores freelance.
    # Por eso filtramos explícitamente por el rol.
    usuarios_soporte = db.query(models_usuario.Usuario)\
        .join(models_usuario.Usuario.roles)\
        .filter(models_permiso.Rol.nombre == 'soporte')\
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

def get_accountant_users(db: Session) -> List[models_usuario.Usuario]:
    """
    Obtiene la lista de usuarios que tienen el rol de 'contador'.
    Util para poblar el filtro "De Contadores" en el panel de soporte.
    """
    return db.query(models_usuario.Usuario)\
        .join(models_usuario.Usuario.roles)\
        .filter(models_permiso.Rol.nombre == 'contador')\
        .order_by(models_usuario.Usuario.email)\
        .all()

def search_empresas(
    db: Session, 
    q: str = None, 
    role_filter: str = 'ADMIN', # 'ADMIN' (Soporte/Propio) vs 'CONTADOR' (Terceros)
    type_filter: str = 'REAL',  # 'REAL' vs 'PLANTILLA'
    owner_id: int = None,       # NUEVO FILTRO: Filtrar por dueño específico
    page: int = 1, 
    size: int = 20
) -> schemas_soporte.EmpresaSearchResponse:
    
    query = db.query(models_empresa.Empresa)

    # 1. Filtro Texto (Búsqueda Inteligente)
    if q:
        search_term = f"%{q.lower()}%"
        query = query.filter(
            (models_empresa.Empresa.razon_social.ilike(search_term)) |
            (models_empresa.Empresa.nit.ilike(search_term))
        )

    # 2. Filtro Tipo (Plantilla vs Real)
    if type_filter == 'PLANTILLA':
        query = query.filter(models_empresa.Empresa.is_template == True)
    else:
        # Por defecto mostramos reales. Debemos incluir False Y NULL (para registros antiguos)
        query = query.filter(
            (models_empresa.Empresa.is_template == False) | 
            (models_empresa.Empresa.is_template == None)
        )

    # 3. Filtro Jerarquia (Admin/Holding vs Contadores/Hijas)
    # 3. Filtro Jerarquia (Admin/Holding vs Contadores/Hijas)
    if role_filter == 'CONTADOR':
        # "De Contadores"
        if owner_id:
            # Filtrar por un contador ESPECÍFICO
            query = query.filter(models_empresa.Empresa.owner_id == owner_id)
        else:
             query = query.filter(models_empresa.Empresa.owner_id != None)
             
    else:
        # "Mis Empresas" (Admin/Sistema)
        
        # CORRECCIÓN: Si estamos buscando PLANTILLAS, el usuario de soporte debe poder ver 
        # TODAS las plantillas disponibles en el sistema, incluso las creadas por contadores.
        if type_filter == 'PLANTILLA':
            pass # No filtramos por owner_id, mostramos todas las plantillas globales.
        else:
            # Si son empresas REALES, solo mostramos las propias del sistema (sin owner)
            query = query.filter(models_empresa.Empresa.owner_id == None)

    # Paginación
    total = query.count()
    items = query.options(
            selectinload(models_empresa.Empresa.usuarios)
            .selectinload(models_usuario.Usuario.roles)
        ) \
        .order_by(models_empresa.Empresa.razon_social) \
        .offset((page - 1) * size) \
        .limit(size) \
        .all()
    
    import math
    pages = math.ceil(total / size)
    
    return schemas_soporte.EmpresaSearchResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

def create_empresa_from_template(db: Session, data: schemas_soporte.EmpresaCreateFromTemplate) -> models_empresa.Empresa:
    """
    Wrapper para llamar al servicio de creación desde plantilla.
    """
    from app.services import empresa as empresa_service
    
    # Validamos que existe la plantilla (esto lo hace el servicio core, pero el wrapper sirve de puente)
    
    # Importante: el servicio core espera 'empresa_data' como schemas.empresa.EmpresaConUsuariosCreate
    # Nuestro schema de soporte usa schemas.soporte.EmpresaConUsuarios (que es igual o compatible)
    # Pero para estar seguros, convertimos a dict y recreamos el objeto esperado si fuera necesario.
    # Como pydantic es flexible, pasarlo directo suele funcionar si los campos coinciden.
    
    # Requerimos importar el schema de empresa para casting explícito si Pydantic se queja,
    # pero intentaremos pasarlo directo primero.
    
    return empresa_service.create_empresa_from_template(
        db=db,
        empresa_data=data.empresa_data,
        template_category=data.template_category,
        owner_id=data.owner_id
    )