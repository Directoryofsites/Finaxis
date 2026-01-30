# app/services/empresa.py
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from ..models.cupo_adicional import CupoAdicional

# Se importan todos los modelos necesarios para una limpieza completa
from ..models import (
    empresa as empresa_model,
    usuario as usuario_model,
    log_operacion as log_operacion_model,
    documento as documento_model,
    tercero as tercero_model,
    plan_cuenta as plan_cuenta_model,
    centro_costo as centro_costo_model,
    tipo_documento as tipo_documento_model,
    permiso as permiso_model,
    periodo_contable_cerrado as periodo_cerrado_model
)

from ..schemas import empresa as empresa_schema, usuario as usuario_schema

# --- CREACIÓN ---
def create_empresa_con_usuarios(
    db: Session, 
    empresa_data: empresa_schema.EmpresaConUsuariosCreate,
    owner_id: int = None,
    padre_id: int = None
    ) -> empresa_model.Empresa:
    
    db_empresa_existente = db.query(empresa_model.Empresa).filter(empresa_model.Empresa.nit == empresa_data.nit).first()
    if db_empresa_existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Ya existe una empresa con el NIT {empresa_data.nit}")
    
    emails_a_crear = [user.email for user in empresa_data.usuarios]
    # Check existing users (skipped for brevity, assuming standard check remains or is handled by try/catch)
    db_usuarios_existentes = db.query(usuario_model.Usuario).filter(usuario_model.Usuario.email.in_(emails_a_crear)).all()
    if db_usuarios_existentes:
        emails_existentes = [user.email for user in db_usuarios_existentes]
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Los siguientes emails ya existen: {', '.join(emails_existentes)}")

    try:
        nueva_empresa = empresa_model.Empresa(
            razon_social=empresa_data.razon_social, 
            nit=empresa_data.nit,
            fecha_inicio_operaciones=empresa_data.fecha_inicio_operaciones, 
            # --- NUEVOS CAMPOS AÑADIDOS AQUÍ ---
            direccion=empresa_data.direccion,
            telefono=empresa_data.telefono,
            email=empresa_data.email,

            logo_url=empresa_data.logo_url,
            modo_operacion=empresa_data.modo_operacion, 
            
            # LINKING ROBUSTO
            owner_id=owner_id,
            padre_id=padre_id,
            # NUEVO MODELO BOLSA: Si tiene padre (es hija), límite local es 0/Infinito.
            limite_registros_mensual=0 if padre_id else 1000, 
            
            created_at=datetime.utcnow()
        )
        db.add(nueva_empresa)
        db.flush()

        # Buscamos el rol con el nombre correcto en minúscula, tal como lo crea el seeder.
        # Buscamos el rol adecuado según el modo de operación
        if empresa_data.modo_operacion == 'AUDITORIA_READONLY':
             rol_nombre = "clon_restringido"
        else:
             rol_nombre = "administrador"

        # 3. Asignar Rol al Usuario
        rol_asignar = None

        # PRIORIDAD: Si se especifica ID de rol manualmente (nueva funcionalidad), usar ese.
        if empresa_data.rol_inicial_id:
            rol_asignar = db.query(permiso_model.Rol).filter(permiso_model.Rol.id == empresa_data.rol_inicial_id).first()
            if not rol_asignar:
                 db.rollback()
                 raise HTTPException(status_code=400, detail=f"El Rol Inicial ID {empresa_data.rol_inicial_id} no existe.")

        # FALLBACK: Si no se especifica, usar el nombre por defecto
        if not rol_asignar:
            admin_role = db.query(permiso_model.Rol).filter(permiso_model.Rol.nombre == rol_nombre).first()
            # Renombramos variable para usarla abajo consistentemente
            rol_asignar = admin_role

        if not rol_asignar:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"CRÍTICO: El rol '{rol_nombre}' no está definido en la base de datos.")

        # --- VARIABLE PARA CAPTURAR AL PRIMER ADMIN/CONTADOR CREADO ---
        # Esto es crucial para solucionar el problema de "Empresas Huérfanas".
        nuevo_owner_id = None

        for usuario_data in empresa_data.usuarios:
            from . import usuario as usuario_service
            # Asignar rol seleccionado (o default)
            user_payload = usuario_schema.UserCreateInCompany(
                email=usuario_data.email, password=usuario_data.password, roles_ids=[rol_asignar.id]
            )
            created_user = usuario_service.create_user_in_company(db=db, user_data=user_payload, empresa_id=nueva_empresa.id)
            
            # Si aún no tenemos un dueño candidato, tomamos al primero que creamos.
            if not nuevo_owner_id:
                nuevo_owner_id = created_user.id
        
        # 4. Vincular al Owner/Contador
        # CASO A: Se proveyó un owner_id explícito (ej: creando hija) -> Usamos ese.
        # CASO B: No se proveyó (ej: Soporte creando perfil contador) -> Usamos el que acabamos de crear.
        
        final_owner_id = owner_id if owner_id else nuevo_owner_id
        
        if final_owner_id:
            # A) Estampar en la tabla Empresa (Propiedad Legal)
            nueva_empresa.owner_id = final_owner_id
            db.add(nueva_empresa) # Asegurar persistencia del cambio
            
            # B) Estampar en la tabla de asociación (Visibilidad)
            from ..models.usuario import usuario_empresas
            # Primero verificamos si ya existe la asociación (create_user ya lo asocia como empleado, pero aquí marcamos owner)
            # Como create_user pone empresa_id en el usuario, la relación usuario_empresas es opcional pero recomendada para 'Multitenancy'.
            # Vamos a insertar o actualizar.
            
            # Check existencia
            exists_stmt = db.query(usuario_empresas).filter_by(usuario_id=final_owner_id, empresa_id=nueva_empresa.id).first()
            if not exists_stmt:
                stmt = usuario_empresas.insert().values(usuario_id=final_owner_id, empresa_id=nueva_empresa.id, is_owner=True)
                db.execute(stmt)
            else:
                # Si ya existe (raro pero posible), aseguramos flag is_owner
                stmt = usuario_empresas.update().where(
                    usuario_empresas.c.usuario_id == final_owner_id,
                    usuario_empresas.c.empresa_id == nueva_empresa.id
                ).values(is_owner=True)
                db.execute(stmt)

        db.commit()
        db.refresh(nueva_empresa)
        return nueva_empresa
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error de integridad de datos: {e.orig}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Un error inesperado ocurrió: {str(e)}")

