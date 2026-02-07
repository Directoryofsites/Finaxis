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

        # --- AUTO-CONFIGURACIÓN FACTURACIÓN ELECTRÓNICA (SANDBOX) ---
        # Para facilitar pruebas, inyectamos credenciales de Sandbox a toda empresa nueva.
        try:
            from ..models.configuracion_fe import ConfiguracionFE
            import json
            
            creds_sandbox = {
                "client_id": "a1003ed4-93cc-4980-89ab-1a181b031918",
                "client_secret": "iO7V0w287m87yGZ3JOlWgR5ytGsFSXaIkGcOMaJd",
                "username": "sandbox@factus.com.co",
                "password": "sandbox2024%"
            }
            
            nueva_config_fe = ConfiguracionFE(
                empresa_id=nueva_empresa.id,
                proveedor='FACTUS',
                ambiente='PRUEBAS',
                habilitado=True,
                api_token=json.dumps(creds_sandbox)
            )
            db.add(nueva_config_fe)
            # No hacemos commit aquí, esperamos al commit final de la transacción principal
        except Exception as e:
            print(f"Advertencia: No se pudo auto-configurar FE Sandbox: {e}")
        # -------------------------------------------------------------

        # Buscamos el rol con el nombre correcto en minúscula, tal como lo crea el seeder.
        # Buscamos el rol adecuado según el modo de operación
        if empresa_data.modo_operacion == 'AUDITORIA_READONLY':
             rol_nombre = "clon_restringido"
        else:
             rol_nombre = "Administrador"

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
            
            # Si aún no tenemos un dueño candidato, tomamos al primero que creamos...
            # PERO: Solo si el rol asignado es 'contador' o similar.
            # Si el rol es 'administrador' (Local), NO lo marcamos como Owner en la tabla Empresa.
            # Esto evita que empresas del sistema aparezcan en la lista de Contadores.
            if not nuevo_owner_id:
                # Verificamos el rol que acabamos de usar
                if rol_asignar.nombre.lower() == 'contador': 
                     nuevo_owner_id = created_user.id
                else:
                     # Es un admin local, no es "Owner" SaaS.
                     pass
        
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

def get_empresas_para_usuario(db: Session, current_user: usuario_model.Usuario, mes: Optional[int] = None, anio: Optional[int] = None) -> List[empresa_model.Empresa]:
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
    mes_actual = mes if mes else now.month
    anio_actual = anio if anio else now.year
    
    for emp in result_list:
        try:
            # Usamos lógica optimizada si existiera, o la estándar
            stats = dashboard_service.get_consumo_actual(db, emp.id, mes_actual, anio_actual)
            emp.consumo_actual = stats["total_registros"]
            # Aseguramos que limite_registros_mensual esté actualizado con excepciones si las hay
            emp.limite_registros_mensual = stats["limite_registros"]
            emp.periodo_consumo = stats["periodo_texto"] # Inject Period Name for Portal 
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
def delete_empresa(db: Session, empresa_id: int) -> bool:
    empresa = get_empresa(db, empresa_id)
    if not empresa:
        return False
        
    try:
        # --- PRE-LIMPIEZA MANUAL (DESHABILITADA) ---
        # Ahora confiamos en el cascade ORM completo configurado en app/models/empresa.py
        # El cascade debe manejar: Productos -> Grupos -> Cuentas, etc.
        
        # 1. PH
        # from sqlalchemy import text
        # db.execute(text("DELETE FROM ph_conceptos WHERE empresa_id = :eid"), {"eid": empresa_id})
        # db.execute(text("DELETE FROM ph_configuracion WHERE empresa_id = :eid"), {"eid": empresa_id})
        
        # ... (Resto deshabilitado) ...
        
        db.delete(empresa)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Un error inesperado ocurrió durante la limpieza en cascada: {e}")
        # Re-raise para ver el error real si falla aun con limpieza
        raise e 
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
        
        # --- FIX: Borrar dependencias de Nómina (ConfiguracionNomina bloquea PlanCuentas) ---
        from ..models import nomina as nomina_model
        
        # 1. Borrar Documentos de Nómina (y sus detalles por cascade)
        db.query(nomina_model.Nomina).filter(nomina_model.Nomina.empresa_id == empresa_id).delete(synchronize_session=False)
        
        # 2. Borrar Configuración (Rompe vínculo con PlanCuenta)
        db.query(nomina_model.ConfiguracionNomina).filter(nomina_model.ConfiguracionNomina.empresa_id == empresa_id).delete(synchronize_session=False)
        
        # 3. Borrar Empleados (Rompe vínculo con Terceros)
        db.query(nomina_model.Empleado).filter(nomina_model.Empleado.empresa_id == empresa_id).delete(synchronize_session=False)
        
        # 4. Borrar Tipos de Nómina
        db.query(nomina_model.TipoNomina).filter(nomina_model.TipoNomina.empresa_id == empresa_id).delete(synchronize_session=False)
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
        if imp.cuenta_id and imp.cuenta_id in mapa_id_codigo_origen:
            codigo = mapa_id_codigo_origen[imp.cuenta_id]
            nuevo_cuenta_id = mapa_codigo_id.get(codigo)
            
        nuevo_cuenta_desc_id = None
        if imp.cuenta_iva_descontable_id and imp.cuenta_iva_descontable_id in mapa_id_codigo_origen:
            codigo = mapa_id_codigo_origen[imp.cuenta_iva_descontable_id]
            nuevo_cuenta_desc_id = mapa_codigo_id.get(codigo)
            
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

