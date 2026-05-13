from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.models.permiso import Rol
from app.services.usuario import get_password_hash
from pydantic import BaseModel
from typing import Optional
from datetime import date

router = APIRouter(prefix="/setup", tags=["setup"])

class InitialSetupSchema(BaseModel):
    razon_social: str
    nit: str
    fecha_inicio: Optional[date] = None  # Default: hoy
    admin_email: str
    admin_password: str

@router.get("/check")
def check_setup_needed():
    """Verifica si el sistema necesita configuración inicial (si hay 0 empresas)."""
    import os as _os
    
    # ═══════════════════════════════════════════════
    # SONDA DE DIAGNÓSTICO — eliminar en producción
    # ═══════════════════════════════════════════════
    import app.core.database as _dbm
    _appdata = _os.getenv('APPDATA', 'N/A')
    _config_path = _os.path.join(_appdata, "Finaxis", "config.json") if _appdata != 'N/A' else 'N/A'
    _config_exists = _os.path.exists(_config_path) if _config_path != 'N/A' else False
    _config_content = 'NO EXISTE'
    if _config_exists:
        try:
            import json as _json
            with open(_config_path) as _f:
                _config_content = str(_json.load(_f))
        except Exception as _e:
            _config_content = f'ERROR LEYENDO: {_e}'
    
    _engine_url = str(_dbm._last_db_url) if _dbm._last_db_url else 'MOTOR NO INICIALIZADO'
    
    print("=" * 60)
    print("[SONDA /setup/check] DIAGNÓSTICO COMPLETO")
    print(f"  APPDATA          : {_appdata}")
    print(f"  config.json path : {_config_path}")
    print(f"  config.json existe: {_config_exists}")
    print(f"  config.json valor: {_config_content}")
    print(f"  Motor DB activo  : {_engine_url}")
    print("=" * 60)
    # ═══════════════════════════════════════════════
    
    # PRE-CHECK: Evitar que SQLAlchemy cree un finaxis_local.db vacío
    if _engine_url.startswith("sqlite:///"):
        _db_path = _engine_url.replace("sqlite:///", "")
        if not _os.path.exists(_db_path):
            print(f"[SONDA /setup/check] Base local no existe ({_db_path}) → setup_needed=True")
            return {"setup_needed": True}
    
    db = SessionLocal()
    try:
        count = db.query(Empresa).execution_options(ignore_tenant=True).count()
        print(f"[SONDA /setup/check] Empresas encontradas: {count} → setup_needed={count == 0}")
        return {"setup_needed": count == 0}
    except Exception as e:
        print(f"[SONDA /setup/check] ERROR al contar empresas: {e} → redirigiendo al wizard")
        return {"setup_needed": True}
    finally:
        db.close()

@router.post("/reset")
def reset_configuration():
    """Elimina la configuración de red y vuelve al modo SQLite local (para reinstalación limpia)."""
    import os, json
    appdata = os.getenv('APPDATA')
    if appdata:
        config_path = os.path.join(appdata, "Finaxis", "config.json")
        if os.path.exists(config_path):
            try:
                os.remove(config_path)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"No se pudo eliminar la configuración: {e}")
    
    # Forzar reinicio del engine al SQLite
    import app.core.database as db_module
    if db_module._engine:
        db_module._engine.dispose()
    db_module._engine = None
    db_module._last_db_url = None
    db_module._SessionLocal = None
    
    return {"status": "success", "message": "Configuración restablecida. El sistema volverá al asistente de inicio."}