# --- ACTUALIZACIÓN (AQUÍ ESTABA EL PROBLEMA) ---
def update_empresa(db: Session, empresa_id: int, empresa: empresa_schema.EmpresaUpdate) -> empresa_model.Empresa:
    # Nota: Renombré el argumento 'empresa_data' a 'empresa' para coincidir con la llamada del router.
    db_empresa = get_empresa_by_id(db, empresa_id=empresa_id)
    if not db_empresa:
        return None # El router manejará el 404
    
    # Usamos model_dump(exclude_unset=True) para actualizar solo lo que envió el usuario
    try:
        update_data = empresa.model_dump(exclude_unset=True)
    except AttributeError:
        # Fallback para versiones viejas de Pydantic
        update_data = empresa.dict(exclude_unset=True)

    for key, value in update_data.items():
        if hasattr(db_empresa, key):
            setattr(db_empresa, key, value)

    db.add(db_empresa)
    db.commit()
    db.refresh(db_empresa)
    return db_empresa

# --- GETTERS ---
def get_empresas(db: Session, skip: int = 0, limit: int = 100):
    """Devuelve la lista de todas las empresas (Paginada)."""
    return db.query(empresa_model.Empresa).offset(skip).limit(limit).all()

def get_empresa(db: Session, empresa_id: int):
    """Alias para get_empresa_by_id, requerido por el router."""
    return get_empresa_by_id(db, empresa_id)

def get_empresa_by_id(db: Session, empresa_id: int) -> Optional[empresa_model.Empresa]:
    return db.query(empresa_model.Empresa).filter(empresa_model.Empresa.id == empresa_id).first()