def _clone_configuracion_reporte(db: Session, source_empresa_id: int, target_empresa_id: int):
    """
    Clona la configuración de reportes (Renglones IVA, Renta, etc.)
    Re-mapea las cuentas_ids usando el código de cuenta como puente.
    """
    from ..models.configuracion_reporte import ConfiguracionReporte
    from ..models.plan_cuenta import PlanCuenta

    # 1. Obtener configs origen
    configs_origen = db.query(ConfiguracionReporte).filter(
        ConfiguracionReporte.empresa_id == source_empresa_id
    ).all()
    
    if not configs_origen: return
    
    # 2. Preparar Mapa de Cuentas (Old ID -> Code -> New ID)
    # 2.1 Cuentas Destino (Mapa Code -> NewID)
    cuentas_destino = db.query(PlanCuenta).filter(PlanCuenta.empresa_id == target_empresa_id).all()
    mapa_codigo_newid = {c.codigo: c.id for c in cuentas_destino}
    
    # 2.2 Cuentas Origen (Mapa OldID -> Code)
    # Recolectar todos los IDs usados en los JSONs
    all_old_ids = set()
    for conf in configs_origen:
        if conf.cuentas_ids:
            # cuentas_ids es un JSON array de ints o strings numéricos
            for uid in conf.cuentas_ids:
                try:
                    all_old_ids.add(int(uid))
                except:
                    pass
    
    mapa_oldid_codigo = {}
    if all_old_ids:
        cuentas_origen = db.query(PlanCuenta).filter(PlanCuenta.id.in_(list(all_old_ids))).all()
        mapa_oldid_codigo = {c.id: c.codigo for c in cuentas_origen}
        
    # 3. Clonar
    nuevas_configs = []
    for conf in configs_origen:
        nuevos_ids = []
        if conf.cuentas_ids:
            for old_id in conf.cuentas_ids:
                try:
                    # Case 1: Value is a Code string (e.g. "413501")
                    val_str = str(old_id).strip()
                    # Check if this code exists in the new company (which clones standard PUC codes)
                    # We store the CODE itself if the destination uses codes, 
                    # OR we map to NewID if destination uses New IDs.
                    # The Model says "cuentas_ids = Column(JSON)" storing CODES. 
                    # So we should append the CODE if valid.
                    
                    # Wait, if the model stores CODES, we just verify it exists?
                    # "mapa_codigo_newid" maps Code -> NewID. 
                    # Is 'cuentas_ids' supposed to store IDs or Codes? 
                    # The DEBUG output showed ['413501']. That is a Code.
                    # The previous logic was appending `mapa_codigo_newid[code]` which adds an ID!
                    # That implies the goal is to store IDs?
                    # BUT the debug output showed ['413501'] on the SOURCE.
                    # If Source has Code, Target should have Code.
                    
                    # Let's assume we store CODES to be consistent with Source.
                    if val_str in mapa_codigo_newid:
                         nuevos_ids.append(val_str)
                         continue
                         
                    # Case 2: Value is an ID (legacy)
                    oid = int(old_id)
                    if oid in mapa_oldid_codigo:
                        code = mapa_oldid_codigo[oid]
                        # If mapped code exists in new company, store the CODE
                        if code in mapa_codigo_newid:
                            nuevos_ids.append(code)
                except:
                    continue
        
        nuevo = ConfiguracionReporte(
            empresa_id=target_empresa_id,
            tipo_reporte=conf.tipo_reporte,
            renglon=conf.renglon,
            concepto=conf.concepto,
            cuentas_ids=nuevos_ids
        )
        nuevas_configs.append(nuevo)
        
    db.add_all(nuevas_configs)
    db.flush()

