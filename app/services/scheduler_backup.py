
import os
import json
import logging
import zipfile
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services import migracion as migracion_service
from app.models.empresa import Empresa

# Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.models.configuracion_sistema import ConfiguracionSistema

def _save_to_db(full_config):
    db: Session = SessionLocal()
    try:
        conf = db.query(ConfiguracionSistema).filter(ConfiguracionSistema.clave == "backup_config").first()
        val = json.dumps(full_config, indent=4)
        if conf:
            conf.valor = val
        else:
            conf = ConfiguracionSistema(clave="backup_config", valor=val)
            db.add(conf)
        db.commit()
    except Exception as e:
        logger.error(f"[AutoBackup] Error saving to DB: {e}")
        db.rollback()
    finally:
        db.close()

scheduler = BackgroundScheduler()

def get_global_backup_path() -> str:
    """Devuelve la ruta configurada para los backups globales"""
    try:
        cfg = load_config("global")
        return cfg.get("ruta_local", "C:/Backups_Finaxis")
    except Exception:
        return "C:/Backups_Finaxis"

def load_config(empresa_id=None):
    """
    Carga la configuración.
    Si empresa_id es None, devuelve TODO el JSON (estructura interna).
    Si empresa_id es int, devuelve la config específica de esa empresa (o default).
    Si empresa_id es 'global', devuelve la config global.
    """
    logger.info(f"[AutoBackup] LOADING CONFIG from DATABASE")
    
    default_global = {"enabled": False, "hora_ejecucion": "00:00", "ruta_local": "C:/Backups_Finaxis", "dias_retencion": 7, "last_run": None}
    default_config = {"enabled": False, "hora_ejecucion": "02:00", "ruta_local": "C:/Backups_Finaxis", "dias_retencion": 30}
    
    from app.models.configuracion_sistema import ConfiguracionSistema
    db: Session = SessionLocal()
    try:
        conf = db.query(ConfiguracionSistema).filter(ConfiguracionSistema.clave == "backup_config").first()
        if conf and conf.valor:
            full_config = json.loads(conf.valor)
        else:
            full_config = {"companies": {}, "global": default_global}
    except Exception as e:
        logger.error(f"[AutoBackup] Error loading from DB: {e}")
        full_config = {"companies": {}, "global": default_global}
    finally:
        db.close()

    if "companies" not in full_config:
        logger.info("[AutoBackup] Migrating legacy config to multi-tenant format...")
        full_config["companies"] = {} 
    
    if "global" not in full_config:
        full_config["global"] = default_global

    if empresa_id is None:
        return full_config
        
    if empresa_id == "global":
        return full_config.get("global", default_global)
    
    # Retornar config específica para una empresa
    str_id = str(empresa_id)
    return full_config.get("companies", {}).get(str_id, default_config)

def save_config(config_data, empresa_id):
    """
    Guarda la configuración para una empresa específica.
    """
    full_config = load_config(empresa_id=None)
    str_id = str(empresa_id)
    
    # Asegurar estructura
    if "companies" not in full_config:
        full_config["companies"] = {}

    # Preservar datos internos que no vienen del frontend (como last_run) si existen
    current_saved = full_config["companies"].get(str_id, {})
    if "last_run" in current_saved:
        config_data["last_run"] = current_saved["last_run"]
        
    full_config["companies"][str_id] = config_data
    
    logger.info(f"[AutoBackup] SAVING CONFIG for Company {empresa_id} to DATABASE")
    logger.info(f"[AutoBackup] Config Data: {config_data}")
    
    _save_to_db(full_config)
        
    # Recargar scheduler para aplicar cambios
    logger.info(f"[AutoBackup] Config updated for Company {empresa_id}. Reloading scheduler.")
    schedule_backup_jobs()

def save_global_config(config_data):
    full_config = load_config(empresa_id=None)
    current_global = full_config.get("global", {})
    if "last_run" in current_global:
        config_data["last_run"] = current_global["last_run"]
    
    full_config["global"] = config_data
    _save_to_db(full_config)
        
    logger.info(f"[AutoBackup] Global config updated. Reloading scheduler.")
    schedule_backup_jobs()