def get_empresas_para_usuario(db: Session, current_user: usuario_model.Usuario) -> List[empresa_model.Empresa]:
    # DEBUG LOGGING
    print(f"DEBUG: get_empresas_para_usuario - User: {current_user.email} (ID: {current_user.id})")
    
    user_roles = {rol.nombre for rol in current_user.roles} if current_user.roles else set()
    if "soporte" in user_roles:
        print("DEBUG: User is Soporte - returning ALL")
        return db.query(empresa_model.Empresa).order_by(empresa_model.Empresa.razon_social).all()
        
    # Lógica Multi-Tenancy:
    # 1. Empresa Principal (si tiene)
    empresas = []
    if current_user.empresa_id:
        emp_principal = db.query(empresa_model.Empresa).filter(empresa_model.Empresa.id == current_user.empresa_id).first()
        if emp_principal: 
            empresas.append(emp_principal)
            print(f"DEBUG: Main Company: {emp_principal.razon_social}")
        
    # 2. Empresas Asignadas (Cartera)
    empresas_map = {e.id: e for e in empresas}
    
    # Force reload/query of assigned companies if needed
    # Note: accessing the relationship triggers lazy load
    assigned_count = 0
    for asignada in current_user.empresas_asignadas:
        empresas_map[asignada.id] = asignada
        assigned_count += 1
        print(f"DEBUG: Found Assigned Company: {asignada.razon_social} (ID: {asignada.id})")
        
    print(f"DEBUG: Total Unique Companies: {len(empresas_map)}")
    
    # --- FIX CRÍTICO: INCLUIR EMPRESAS PROPIAS Y FILIALES (HOLDING) ---
    # A veces la relación M2M puede fallar o no ser suficiente.
    # Garantizamos que el contador vea las empresas que EL creó (owner_id) 
    # o que pertenecen a su empresa principal (padre_id).
    
    otras_empresas = []
    
    # 3. Empresas Propiedad del Usuario (Creador)
    owned_companies = db.query(empresa_model.Empresa).filter(
        empresa_model.Empresa.owner_id == current_user.id
    ).all()
    otras_empresas.extend(owned_companies)
    
    # 4. Empresas Hijas (Si el usuario pertenece a una Holding)
    if current_user.empresa_id:
        child_companies = db.query(empresa_model.Empresa).filter(
            empresa_model.Empresa.padre_id == current_user.empresa_id
        ).all()
        otras_empresas.extend(child_companies)
        
    # Merge al mapa para evitar duplicados
    for extra in otras_empresas:
        if extra.id not in empresas_map:
            empresas_map[extra.id] = extra
            print(f"DEBUG: Found Implicit Company: {extra.razon_social} (ID: {extra.id})")
    # ------------------------------------------------------------------
        
    result_list = list(empresas_map.values())
    
    # --- CALCULAR CONSUMO PARA EL PORTAL ---
    # Enriquecemos los objetos con el consumo del mes actual para que el frontend los muestre.
    from datetime import datetime
    from app.services import dashboard as dashboard_service # Importación local para evitar ciclos
    
    now = datetime.now()
    mes_actual = now.month
    anio_actual = now.year
    
    for emp in result_list:
        try:
            # Usamos lógica optimizada si existiera, o la estándar
            stats = dashboard_service.get_consumo_actual(db, emp.id, mes_actual, anio_actual)
            emp.consumo_actual = stats["total_registros"]
            # Aseguramos que limite_registros_mensual esté actualizado con excepciones si las hay
            emp.limite_registros_mensual = stats["limite_registros"] 
        except Exception as e:
            print(f"Error calculando consumo para empresa {emp.id}: {e}")
            emp.consumo_actual = 0
            
    return result_list

def get_templates(db: Session, current_user: usuario_model.Usuario) -> List[empresa_model.Empresa]:
    """
    Obtiene las plantillas disponibles para un usuario.
    Incluye:
    1. Plantillas Globales (System/Support): owner_id IS NULL
    2. Plantillas Privadas (Del usuario): owner_id == current_user.id
    """
    from sqlalchemy import or_
    
    return db.query(empresa_model.Empresa).filter(
        empresa_model.Empresa.is_template == True,
        or_(
            empresa_model.Empresa.owner_id == None,
            empresa_model.Empresa.owner_id == current_user.id
        )
    ).all()

def get_usuarios_by_empresa_id(db: Session, empresa_id: int) -> List[usuario_model.Usuario]:
    return db.query(usuario_model.Usuario).options(
        joinedload(usuario_model.Usuario.roles)
    ).filter(
        usuario_model.Usuario.empresa_id == empresa_id
    ).order_by(
        usuario_model.Usuario.email
    ).all()