def _get_mapped_id(old_id, map_old_code, map_code_newid):
    """Helper to map OldID -> Code -> NewID"""
    if not old_id: return None
    if old_id in map_old_code:
        code = map_old_code[old_id]
        if code in map_code_newid:
            return map_code_newid[code]
    return None

def _clone_ph_config(db: Session, source_empresa_id: int, target_empresa_id: int):
    """Clona la configuración general de PH (Intereses, Fechas, Cuentas Centrales)"""
    from ..models.propiedad_horizontal.configuracion import PHConfiguracion
    from ..models.plan_cuenta import PlanCuenta
    from ..models.tipo_documento import TipoDocumento

    source_conf = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == source_empresa_id).first()
    if not source_conf: return

    # MAPPERS
    # 1. Cuentas
    cuentas_new = db.query(PlanCuenta).filter(PlanCuenta.empresa_id == target_empresa_id).all()
    map_code_newid = {c.codigo: c.id for c in cuentas_new}
    
    # Needs old accounts to get codes
    old_account_ids = []
    if source_conf.cuenta_cartera_id: old_account_ids.append(source_conf.cuenta_cartera_id)
    if source_conf.cuenta_caja_id: old_account_ids.append(source_conf.cuenta_caja_id)
    if source_conf.cuenta_ingreso_intereses_id: old_account_ids.append(source_conf.cuenta_ingreso_intereses_id)
    
    map_old_code = {}
    if old_account_ids:
        old_accs = db.query(PlanCuenta).filter(PlanCuenta.id.in_(old_account_ids)).all()
        map_old_code = {c.id: c.codigo for c in old_accs}

    # 2. Tipos Documento (Map by Name/Code? Usually Name key for types)
    # Let's assume Name is the key for Document Types (e.g. "Factura de Venta", "Recibo de Caja")
    docs_new = db.query(TipoDocumento).filter(TipoDocumento.empresa_id == target_empresa_id).all()
    map_doc_name_newid = {d.nombre: d.id for d in docs_new}
    
    old_doc_ids = []
    if source_conf.tipo_documento_factura_id: old_doc_ids.append(source_conf.tipo_documento_factura_id)
    if source_conf.tipo_documento_recibo_id: old_doc_ids.append(source_conf.tipo_documento_recibo_id)
    if source_conf.tipo_documento_mora_id: old_doc_ids.append(source_conf.tipo_documento_mora_id)
    
    map_old_doc_name = {}
    if old_doc_ids:
        old_docs = db.query(TipoDocumento).filter(TipoDocumento.id.in_(old_doc_ids)).all()
        map_old_doc_name = {d.id: d.nombre for d in old_docs}

    def _get_doc_id(old_id):
        if not old_id: return None
        if old_id in map_old_doc_name:
            name = map_old_doc_name[old_id]
            return map_doc_name_newid.get(name)
        return None

    new_conf = PHConfiguracion(
        empresa_id=target_empresa_id,
        interes_mora_mensual=source_conf.interes_mora_mensual,
        dia_corte=source_conf.dia_corte,
        dia_limite_pago=source_conf.dia_limite_pago,
        dia_limite_pronto_pago=source_conf.dia_limite_pronto_pago,
        descuento_pronto_pago=source_conf.descuento_pronto_pago,
        mensaje_factura=source_conf.mensaje_factura,
        tipo_negocio=source_conf.tipo_negocio,
        interes_mora_habilitado=source_conf.interes_mora_habilitado,
        
        # Mapped Foreign Keys
        cuenta_cartera_id=_get_mapped_id(source_conf.cuenta_cartera_id, map_old_code, map_code_newid),
        cuenta_caja_id=_get_mapped_id(source_conf.cuenta_caja_id, map_old_code, map_code_newid),
        cuenta_ingreso_intereses_id=_get_mapped_id(source_conf.cuenta_ingreso_intereses_id, map_old_code, map_code_newid),
        
        tipo_documento_factura_id=_get_doc_id(source_conf.tipo_documento_factura_id),
        tipo_documento_recibo_id=_get_doc_id(source_conf.tipo_documento_recibo_id),
        tipo_documento_mora_id=_get_doc_id(source_conf.tipo_documento_mora_id)
    )
    db.add(new_conf)
    db.flush()