@router.post("/initialize")
def initialize_system(data: InitialSetupSchema):
    """Crea la primera empresa y el administrador global."""
    import app.core.database as db_module
    from app.core.database import Base
    from app.core.seeder import seed_database

    # ── BOOTSTRAP: Crear tablas y sembrar datos maestros si es una instalación nueva ──
    # Esto es esencial para el modo monousuario donde /config-db nunca se llama.
    try:
        current_engine = db_module.get_engine()
        print(f"[Setup/Initialize] Bootstrapping DB: {str(current_engine.url)[:50]}...")
        Base.metadata.create_all(bind=current_engine)
        print("[Setup/Initialize] Tablas creadas. Ejecutando seeder...")
        seed_database()
        print("[Setup/Initialize] Seeder completado. Procediendo a crear empresa...")
    except Exception as e:
        import traceback
        print(f"[Setup/Initialize] ERROR en bootstrap: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error preparando la base de datos: {str(e)}")

    db = SessionLocal()
    try:
        # 1. Verificación inteligente: ¿El sistema ya fue inicializado POR EL CLIENTE?
        #    Solo bloquear si hay empresas CON usuarios reales (no solo soporte@soporte.com)
        empresas_existentes = db.query(Empresa).execution_options(ignore_tenant=True).all()
        if empresas_existentes:
            EMAILS_SISTEMA = {"soporte@soporte.com", "soporte@finaxis.com", "admin@finaxis.com"}
            usuarios_reales = db.query(Usuario).execution_options(ignore_tenant=True).filter(
                ~Usuario.email.in_(EMAILS_SISTEMA)
            ).all()

            if usuarios_reales:
                emails = [u.email for u in usuarios_reales]
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"El sistema ya ha sido inicializado anteriormente. Usuarios detectados: {', '.join(emails)}"
                )
            else:
                # Solo datos del Seeder — limpiar empresas fantasma y continuar
                print(f"[Setup/Initialize] {len(empresas_existentes)} empresa(s) del Seeder sin usuarios reales. Limpiando...")
                for emp in empresas_existentes:
                    db.delete(emp)
                db.flush()
                print("[Setup/Initialize] Limpieza completada. Continuando registro del cliente...")

        # 2. Buscar el Rol Administrador (debe existir luego del seeder)
        rol_admin = db.query(Rol).filter(Rol.nombre == "Administrador").first()
        if not rol_admin:
            # Fallback de emergencia
            rol_admin = Rol(nombre="Administrador", descripcion="Administrador Global")
            db.add(rol_admin)
            db.flush()

        # 3. Crear la Empresa
        from datetime import date as date_type
        nueva_empresa = Empresa(
            razon_social=data.razon_social,
            nit=data.nit,
            fecha_inicio_operaciones=data.fecha_inicio or date_type.today(),
            limite_registros_mensual=200
        )
        db.add(nueva_empresa)
        db.flush()

        # 4. Crear el Usuario Administrador
        nuevo_usuario = Usuario(
            email=data.admin_email,
            nombre_completo="Administrador Principal",
            password_hash=get_password_hash(data.admin_password),
            empresa_id=nueva_empresa.id
        )
        nuevo_usuario.roles.append(rol_admin)
        db.add(nuevo_usuario)

        db.commit()
        print(f"[Setup/Initialize] ✅ Sistema inicializado: empresa '{data.razon_social}', admin '{data.admin_email}'")
        return {"status": "success", "message": "Sistema inicializado correctamente. Ya puede iniciar sesión."}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        print(f"[Setup/Initialize] ERROR al crear empresa/usuario: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error en la inicialización: {str(e)}")
    finally:
        db.close()

class DBConfigSchema(BaseModel):
    database_url: str