# --- OTROS UPDATES ---
def update_limite_registros(db: Session, empresa_id: int, limite_data: empresa_schema.EmpresaLimiteUpdate) -> empresa_model.Empresa:
    db_empresa = get_empresa_by_id(db, empresa_id=empresa_id)
    if not db_empresa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa no encontrada para actualizar el límite.")
    
    # ACTUALIZACION DUAL: Mantenemos sincronizados ambos campos para evitar conflictos
    db_empresa.limite_registros = limite_data.limite_registros
    db_empresa.limite_registros_mensual = limite_data.limite_registros
    
    db.add(db_empresa)
    db.commit()
    db.refresh(db_empresa)
    return db_empresa

# --- BORRADO ---
def delete_empresa(db: Session, empresa_id: int):
    """Alias para delete_empresa_y_usuarios, adaptado para devolver bool."""
    try:
        delete_empresa_y_usuarios(db, empresa_id)
        return True
    except HTTPException:
        # Si delete_empresa_y_usuarios lanza excepción (ej: por tener documentos), la propagamos
        raise 
    except Exception:
        return False

def delete_empresa_y_usuarios(db: Session, empresa_id: int):
    db_empresa = get_empresa_by_id(db, empresa_id=empresa_id)
    if not db_empresa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No se encontró una empresa con el id {empresa_id}")
    
    documento_existente = db.query(documento_model.Documento).filter(documento_model.Documento.empresa_id == empresa_id).first()
    if documento_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Esta empresa no se puede eliminar porque tiene documentos contables históricos. Utilice el 'Erradicador Universal' para una eliminación forzada."
        )
    try:
        # Borrado en cascada manual (seguridad adicional)
        
        # --- FIX: Borrar dependencias de Inventario e Impuestos primero ---
        from ..models import impuesto as impuesto_model
        # Intentamos importar producto si existe, sino lo omitimos (pero debería existir)
        try:
             from ..models import producto as producto_model
             db.query(producto_model.Producto).filter(producto_model.Producto.empresa_id == empresa_id).delete(synchronize_session=False)
        except ImportError:
             pass
             
        db.query(impuesto_model.TasaImpuesto).filter(impuesto_model.TasaImpuesto.empresa_id == empresa_id).delete(synchronize_session=False)
        # ------------------------------------------------------------------

        db.query(plan_cuenta_model.PlanCuenta).filter(plan_cuenta_model.PlanCuenta.empresa_id == empresa_id).delete(synchronize_session=False)
        db.query(tercero_model.Tercero).filter(tercero_model.Tercero.empresa_id == empresa_id).delete(synchronize_session=False)
        db.query(centro_costo_model.CentroCosto).filter(centro_costo_model.CentroCosto.empresa_id == empresa_id).delete(synchronize_session=False)
        db.query(tipo_documento_model.TipoDocumento).filter(tipo_documento_model.TipoDocumento.empresa_id == empresa_id).delete(synchronize_session=False)
        db.query(periodo_cerrado_model.PeriodoContableCerrado).filter(periodo_cerrado_model.PeriodoContableCerrado.empresa_id == empresa_id).delete(synchronize_session=False)
        db.query(log_operacion_model.LogOperacion).filter(log_operacion_model.LogOperacion.empresa_id == empresa_id).delete(synchronize_session=False)
        
        # --- FIX FK VIOLATION: Eliminar roles asignados a los usuarios primero ---
        # 1. Obtenemos los usuarios asociados a esta empresa
        usuarios = db.query(usuario_model.Usuario).filter(usuario_model.Usuario.empresa_id == empresa_id).all()
        
        # 2. Clasificamos usuarios: ¿Se deben borrar o solo desvincular?
        # Un usuario no se debe borrar si:
        # A) Es dueño de OTRAS empresas.
        # B) Tiene asignadas OTRAS empresas en usuario_empresas.
        
        usuarios_a_borrar = []
        usuarios_a_desvincular = []
        
        from ..models.usuario import usuario_empresas
        
        for u in usuarios:
            # Check A: Dueño de otras empresas (excluyendo la actual)
            otras_como_owner = db.query(empresa_model.Empresa).filter(
                empresa_model.Empresa.owner_id == u.id,
                empresa_model.Empresa.id != empresa_id
            ).count()
            
            # Check B: Asignado a otras empresas (count en tabla intermedia)
            # (SQLAlchemy ORM count on relationship is cleaner but hybrid query works too)
            # Consultamos tabla intermedia directo
            from sqlalchemy import select, func
            stmt = select(func.count()).select_from(usuario_empresas).where(
                usuario_empresas.c.usuario_id == u.id,
                usuario_empresas.c.empresa_id != empresa_id
            )
            otras_asignaciones = db.scalar(stmt)
            
            if otras_como_owner > 0 or otras_asignaciones > 0:
                print(f"DEBUG: Usuario {u.email} es COMPARTIDO (Owner: {otras_como_owner}, Asignado: {otras_asignaciones}). Se desvinculará.")
                usuarios_a_desvincular.append(u)
            else:
                print(f"DEBUG: Usuario {u.email} es LOCAL. Se eliminará.")
                usuarios_a_borrar.append(u)

        # 3. Limpiar tabla intermedia usuario_empresas para TODOS (borrar y desvincular)
        # CRÍTICO: Borramos TODAS las asociaciones de esta empresa, 
        # incluyendo las del Owner/Contador que no sale en la lista de 'usuarios' internos.
        db.execute(usuario_empresas.delete().where(
            usuario_empresas.c.empresa_id == empresa_id
        ))

        # 4. Desvincular usuarios compartidos (Update empresa_id = NULL)
        for u in usuarios_a_desvincular:
            u.empresa_id = None
            db.add(u)
        
        # 5. Borrar usuarios locales
        if usuarios_a_borrar:
            ids_borrar = [u.id for u in usuarios_a_borrar]
            # Primero sus roles
            from ..models.usuario import usuario_roles
            db.execute(usuario_roles.delete().where(usuario_roles.c.usuario_id.in_(ids_borrar)))
            # Luego el usuario
            db.query(usuario_model.Usuario).filter(usuario_model.Usuario.id.in_(ids_borrar)).delete(synchronize_session=False)
        # ------------------------------------------------------------------------
        
        db.delete(db_empresa)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Un error inesperado ocurrió durante la limpieza en cascada: {str(e)}")
    


    db.commit()
    return True