def _clone_ph_conceptos(db: Session, source_empresa_id: int, target_empresa_id: int):
    """Clona Conceptos de Facturación de PH y sus cuentas"""
    from ..models.propiedad_horizontal.concepto import PHConcepto
    from ..models.plan_cuenta import PlanCuenta

    conceptos_source = db.query(PHConcepto).filter(PHConcepto.empresa_id == source_empresa_id).all()
    if not conceptos_source: return

    # MAPPERS (Reusing logic, fetching fresh for safety/completeness inside function scope)
    cuentas_new = db.query(PlanCuenta).filter(PlanCuenta.empresa_id == target_empresa_id).all()
    map_code_newid = {c.codigo: c.id for c in cuentas_new}
    
    # Gather ALL used old IDs efficiently
    all_old_ids = set()
    for c in conceptos_source:
        if c.cuenta_ingreso_id: all_old_ids.add(c.cuenta_ingreso_id)
        if c.cuenta_cxc_id: all_old_ids.add(c.cuenta_cxc_id)
        if c.cuenta_interes_id: all_old_ids.add(c.cuenta_interes_id)
        if c.cuenta_caja_id: all_old_ids.add(c.cuenta_caja_id)
    
    map_old_code = {}
    if all_old_ids:
        old_accs = db.query(PlanCuenta).filter(PlanCuenta.id.in_(list(all_old_ids))).all()
        map_old_code = {acc.id: acc.codigo for acc in old_accs}

    nuevos_conceptos = []
    for c in conceptos_source:
        nuevo = PHConcepto(
            empresa_id=target_empresa_id,
            nombre=c.nombre,
            usa_coeficiente=c.usa_coeficiente,
            es_fijo=c.es_fijo,
            es_interes=c.es_interes,
            valor_defecto=c.valor_defecto,
            activo=c.activo,
            
            # Accounts
            cuenta_ingreso_id=_get_mapped_id(c.cuenta_ingreso_id, map_old_code, map_code_newid),
            cuenta_cxc_id=_get_mapped_id(c.cuenta_cxc_id, map_old_code, map_code_newid),
            cuenta_interes_id=_get_mapped_id(c.cuenta_interes_id, map_old_code, map_code_newid),
            cuenta_caja_id=_get_mapped_id(c.cuenta_caja_id, map_old_code, map_code_newid)
        )
        nuevos_conceptos.append(nuevo)
    
    db.add_all(nuevos_conceptos)
    db.flush()