def run_global_backup():
    """
    Ejecuta el backup global de todas las empresas y las comprime en un ZIP EN MEMORIA,
    para luego guardar todo nativamente en PostgreSQL mediante CopiaSeguridad.
    Puede ser invocado manualmente o por el scheduler.
    """
    logger.info("[AutoBackup] Iniciando Backup Global...")
    import io
    from app.models.copia_seguridad import CopiaSeguridad
    
    db: Session = SessionLocal()
    try:
        empresas = db.query(Empresa).all()
        if not empresas:
            logger.info("[AutoBackup] No hay empresas registradas para respaldar.")
            return
            
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        zip_filename = f"BACKUP_GLOBAL_{timestamp}.zip"
        
        in_memory_zip = io.BytesIO()
        with zipfile.ZipFile(in_memory_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for emp in empresas:
                try:
                    logger.info(f"[AutoBackup] Respaldando empresa: {emp.razon_social} (ID: {emp.id})")
                    backup_data = migracion_service.generar_backup_json(db, emp.id, filtros=None)
                    
                    safe_name = "".join([c for c in emp.razon_social if c.isalnum() or c in (' ', '-', '_')]).strip()
                    json_filename = f"{emp.id}_{safe_name}.json"
                    
                    json_str = json.dumps(backup_data, default=str, ensure_ascii=False)
                    zipf.writestr(json_filename, json_str.encode('utf-8'))
                except Exception as e:
                    logger.error(f"[AutoBackup] Error en empresa {emp.id}: {e}")
                    
        in_memory_zip.seek(0)
        zip_bytes = in_memory_zip.read()
        tamano_mb = str(round(len(zip_bytes) / (1024 * 1024), 2))
        
        backup_record = CopiaSeguridad(
            empresa_id=None,
            nombre_archivo=zip_filename,
            datos_json=zip_bytes,
            tamanio_mb=tamano_mb
        )
        db.add(backup_record)
        db.commit()
        logger.info(f"[AutoBackup] Backup Global Exitoso guardado en BD!")
        
        full_config = load_config(empresa_id=None)
        if "global" not in full_config:
            full_config["global"] = {}
        full_config["global"]["last_run"] = datetime.now().isoformat()
        _save_to_db(full_config)
            
        cfg = load_config("global")
        _apply_global_retention_policy_db(db, cfg.get("dias_retencion", 7))
        
        return True
        
    except Exception as e:
        logger.error(f"[AutoBackup] Error fatal en Backup Global: {e}")
        return False
    finally:
        db.close()

def get_global_backup_files():
    """Lista todos los backups globales almacenados en la base de datos."""
    from app.models.copia_seguridad import CopiaSeguridad
    db: Session = SessionLocal()
    archivos = []
    try:
        backups = db.query(CopiaSeguridad).filter(CopiaSeguridad.empresa_id == None).order_by(CopiaSeguridad.fecha.desc()).all()
        for b in backups:
            archivos.append({
                "filename": b.nombre_archivo,
                "size_mb": float(b.tamanio_mb) if b.tamanio_mb else 0.0,
                "created_at": b.fecha.isoformat()
            })
        return archivos
    except Exception as e:
        logger.error(f"Error listando backups DB: {e}")
        return []
    finally:
        db.close()

def get_global_backup_by_name(filename: str):
    from app.models.copia_seguridad import CopiaSeguridad
    db: Session = SessionLocal()
    try:
        return db.query(CopiaSeguridad).filter(CopiaSeguridad.nombre_archivo == filename, CopiaSeguridad.empresa_id == None).first()
    finally:
        db.close()

def delete_global_backup_file(filename: str) -> bool:
    """Borra físicamente un archivo de backup en BD"""
    from app.models.copia_seguridad import CopiaSeguridad
    db: Session = SessionLocal()
    try:
        backup = db.query(CopiaSeguridad).filter(CopiaSeguridad.nombre_archivo == filename, CopiaSeguridad.empresa_id == None).first()
        if backup:
            db.delete(backup)
            db.commit()
            logger.info(f"[AutoBackup] Usuario eliminó backup de BD: {filename}")
            return True
        return False
    except Exception as e:
        logger.error(f"[AutoBackup] Error eliminando {filename}: {e}")
        return False
    finally:
        db.close()

def _apply_global_retention_policy_db(db, days):
    from app.models.copia_seguridad import CopiaSeguridad
    try:
        cutoff = datetime.now() - timedelta(days=days)
        viejos = db.query(CopiaSeguridad).filter(CopiaSeguridad.empresa_id == None, CopiaSeguridad.fecha < cutoff).all()
        for v in viejos:
            db.delete(v)
            logger.info(f"[AutoBackup] Deleted old global backup from DB: {v.nombre_archivo}")
        db.commit()
    except Exception as e:
        logger.warning(f"[AutoBackup] Global retention policy error: {e}")

def run_backup_for_company(empresa_id: int):
    """
    Ejecuta el backup para una empresa específica en BD.
    """
    cfg = load_config(empresa_id)
    if not cfg.get("enabled", False):
        return

    from app.models.copia_seguridad import CopiaSeguridad
    db: Session = SessionLocal()
    try:
        emp = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        if not emp:
            logger.warning(f"[AutoBackup] Company {empresa_id} not found. Skipping.")
            return

        logger.info(f"[AutoBackup] Processing Company: {emp.razon_social} (ID: {emp.id})")
        
        _update_last_run(empresa_id)
        
        backup_data = migracion_service.generar_backup_json(db, emp.id, filtros=None)
        
        safe_name = "".join([c for c in emp.razon_social if c.isalnum() or c in (' ', '-', '_')]).strip()
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"BACKUP_AUTO_{safe_name}_{timestamp}.json"
        
        json_str = json.dumps(backup_data, default=str, ensure_ascii=False)
        json_bytes = json_str.encode('utf-8')
        tamano_mb = str(round(len(json_bytes) / (1024 * 1024), 2))
        
        backup_record = CopiaSeguridad(
            empresa_id=empresa_id,
            nombre_archivo=filename,
            datos_json=json_bytes,
            tamanio_mb=tamano_mb
        )
        db.add(backup_record)
        db.commit()
        
        logger.info(f"[AutoBackup] Success! Saved to Database {filename}")
        
        _apply_retention_policy_db(db, cfg.get("dias_retencion", 30), empresa_id)

    except Exception as e:
        logger.error(f"[AutoBackup] Error backing up company {empresa_id}: {e}")
    finally:
        db.close()

def _update_last_run(empresa_id):
    full_config = load_config(empresa_id=None)
    str_id = str(empresa_id)
    if str_id in full_config.get("companies", {}):
        full_config["companies"][str_id]["last_run"] = datetime.now().isoformat()
        _save_to_db(full_config)

def _apply_retention_policy_db(db, days, empresa_id):
    """
    Elimina backups viejos nativamente en BD.
    """
    from app.models.copia_seguridad import CopiaSeguridad
    try:
        cutoff = datetime.now() - timedelta(days=days)
        viejos = db.query(CopiaSeguridad).filter(CopiaSeguridad.empresa_id == empresa_id, CopiaSeguridad.fecha < cutoff).all()
        for v in viejos:
            db.delete(v)
            logger.info(f"[AutoBackup] Deleted old company backup: {v.nombre_archivo}")
        db.commit()
    except Exception as e:
        logger.warning(f"[AutoBackup] Retention policy error DB: {e}")

def _parse_time(hora_str: str):
    """
    Intenta parsear la hora en diferentes formatos comunes.
    Soporta: "HH:MM" (24h), "HH:MM AM/PM", "H:MM a. m.", etc.
    """
    hora_str = hora_str.strip().lower().replace(".", "").replace(" ", "") # Limpiar puntos y espacios: "a. m." -> "am"
    
    # Intentar 24h (HH:MM)
    try:
        return datetime.strptime(hora_str, "%H:%M").time()
    except ValueError:
        pass
        
    # Intentar 12h (HH:MM am/pm)
    # Ajustamos formatos para manejar la cadena sin espacios que generamos arriba (ej: "09:41am")
    formats = ["%I:%M%p", "%I:%M %p", "%H:%M%p", "%H:%M %p"]
    for fmt in formats:
        try:
            return datetime.strptime(hora_str, fmt).time()
        except ValueError:
            continue
            
    # Si falla todo, loguear y retornar default
    logger.error(f"[AutoBackup] No se pudo parsear el formato de hora: '{hora_str}'. Usando 03:00 por defecto.")
    return datetime.strptime("03:00", "%H:%M").time()

def _check_missed_job(cfg, job_callback, str_id, now, is_global=False):
    if not cfg.get("enabled", False):
        return
        
    try:
        hora_str = cfg.get("hora_ejecucion", "00:00")
        scheduled_time_obj = _parse_time(hora_str)
        scheduled_time = now.replace(
            hour=scheduled_time_obj.hour, 
            minute=scheduled_time_obj.minute, 
            second=0, 
            microsecond=0
        )
        
        last_run_str = cfg.get("last_run")
        last_run = datetime.fromisoformat(last_run_str) if last_run_str else None
        
        logger.info(f"[AutoBackup] Checking {str_id}: Scheduled={scheduled_time}, LastRun={last_run}, Now={now}")
        
        should_run = False
        if not last_run:
            if now > scheduled_time:
                should_run = True
                logger.info(f"[AutoBackup] Case: No last_run and already passed scheduled time.")
        else:
            if last_run.date() < now.date() and now > scheduled_time:
                should_run = True
                logger.info(f"[AutoBackup] Case: Last run was yesterday or before, and already passed scheduled time today.")
        
        if should_run:
            logger.warning(f"[AutoBackup] MISSED BACKUP DETECTED for {'GLOBAL' if is_global else 'Company ' + str_id}. Running NOW.")
            if is_global:
                job_callback()
            else:
                job_callback(int(str_id))
                
    except Exception as e:
        logger.error(f"[AutoBackup] Error checking missed backup for {str_id}: {e}", exc_info=True)

def check_missed_backups():
    """
    Revisa si alguna empresa tenía un backup programado que NO corrió hoy.
    Esto soluciona el problema de "computador apagado a la hora X".
    Se debe llamar al inicio del sistema.
    """
    logger.info("[AutoBackup] Checking for missed backups...")
    full_config = load_config(empresa_id=None)
    companies = full_config.get("companies", {})
    global_cfg = full_config.get("global", {})
    
    now = datetime.now()
    
    _check_missed_job(global_cfg, run_global_backup, "GLOBAL", now, is_global=True)
    
    for str_id, cfg in companies.items():
        _check_missed_job(cfg, run_backup_for_company, str_id, now)

def schedule_backup_jobs():
    """
    Programa los jobs individuales para cada empresa.
    """
    config = load_config(empresa_id=None)
    companies = config.get("companies", {})
    
    scheduler.remove_all_jobs()
    
    for str_id, cfg in companies.items():
        if cfg.get("enabled", False):
            try:
                empresa_id = int(str_id)
                time_str = cfg.get("hora_ejecucion", "03:00")
                target_time = _parse_time(time_str)
                hour, minute = target_time.hour, target_time.minute
                
                # Usamos un closure o partial para capturar el valor actual de empresa_id
                job_id = f"backup_company_{empresa_id}"
                
                scheduler.add_job(
                    run_backup_for_company, 
                    CronTrigger(hour=hour, minute=minute), 
                    args=[empresa_id],
                    id=job_id,
                    replace_existing=True
                )
                logger.info(f"[AutoBackup] Scheduled backup for Company {empresa_id} at {time_str}")
            except ValueError:
                logger.error(f"[AutoBackup] Invalid time format for company {str_id}")

    # Scheduled Global Backup
    global_cfg = config.get("global", {})
    if global_cfg.get("enabled", False):
        try:
            time_str = global_cfg.get("hora_ejecucion", "00:00")
            target_time = _parse_time(time_str)
            hour, minute = target_time.hour, target_time.minute
            
            scheduler.add_job(
                run_global_backup, 
                CronTrigger(hour=hour, minute=minute), 
                id="backup_global",
                replace_existing=True
            )
            logger.info(f"[AutoBackup] Scheduled GLOBAL backup at {time_str}")
        except ValueError:
            logger.error(f"[AutoBackup] Invalid time format for global backup")

def start_scheduler():
    # 1. Configurar y arrancar jobs
    schedule_backup_jobs()
    
    if not scheduler.running:
        scheduler.start()
        logger.info("[AutoBackup] Scheduler started.")
        
    # 2. Verificar backups perdidos DE FORMA ASÍNCRONA (Job)
    # No bloquear el arranque. Programar para dentro de 60 segundos.
    run_date = datetime.now() + timedelta(seconds=60)
    scheduler.add_job(
        check_missed_backups, 
        'date', 
        run_date=run_date,
        id='check_missed_backups_delayed'
    )
    logger.info(f"[AutoBackup] Missed backup check scheduled for {run_date}")