# --- LOGICA MULTI-TENANCY & CLONACIÓN ---

def _clone_puc(db: Session, source_empresa_id: int, target_empresa_id: int):
    """
    Clona el PUC preservando la jerarquía.
    Estrategia: Copia plana + Mapeo de IDs + Reconstrucción de padres.
    """
    # 1. Leer todo el PUC origen
    origen_cuentas = db.query(plan_cuenta_model.PlanCuenta).filter(
        plan_cuenta_model.PlanCuenta.empresa_id == source_empresa_id
    ).all()
    
    if not origen_cuentas: return

    # 2. Crear mapa Old_ID -> New_Instance (sin guardar aún)
    # No podemos saber el New_ID hasta guardar, así que guardamos primero sin padre.
    
    mapa_id = {} # old_id -> new_object
    
    # 3. Primera Pasada: Crear cuentas sin relaciones
    nuevas_cuentas = []
    for c in origen_cuentas:
        nueva = plan_cuenta_model.PlanCuenta(
            empresa_id=target_empresa_id,
            codigo=c.codigo,
            nombre=c.nombre,
            nivel=c.nivel,
            permite_movimiento=c.permite_movimiento,
            funcion_especial=c.funcion_especial,
            clase=c.clase,
            es_cuenta_de_ingresos=c.es_cuenta_de_ingresos,
            is_bank_reconciliation_account=c.is_bank_reconciliation_account,
            cuenta_padre_id=None, # Se asigna en pass 2
            created_by=None # System created
        )
        nuevas_cuentas.append(nueva)
        # Necesitamos rastrear cual era el ID viejo de esta instancia nueva
        # Usaremos un atributo temporal en el objeto python
        nueva._old_id = c.id
    
    db.add_all(nuevas_cuentas)
    db.flush() # Genera IDs para las nuevas cuentas
    
    # 4. Construir Mapa real: Old_ID -> New_ID
    old_to_new_ids = {nc._old_id: nc.id for nc in nuevas_cuentas}
    
    # 5. Segunda Pasada: Asignar padres
    # Iteramos sobre las cuentas ORIGIALES para ver sus padres
    for c_origen in origen_cuentas:
        if c_origen.cuenta_padre_id:
            # Buscamos el ID nuevo correspondiente a esta cuenta
            new_id_child = old_to_new_ids.get(c_origen.id)
            # Buscamos el ID nuevo correspondiente al padre viejo
            new_id_parent = old_to_new_ids.get(c_origen.cuenta_padre_id)
            
            if new_id_child and new_id_parent:
                # Actualizamos en DB (buscando en la lista local para evitar queries)
                # O mejor, hacemos update masivo? No, update individual en session
                child_obj = next(nc for nc in nuevas_cuentas if nc.id == new_id_child)
                child_obj.cuenta_padre_id = new_id_parent
                db.add(child_obj)
    
    db.flush()