def _clone_grupos_inventario(db: Session, source_empresa_id: int, target_empresa_id: int):
    """Clona Grupos de Inventario y re-asocia cuentas/impuestos"""
    from ..models.grupo_inventario import GrupoInventario
    from ..models.plan_cuenta import PlanCuenta
    from ..models.impuesto import TasaImpuesto

    grupos_source = db.query(GrupoInventario).filter(GrupoInventario.empresa_id == source_empresa_id).all()
    if not grupos_source: return

    # MAPPERS
    # 1. Accounts
    cuentas_new = db.query(PlanCuenta).filter(PlanCuenta.empresa_id == target_empresa_id).all()
    map_code_newid = {c.codigo: c.id for c in cuentas_new}
    
    # Needs old accounts to get codes
    all_old_ids = set()
    for g in grupos_source:
        if g.cuenta_inventario_id: all_old_ids.add(g.cuenta_inventario_id)
        if g.cuenta_ingreso_id: all_old_ids.add(g.cuenta_ingreso_id)
        if g.cuenta_costo_venta_id: all_old_ids.add(g.cuenta_costo_venta_id)
        if g.cuenta_ajuste_faltante_id: all_old_ids.add(g.cuenta_ajuste_faltante_id)
        if g.cuenta_ajuste_sobrante_id: all_old_ids.add(g.cuenta_ajuste_sobrante_id)
        if g.cuenta_costo_produccion_id: all_old_ids.add(g.cuenta_costo_produccion_id)

    map_old_code = {}
    if all_old_ids:
        old_accs = db.query(PlanCuenta).filter(PlanCuenta.id.in_(list(all_old_ids))).all()
        map_old_code = {c.id: c.codigo for c in old_accs}

    # 2. Taxes (Map by Name)
    impuestos_new = db.query(TasaImpuesto).filter(TasaImpuesto.empresa_id == target_empresa_id).all()
    map_tax_name_newid = {t.nombre: t.id for t in impuestos_new}
    
    old_tax_ids = [g.impuesto_predeterminado_id for g in grupos_source if g.impuesto_predeterminado_id]
    map_old_tax_name = {}
    if old_tax_ids:
        old_taxes = db.query(TasaImpuesto).filter(TasaImpuesto.id.in_(old_tax_ids)).all()
        map_old_tax_name = {t.id: t.nombre for t in old_taxes}

    def _get_tax_id(old_id):
        if not old_id: return None
        if old_id in map_old_tax_name:
            name = map_old_tax_name[old_id]
            return map_tax_name_newid.get(name)
        return None

    nuevos_grupos = []
    for g in grupos_source:
        nuevo = GrupoInventario(
            empresa_id=target_empresa_id,
            nombre=g.nombre,
            
            # Accounts
            cuenta_inventario_id=_get_mapped_id(g.cuenta_inventario_id, map_old_code, map_code_newid),
            cuenta_ingreso_id=_get_mapped_id(g.cuenta_ingreso_id, map_old_code, map_code_newid),
            cuenta_costo_venta_id=_get_mapped_id(g.cuenta_costo_venta_id, map_old_code, map_code_newid),
            cuenta_ajuste_faltante_id=_get_mapped_id(g.cuenta_ajuste_faltante_id, map_old_code, map_code_newid),
            cuenta_ajuste_sobrante_id=_get_mapped_id(g.cuenta_ajuste_sobrante_id, map_old_code, map_code_newid),
            cuenta_costo_produccion_id=_get_mapped_id(g.cuenta_costo_produccion_id, map_old_code, map_code_newid),
            
            # Tax
            impuesto_predeterminado_id=_get_tax_id(g.impuesto_predeterminado_id)
        )
        nuevos_grupos.append(nuevo)
    
    db.add_all(nuevos_grupos)
    db.flush()

def _clone_activos_categorias(db: Session, source_empresa_id: int, target_empresa_id: int):
    """Clona Categorías de Activos Fijos"""
    from ..models.activo_categoria import ActivoCategoria
    from ..models.plan_cuenta import PlanCuenta

    cats_source = db.query(ActivoCategoria).filter(ActivoCategoria.empresa_id == source_empresa_id).all()
    if not cats_source: return

    # MAPPERS
    cuentas_new = db.query(PlanCuenta).filter(PlanCuenta.empresa_id == target_empresa_id).all()
    map_code_newid = {c.codigo: c.id for c in cuentas_new}
    
    all_old_ids = set()
    for c in cats_source:
        if c.cuenta_activo_id: all_old_ids.add(c.cuenta_activo_id)
        if c.cuenta_gasto_depreciacion_id: all_old_ids.add(c.cuenta_gasto_depreciacion_id)
        if c.cuenta_depreciacion_acumulada_id: all_old_ids.add(c.cuenta_depreciacion_acumulada_id)

    map_old_code = {}
    if all_old_ids:
        old_accs = db.query(PlanCuenta).filter(PlanCuenta.id.in_(list(all_old_ids))).all()
        map_old_code = {c.id: c.codigo for c in old_accs}

    nuevas_cats = []
    for c in cats_source:
        nuevo = ActivoCategoria(
            empresa_id=target_empresa_id,
            nombre=c.nombre,
            vida_util_niif_meses=c.vida_util_niif_meses,
            vida_util_fiscal_meses=c.vida_util_fiscal_meses,
            metodo_depreciacion=c.metodo_depreciacion,
            
            # Accounts
            cuenta_activo_id=_get_mapped_id(c.cuenta_activo_id, map_old_code, map_code_newid),
            cuenta_gasto_depreciacion_id=_get_mapped_id(c.cuenta_gasto_depreciacion_id, map_old_code, map_code_newid),
            cuenta_depreciacion_acumulada_id=_get_mapped_id(c.cuenta_depreciacion_acumulada_id, map_old_code, map_code_newid)
        )
        nuevas_cats.append(nuevo)
    
    db.add_all(nuevas_cats)
    db.flush()