@router.post("/config-db")
def configure_database(data: DBConfigSchema):
    """Prueba y guarda la configuración de la base de datos (Postgres o SQLite)."""
    import os
    import json
    from sqlalchemy import create_engine

    # 1. Si es PostgreSQL, crear la base de datos automáticamente si no existe
    if data.database_url.startswith("postgresql"):
        try:
            # Parsear URL para conectar al servidor sin especificar la DB destino
            from urllib.parse import urlparse
            parsed = urlparse(data.database_url)
            dbname = parsed.path.lstrip('/')
            # Conectar a la BD 'postgres' (siempre existe) para poder crear la nueva
            server_url = data.database_url.replace(f"/{dbname}", "/postgres")
            
            admin_engine = create_engine(server_url, isolation_level="AUTOCOMMIT")
            with admin_engine.connect() as conn:
                # Verificar si la DB ya existe
                result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{dbname}'"))
                exists = result.fetchone()
                if not exists:
                    print(f"[Setup/config-db] Creando base de datos '{dbname}'...")
                    conn.execute(text(f'CREATE DATABASE "{dbname}" ENCODING \'UTF8\''))
                    print(f"[Setup/config-db] ✅ Base de datos '{dbname}' creada.")
                else:
                    print(f"[Setup/config-db] Base de datos '{dbname}' ya existe.")
            admin_engine.dispose()
        except Exception as e:
            print(f"[Setup/config-db] Advertencia al crear DB: {e}")
            # No fallar aquí — intentar la conexión directa a continuación

    # 2. Probar conexión final a la base de datos destino
    try:
        test_engine = create_engine(data.database_url)
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        test_engine.dispose()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de conexión con la base de datos: {str(e)}"
        )

    # 2. Guardar persistentemente en APPDATA
    appdata = os.getenv('APPDATA')
    if not appdata:
        raise HTTPException(status_code=500, detail="No se pudo determinar la carpeta APPDATA.")
    
    db_dir = os.path.join(appdata, "Finaxis")
    os.makedirs(db_dir, exist_ok=True)
    config_path = os.path.join(db_dir, "config.json")

    config_data = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        except:
            pass
    
    config_data["DATABASE_URL"] = data.database_url
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=4)
        
        # --- INICIALIZACIÓN INMEDIATA CON INVALIDACIÓN DE CACHÉ ---
        import app.core.database as db_module
        from app.core.database import Base
        from app.core.seeder import seed_database
        
        # 1. Forzar invalidación del caché del engine para que lea el nuevo config.json
        if db_module._engine:
            db_module._engine.dispose()
        db_module._engine = None
        db_module._last_db_url = None
        db_module._SessionLocal = None
        
        # 2. Re-inicializar con la nueva URL
        new_engine = db_module.get_engine()
        print(f"[Setup] Motor inicializado: {db_module._last_db_url[:30]}...")
        
        # 3. Crear tablas en la nueva DB
        print(f"[Setup] Creando tablas...")
        Base.metadata.create_all(bind=new_engine)
        
        # 4. Sembrar datos maestros (roles, permisos, usuario soporte)
        print(f"[Setup] Ejecutando Sembrado Maestro...")
        seed_database()
        
    except Exception as e:
        import traceback
        print(f"[Setup ERROR] {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error configurando la base de datos: {str(e)}")

    return {"status": "success", "message": "Base de datos configurada e inicializada correctamente."}

@router.post("/migrate-data")
def migrate_local_to_network(data: DBConfigSchema):
    """Mueve los datos de la base de datos local (SQLite) a la configurada (Postgres)."""
    import os
    from app.services.migration import run_sqlite_to_postgres_migration
    
    # 1. Determinar ruta SQLite local (Default en APPDATA)
    appdata = os.getenv('APPDATA')
    if not appdata:
         raise HTTPException(status_code=500, detail="Entorno no compatible para migración automática.")
    
    sqlite_path = os.path.join(appdata, "Finaxis", "contapy.db")
    if not os.path.exists(sqlite_path):
        # Intentar ruta desarrollo por si acaso
        sqlite_path = "./contapy.db"
        if not os.path.exists(sqlite_path):
             raise HTTPException(status_code=404, detail="No se encontró la base de datos SQLite local para migrar.")

    sqlite_url = f"sqlite:///{sqlite_path}"
    postgres_url = data.database_url

    try:
        results = run_sqlite_to_postgres_migration(sqlite_url, postgres_url)
        return {
            "status": "success", 
            "message": "Datos migrados con éxito.",
            "details": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante la migración: {str(e)}")