def _clone_tipos_doc(db: Session, source_empresa_id: int, target_empresa_id: int):
    tipos = db.query(tipo_documento_model.TipoDocumento).filter(
        tipo_documento_model.TipoDocumento.empresa_id == source_empresa_id
    ).all()
    for t in tipos:
        nuevo = tipo_documento_model.TipoDocumento(
            empresa_id=target_empresa_id,
            codigo=t.codigo,
            nombre=t.nombre,
            funcion_especial=t.funcion_especial,
            consecutivo_actual=0,
            numeracion_manual=t.numeracion_manual,
            afecta_inventario=t.afecta_inventario,
            es_venta=t.es_venta,
            es_compra=t.es_compra,
            # NOTA: No clonamos las referencias a cuentas (caja, cxc, cxp) automáticamente por ahora
            # para evitar complejidad de mapeo de IDs. Se deberán configurar manualmente.
            cuenta_caja_id=None,
            cuenta_debito_cxc_id=None,
            cuenta_credito_cxc_id=None,
            cuenta_debito_cxp_id=None,
            cuenta_credito_cxp_id=None
        )
        db.add(nuevo)
    db.flush()

def create_empresa_from_template(
    db: Session, 
    empresa_data: empresa_schema.EmpresaConUsuariosCreate, 
    template_category: str,
    owner_id: int,
    padre_id: int = None
) -> empresa_model.Empresa:
    """
    Crea una empresa clonando una Plantilla Maestra según categoría.
    Asigna owner y padre (Contador).
    """
    # 1. Buscar Template Semilla
    template = db.query(empresa_model.Empresa).filter(
        empresa_model.Empresa.is_template == True,
        empresa_model.Empresa.template_category == template_category
    ).first()
    
    if not template:
        raise HTTPException(status_code=400, detail=f"No existe plantilla para categoría: {template_category}")
        
    # 2. Crear Empresa Base (usando lógica estándar reusada o new instance)
    # Preferimos lógica new instance para controlar campos
    
    # Check NIT dup
    if db.query(empresa_model.Empresa).filter(empresa_model.Empresa.nit == empresa_data.nit).first():
        raise HTTPException(status_code=409, detail="NIT ya existe")

    nueva_empresa = empresa_model.Empresa(
        razon_social=empresa_data.razon_social, 
        nit=empresa_data.nit,
        fecha_inicio_operaciones=empresa_data.fecha_inicio_operaciones, 
        direccion=empresa_data.direccion,
        telefono=empresa_data.telefono,
        email=empresa_data.email,
        logo_url=empresa_data.logo_url,
        modo_operacion='STANDARD',
        
        # LINKING
        padre_id=padre_id,
        owner_id=owner_id,
        limite_registros_mensual=0 if padre_id else 500, # 0 para hijas (consumo padre), 500 default para independientes
        
        created_at=datetime.utcnow()
    )
    db.add(nueva_empresa)
    db.flush()
    
    db.flush()