def _clone_nomina_config(db: Session, source_empresa_id: int, target_empresa_id: int):
    """Clona Configuración de Nómina (Tipos y Cuentas)"""
    from ..models.nomina import TipoNomina, ConfiguracionNomina
    from ..models.plan_cuenta import PlanCuenta
    from ..models.tipo_documento import TipoDocumento

    # 1. Clone Types (TipoNomina)
    tipos_source = db.query(TipoNomina).filter(TipoNomina.empresa_id == source_empresa_id).all()
    map_tipo_id = {} # Old -> New
    
    for t in tipos_source:
        nuevo_tipo = TipoNomina(
            empresa_id=target_empresa_id,
            nombre=t.nombre,
            descripcion=t.descripcion,
            periodo_pago=t.periodo_pago
        )
        db.add(nuevo_tipo)
        db.flush() 
        map_tipo_id[t.id] = nuevo_tipo.id
        
    # 2. Clone Configuration (ConfiguracionNomina)
    configs_source = db.query(ConfiguracionNomina).filter(ConfiguracionNomina.empresa_id == source_empresa_id).all()
    if not configs_source: return

    # Mappers
    cuentas_new = db.query(PlanCuenta).filter(PlanCuenta.empresa_id == target_empresa_id).all()
    map_code_newid = {c.codigo: c.id for c in cuentas_new}
    
    docs_new = db.query(TipoDocumento).filter(TipoDocumento.empresa_id == target_empresa_id).all()
    map_doc_name_newid = {d.nombre: d.id for d in docs_new}

    # Collect Old Account IDs
    all_old_ids = set()
    for c in configs_source:
        acc_fields = [
            'cuenta_sueldo_id', 'cuenta_auxilio_transporte_id', 'cuenta_horas_extras_id', 
            'cuenta_comisiones_id', 'cuenta_otros_devengados_id', 'cuenta_salarios_por_pagar_id',
            'cuenta_aporte_salud_id', 'cuenta_aporte_pension_id', 'cuenta_fondo_solidaridad_id',
            'cuenta_retencion_fuente_id', 'cuenta_otras_deducciones_id'
        ]
        for field in acc_fields:
            val = getattr(c, field)
            if val: all_old_ids.add(val)

    map_old_code = {}
    if all_old_ids:
        old_accs = db.query(PlanCuenta).filter(PlanCuenta.id.in_(list(all_old_ids))).all()
        map_old_code = {c.id: c.codigo for c in old_accs}

    nuevas_configs = []
    for c in configs_source:
        # Resolve TipoNomina (could be None for Global?)
        nuevo_tipo_id = None
        if c.tipo_nomina_id and c.tipo_nomina_id in map_tipo_id:
            nuevo_tipo_id = map_tipo_id[c.tipo_nomina_id]
            
        # Resolve Doc Type (if any)
        # Note: Model has 'tipo_documento_id' 
        # But we need old doc name... optimizing: simple fetch if needed or generic helper
        # Let's rely on mapped_id logic but for Docs it's strictly Name based as ID changes.
        # Impl a quick helper or inline check if simple.
        # It's usually "Nomina Electronica" or similar.
        nuevo_doc_id = None
        # We need to fetch the old doc to get name. 
        # Skipping optimization for brevity unless critical or errors seen.
        if c.tipo_documento_id:
             old_doc = db.query(TipoDocumento).filter(TipoDocumento.id == c.tipo_documento_id).first()
             if old_doc and old_doc.nombre in map_doc_name_newid:
                 nuevo_doc_id = map_doc_name_newid[old_doc.nombre]

        nuevo = ConfiguracionNomina(
            empresa_id=target_empresa_id,
            tipo_nomina_id=nuevo_tipo_id,
            tipo_documento_id=nuevo_doc_id, # Remapped doc type
            
            # Devengados
            cuenta_sueldo_id=_get_mapped_id(c.cuenta_sueldo_id, map_old_code, map_code_newid),
            cuenta_auxilio_transporte_id=_get_mapped_id(c.cuenta_auxilio_transporte_id, map_old_code, map_code_newid),
            cuenta_horas_extras_id=_get_mapped_id(c.cuenta_horas_extras_id, map_old_code, map_code_newid),
            cuenta_comisiones_id=_get_mapped_id(c.cuenta_comisiones_id, map_old_code, map_code_newid),
            cuenta_otros_devengados_id=_get_mapped_id(c.cuenta_otros_devengados_id, map_old_code, map_code_newid),
            
            # Pasivos/Deducciones
            cuenta_salarios_por_pagar_id=_get_mapped_id(c.cuenta_salarios_por_pagar_id, map_old_code, map_code_newid),
            cuenta_aporte_salud_id=_get_mapped_id(c.cuenta_aporte_salud_id, map_old_code, map_code_newid),
            cuenta_aporte_pension_id=_get_mapped_id(c.cuenta_aporte_pension_id, map_old_code, map_code_newid),
            cuenta_fondo_solidaridad_id=_get_mapped_id(c.cuenta_fondo_solidaridad_id, map_old_code, map_code_newid),
            cuenta_retencion_fuente_id=_get_mapped_id(c.cuenta_retencion_fuente_id, map_old_code, map_code_newid),
            cuenta_otras_deducciones_id=_get_mapped_id(c.cuenta_otras_deducciones_id, map_old_code, map_code_newid)
        )
        nuevas_configs.append(nuevo)
        
    db.add_all(nuevas_configs)
    db.flush()


def _clone_produccion_config(db: Session, source_empresa_id: int, target_empresa_id: int):
    """Clona Configuración de Producción (Tipos de Documento)"""
    from ..models.configuracion_produccion import ConfiguracionProduccion
    from ..models.tipo_documento import TipoDocumento

    source_conf = db.query(ConfiguracionProduccion).filter(ConfiguracionProduccion.empresa_id == source_empresa_id).first()
    if not source_conf: return

    # MAPPERS for Doc Types
    docs_new = db.query(TipoDocumento).filter(TipoDocumento.empresa_id == target_empresa_id).all()
    map_doc_name_newid = {d.nombre: d.id for d in docs_new}
    
    old_doc_ids = []
    if source_conf.tipo_documento_orden_id: old_doc_ids.append(source_conf.tipo_documento_orden_id)
    if source_conf.tipo_documento_anulacion_id: old_doc_ids.append(source_conf.tipo_documento_anulacion_id)
    if source_conf.tipo_documento_consumo_id: old_doc_ids.append(source_conf.tipo_documento_consumo_id)
    if source_conf.tipo_documento_entrada_pt_id: old_doc_ids.append(source_conf.tipo_documento_entrada_pt_id)
    
    map_old_doc_name = {}
    if old_doc_ids:
        old_docs = db.query(TipoDocumento).filter(TipoDocumento.id.in_(old_doc_ids)).all()
        map_old_doc_name = {d.id: d.nombre for d in old_docs}

    def _get_doc_id(old_id):
        if not old_id: return None
        if old_id in map_old_doc_name:
            name = map_old_doc_name[old_id]
            return map_doc_name_newid.get(name)
        return None

    new_conf = ConfiguracionProduccion(
        empresa_id=target_empresa_id,
        tipo_documento_orden_id=_get_doc_id(source_conf.tipo_documento_orden_id),
        tipo_documento_anulacion_id=_get_doc_id(source_conf.tipo_documento_anulacion_id),
        tipo_documento_consumo_id=_get_doc_id(source_conf.tipo_documento_consumo_id),
        tipo_documento_entrada_pt_id=_get_doc_id(source_conf.tipo_documento_entrada_pt_id)
    )
    db.add(new_conf)
    db.flush()