def _clone_impuestos(db: Session, source_empresa_id: int, target_empresa_id: int):
    """
    Clona los impuestos y sus relaciones con cuentas contables.
    Requiere que _clone_puc ya se haya ejecutado para re-enlazar cuentas.
    """
    # 1. Obtener impuestos origen
    from ..models.impuesto import TasaImpuesto
    impuestos_origen = db.query(TasaImpuesto).filter(
        TasaImpuesto.empresa_id == source_empresa_id
    ).all()
    
    if not impuestos_origen: return

    # 2. Mapa de cuentas (Nombre/Codigo -> Nuevo ID)
    # Como los IDs cambian, necesitamos buscar la cuenta equivalente en la nueva empresa.
    # Asumimos que el clonado de PUC mantuvo los CODIGOS.
    
    # Optimizacion: Cargar mapa de codigos de la nueva empresa
    cuentas_nuevas = db.query(plan_cuenta_model.PlanCuenta).filter(
        plan_cuenta_model.PlanCuenta.empresa_id == target_empresa_id
    ).all()
    mapa_codigo_id = {c.codigo: c.id for c in cuentas_nuevas}
    
    # Necesitamos saber el codigo de la cuenta original para buscar la nueva
    # Cargamos las cuentas originales referenciadas
    ids_cuentas_origen = set()
    for imp in impuestos_origen:
        if imp.cuenta_id: ids_cuentas_origen.add(imp.cuenta_id)
        if imp.cuenta_iva_descontable_id: ids_cuentas_origen.add(imp.cuenta_iva_descontable_id)
        
    mapa_id_codigo_origen = {}
    if ids_cuentas_origen:
        cuentas_origen = db.query(plan_cuenta_model.PlanCuenta).filter(
            plan_cuenta_model.PlanCuenta.id.in_(list(ids_cuentas_origen))
        ).all()
        mapa_id_codigo_origen = {c.id: c.codigo for c in cuentas_origen}

    # 3. Clonar
    nuevos_impuestos = []
    for imp in impuestos_origen:
        # Resolver IDs nuevos
        nuevo_cuenta_id = None
        if imp.cuenta_id:
            cod = mapa_id_codigo_origen.get(imp.cuenta_id)
            nuevo_cuenta_id = mapa_codigo_id.get(cod)
            
        nuevo_cuenta_desc_id = None
        if imp.cuenta_iva_descontable_id:
            cod = mapa_id_codigo_origen.get(imp.cuenta_iva_descontable_id)
            nuevo_cuenta_desc_id = mapa_codigo_id.get(cod)

        nuevo = TasaImpuesto(
            empresa_id=target_empresa_id,
            nombre=imp.nombre,
            tasa=imp.tasa,
            cuenta_id=nuevo_cuenta_id,
            cuenta_iva_descontable_id=nuevo_cuenta_desc_id
        )
        nuevos_impuestos.append(nuevo)
        
    db.add_all(nuevos_impuestos)
    db.flush()

def create_empresa_from_template(
    db: Session, 
    empresa_data: empresa_schema.EmpresaConUsuariosCreate, 
    template_category: str,
    owner_id: int,
    padre_id: int = None
) -> empresa_model.Empresa:
    """
    Crea una empresa clonando una Plantilla Maestra según categoría.
    Asigna owner y padre (Contador).
    """
    # 1. Buscar Template Semilla
    template = db.query(empresa_model.Empresa).filter(
        empresa_model.Empresa.is_template == True,
        empresa_model.Empresa.template_category == template_category
    ).first()
    
    if not template:
        raise HTTPException(status_code=400, detail=f"No existe plantilla para categoría: {template_category}")
        
    # 2. Crear Empresa Base (usando lógica estándar reusada o new instance)
    # Preferimos lógica new instance para controlar campos
    
    # Check NIT dup
    if db.query(empresa_model.Empresa).filter(empresa_model.Empresa.nit == empresa_data.nit).first():
        raise HTTPException(status_code=409, detail="NIT ya existe")

    nueva_empresa = empresa_model.Empresa(
        razon_social=empresa_data.razon_social, 
        nit=empresa_data.nit,
        fecha_inicio_operaciones=empresa_data.fecha_inicio_operaciones, 
        direccion=empresa_data.direccion,
        telefono=empresa_data.telefono,
        email=empresa_data.email,
        logo_url=empresa_data.logo_url,
        modo_operacion='STANDARD',
        
        # LINKING
        padre_id=padre_id,
        owner_id=owner_id,
        limite_registros_mensual=0 if padre_id else 500, # 0 para hijas (consumo padre), 500 default para independientes
        
        created_at=datetime.utcnow()
    )
    db.add(nueva_empresa)
    db.flush()
    
    # 3. CLONACIÓN
    _clone_puc(db, template.id, nueva_empresa.id)
    _clone_tipos_doc(db, template.id, nueva_empresa.id)
    _clone_impuestos(db, template.id, nueva_empresa.id)
    
    # 4. Crear Usuario Admin Inicial (Dueño) si viene en data
    # (Reusamos lógica de create_empresa_con_usuarios parcial o manual)
    # Por ahora manual simple
    rol_admin = db.query(permiso_model.Rol).filter(permiso_model.Rol.nombre == "administrador").first()
    
    for u_data in empresa_data.usuarios:
        from . import usuario as usuario_service
        up = usuario_schema.UserCreateInCompany(
            email=u_data.email, password=u_data.password, roles_ids=[rol_admin.id]
        )
        usuario_service.create_user_in_company(db=db, user_data=up, empresa_id=nueva_empresa.id)
        
    # 5. Asociar Owner (Contador) a la lista de empresas permitidas de esa empresa nueva?
    # El owner ya tiene acceso via "padre_id" implícito o rol?
    # Mejor: agregar explícitamente a usuario_empresas del contador para que salga en su lista.
    if owner_id:
        # Check if already linked (via create_user logic)? No, owner is external.
        # Insert into association table
        from ..models.usuario import usuario_empresas
        stmt = usuario_empresas.insert().values(usuario_id=owner_id, empresa_id=nueva_empresa.id, is_owner=True)
        db.execute(stmt)

    db.commit()
    return nueva_empresa

def transferir_cartera(db: Session, empresa_id: int, nuevo_padre_id: int = None, nuevo_owner_id: int = None):
    """
    PROTOCOLO ANTI-SECUESTRO / CAMBIO DE DUEÑO.
    Permite mover una empresa de la cartera de un Contador a otro (o a ninguno/Directo).
    """
    empresa = get_empresa_by_id(db, empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
        
    # Validar nuevo padre
    if nuevo_padre_id:
        padre = get_empresa_by_id(db, nuevo_padre_id)
        if not padre: raise HTTPException(status_code=400, detail="Nuevo padre no existe")
        
    empresa.padre_id = nuevo_padre_id
    if nuevo_owner_id is not None:
        empresa.owner_id = nuevo_owner_id
        
    db.add(empresa)
    db.commit()
    return empresa

def create_template_from_existing(
    db: Session, 
    source_empresa_id: int, 
    template_category: str
) -> empresa_model.Empresa:
    """
    Crea una NUEVA empresa plantilla copiando datos de una empresa existente.
    NO modifica la empresa original.
    """
    source = get_empresa_by_id(db, source_empresa_id)
    if not source:
        raise HTTPException(status_code=404, detail="Empresa origen no encontrada")

    # 1. Crear Nueva Empresa (Clon de Cabecera)
    print(f"Cloning Company '{source.razon_social}' to create a Template...")
    
    # Generate unique NIT for template to avoid collisions
    # Format: T-{OriginalNIT}-{Random4} or just T-{OriginalNIT} if checks allow
    # Let's use a robust format
    import random
    suffix = random.randint(1000, 9999)
    new_nit = f"T-{source.nit}-{suffix}"
    
    new_name = f"{source.razon_social} (Plantilla)"
    
    # Check name collision?
    # Let's assume name collision is allowed or handled by user later
    
    nueva_empresa = empresa_model.Empresa(
        razon_social=new_name,
        nit=new_nit,
        fecha_inicio_operaciones=datetime.utcnow(), 
        direccion=source.direccion,
        telefono=source.telefono,
        email=source.email,
        logo_url=source.logo_url,
        modo_operacion='STANDARD',
        
        # KEY FLAGS
        is_template=True,
        template_category=template_category,
        
        # Templates are usually owned by System/Support (owner_id=None implies System in some logic, 
        # or we might want to assign current user. For Soporte Util, None is safer or safer to keep source owner?)
        # User said: "convertir esa empresa en plantilla... cuando cree otras empresas."
        # If we set owner_id to None, it appears in "Mis Empresas" (Admin) based on new logic.
        # If we set owner_id to Source Owner, it appears in their list?
        # Let's set owner_id to None (System) so it's a "Global Template".
        owner_id=None, 
        padre_id=None, 
        
        limite_registros_mensual=source.limite_registros_mensual,
        created_at=datetime.utcnow()
    )
    
    db.add(nueva_empresa)
    db.flush()
    
    # 2. CLONAR DATOS
    _clone_puc(db, source.id, nueva_empresa.id)
    _clone_tipos_doc(db, source.id, nueva_empresa.id)
    _clone_impuestos(db, source.id, nueva_empresa.id)
    
    db.commit()
    db.refresh(nueva_empresa)
    return nueva_empresa