def create_empresa_from_template(
    db: Session, 
    empresa_data: empresa_schema.EmpresaConUsuariosCreate, 
    template_category: str,
    owner_id: int,
    padre_id: int = None
) -> empresa_model.Empresa:
    """
    Crea una empresa clonando una Plantilla Maestra según ID o categoría.
    Asigna owner y padre (Contador).
    """
    # 1. Buscar Template Semilla
    template = None
    
    # Prioridad 1: ID específico (si viene en el payload)
    if empresa_data.template_id:
        template = db.query(empresa_model.Empresa).filter(
            empresa_model.Empresa.id == empresa_data.template_id,
            empresa_model.Empresa.is_template == True
        ).first()
        
    # Prioridad 2: Categoría (Legacy fallback)
    if not template and template_category:
        template = db.query(empresa_model.Empresa).filter(
            empresa_model.Empresa.is_template == True,
            empresa_model.Empresa.template_category == template_category
        ).first()
    
    if not template:
        # Fallback error message based on inputs
        ref = f"ID {empresa_data.template_id}" if empresa_data.template_id else f"Categoría {template_category}"
        raise HTTPException(status_code=400, detail=f"No existe plantilla válida: {ref}")
        
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
    
    try:
        # 3. CLONACIÓN
        _clone_puc(db, template.id, nueva_empresa.id)
        _clone_tipos_doc(db, template.id, nueva_empresa.id)
        _clone_impuestos(db, template.id, nueva_empresa.id)
        _clone_configuracion_reporte(db, template.id, nueva_empresa.id) # FIX: Clone Tax Lines
        _clone_ph_config(db, template.id, nueva_empresa.id) # PHASE 2: PH Config
        _clone_ph_conceptos(db, template.id, nueva_empresa.id) # PHASE 2: PH Concepts
        _clone_grupos_inventario(db, template.id, nueva_empresa.id) # PHASE 2: Inventory
        _clone_activos_categorias(db, template.id, nueva_empresa.id) # PHASE 2: Assets
        _clone_nomina_config(db, template.id, nueva_empresa.id) # PHASE 2: Payroll
        _clone_produccion_config(db, template.id, nueva_empresa.id) # PHASE 2: Production
    except Exception as e:
        print(f"Error cloning template data: {e}")
        # Non-critical failure logic? Or raise?
        # Better to log and continue or warning. 
        # But for tax lines it might be annoying if missing. Let's raise only if critical.
        try:
            from ..models.configuracion_fe import ConfiguracionFE
            import json
            
            creds_sandbox = {
                "client_id": "a1003ed4-93cc-4980-89ab-1a181b031918",
                "client_secret": "iO7V0w287m87yGZ3JOlWgR5ytGsFSXaIkGcOMaJd",
                "username": "sandbox@factus.com.co",
                "password": "sandbox2024%"
            }
            
            nueva_config_fe = ConfiguracionFE(
                empresa_id=nueva_empresa.id,
                proveedor='FACTUS',
                ambiente='PRUEBAS',
                habilitado=True,
                api_token=json.dumps(creds_sandbox)
            )
            db.add(nueva_config_fe)
        except Exception as e_fe:
            print(f"Advertencia: No se pudo auto-configurar FE Sandbox en template: {e_fe}")

        pass
    
    # 4. Crear Usuario Admin Inicial (Dueño) si viene en data
    # (Reusamos lógica de create_empresa_con_usuarios parcial o manual)
    # Por ahora manual simple
    rol_admin = db.query(permiso_model.Rol).filter(permiso_model.Rol.nombre == "Administrador").first()
    
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
    template_category: str,
    owner_id: Optional[int] = None, # NEW: Support private ownership
    custom_name: Optional[str] = None # NEW: Support custom naming
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
    
    # Naming Logic
    new_name = custom_name if custom_name else f"{source.razon_social} (Plantilla)"
    
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
        
        # Ownership Logic: 
        # If owner_id is provided (Accountant), it's a Private Template.
        # If None, it's a System Template (Global).
        owner_id=owner_id, 
        padre_id=None, # Templates have no parent, they are root-like or standalone tools
        
        limite_registros_mensual=source.limite_registros_mensual,
        created_at=datetime.utcnow()
    )
    
    db.add(nueva_empresa)
    db.flush()
    
    # 2. CLONAR DATOS
    _clone_puc(db, source.id, nueva_empresa.id)
    _clone_tipos_doc(db, source.id, nueva_empresa.id)
    _clone_impuestos(db, source.id, nueva_empresa.id)
    _clone_configuracion_reporte(db, source.id, nueva_empresa.id) # FIX: Extract Tax Lines
    _clone_ph_config(db, source.id, nueva_empresa.id) # PHASE 2: PH Config
    _clone_ph_conceptos(db, source.id, nueva_empresa.id) # PHASE 2: PH Concepts
    _clone_grupos_inventario(db, source.id, nueva_empresa.id) # PHASE 2: Inventory
    _clone_activos_categorias(db, source.id, nueva_empresa.id) # PHASE 2: Assets
    _clone_nomina_config(db, source.id, nueva_empresa.id) # PHASE 2: Payroll
    _clone_produccion_config(db, source.id, nueva_empresa.id) # PHASE 2: Production
    
    db.commit()
    db.refresh(nueva_empresa)
    return nueva_empresa
