
import os
import json
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services import migracion as migracion_service
from app.models.empresa import Empresa

# Config
CONFIG_FILE = "backup_config.json"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def load_config(empresa_id=None):
    """
    Carga la configuración. 
    Si empresa_id es None, devuelve TODO el JSON (estructura interna).
    Si empresa_id es int, devuelve la config específica de esa empresa (o default).
    """
    default_config = {"enabled": False, "hora_ejecucion": "03:00", "ruta_local": "C:/Backups_Finaxis", "dias_retencion": 30, "last_run": None}
    
    if not os.path.exists(CONFIG_FILE):
        full_config = {"companies": {}}
    else:
        try:
            with open(CONFIG_FILE, "r") as f:
                full_config = json.load(f)
            
            # MIGRACIÓN AUTOMÁTICA DE FORMATO LEGACY (FLAT) A MULTI-EMPRESA
            if "companies" not in full_config:
                logger.info("[AutoBackup] Migrating legacy config to multi-tenant format...")
                # Asumimos que la config antigua era global, pero ahora debe quedar vacía o asignada a alguien. 
                # Por seguridad, la dejamos como base para nuevas, pero iniciamos "companies" vacío
                # o podríamos intentar asignarla a la primera empresa encontrada. 
                # Decisión: Resetear estructura a limpio para evitar backups cruzados accidentales, 
                # el usuario deberá reconfigurar para estar seguro.
                full_config = {"companies": {}} 
                
        except:
            full_config = {"companies": {}}

    if empresa_id is None:
        return full_config
    
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
    
    with open(CONFIG_FILE, "w") as f:
        json.dump(full_config, f, indent=4)
        
    # Recargar scheduler para aplicar cambios
    logger.info(f"[AutoBackup] Config updated for Company {empresa_id}. Reloading scheduler.")
    schedule_backup_jobs()

def run_backup_for_company(empresa_id: int):
    """
    Ejecuta el backup para una empresa específica.
    """
    cfg = load_config(empresa_id)
    if not cfg.get("enabled", False):
        return

    path = cfg.get("ruta_local", "C:/Backups_Finaxis")
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except Exception as e:
            logger.error(f"[AutoBackup] Failed to create directory {path}: {e}")
            return

    db: Session = SessionLocal()
    try:
        emp = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        if not emp:
            logger.warning(f"[AutoBackup] Company {empresa_id} not found. Skipping.")
            return

        logger.info(f"[AutoBackup] Processing Company: {emp.razon_social} (ID: {emp.id})")
        
        # 1. Generate Backup
        backup_data = migracion_service.generar_backup_json(db, emp.id, filtros=None)
        
        # 2. Save File
        safe_name = "".join([c for c in emp.razon_social if c.isalnum() or c in (' ', '-', '_')]).strip()
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"BACKUP_AUTO_{safe_name}_{timestamp}.json"
        full_path = os.path.join(path, filename)
        
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, default=str)
        
        logger.info(f"[AutoBackup] Success! Saved to {full_path}")
        
        # 3. Update last_run
        _update_last_run(empresa_id)

        # 4. Retention Policy
        _apply_retention_policy(path, cfg.get("dias_retencion", 30), safe_name)

    except Exception as e:
        logger.error(f"[AutoBackup] Error backing up company {empresa_id}: {e}")
    finally:
        db.close()

def _update_last_run(empresa_id):
    full_config = load_config(empresa_id=None)
    str_id = str(empresa_id)
    if str_id in full_config.get("companies", {}):
        full_config["companies"][str_id]["last_run"] = datetime.now().isoformat()
        with open(CONFIG_FILE, "w") as f:
            json.dump(full_config, f, indent=4)

def _apply_retention_policy(path, days, company_safe_name):
    """
    Elimina backups viejos, PERO SOLO de esta empresa (basado en el nombre).
    Esto es importante para no borrar backups de otras empresas si comparten carpeta.
    """
    try:
        now = datetime.now()
        prefix = f"BACKUP_AUTO_{company_safe_name}_"
        
        for f in os.listdir(path):
            if f.startswith(prefix) and f.endswith(".json"):
                fpath = os.path.join(path, f)
                mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                if (now - mtime).days > days:
                    os.remove(fpath)
                    logger.info(f"[AutoBackup] Deleted old backup: {f}")
    except Exception as e:
        logger.warning(f"[AutoBackup] Retention policy error: {e}")

def check_missed_backups():
    """
    Revisa si alguna empresa tenía un backup programado que NO corrió hoy.
    Esto soluciona el problema de "computador apagado a la hora X".
    Se debe llamar al inicio del sistema.
    """
    logger.info("[AutoBackup] Checking for missed backups...")
    full_config = load_config(empresa_id=None)
    companies = full_config.get("companies", {})
    
    now = datetime.now()
    
    for str_id, cfg in companies.items():
        if not cfg.get("enabled", False):
            continue
            
        try:
            # Parsear hora programada
            hora_str = cfg.get("hora_ejecucion", "03:00")
            h, m = map(int, hora_str.split(":"))
            scheduled_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
            
            # Fecha de la última ejecución
            last_run_str = cfg.get("last_run")
            last_run = datetime.fromisoformat(last_run_str) if last_run_str else None
            
            should_run = False
            
            # CASO A: Nunca ha corrido y ya pasó la hora hoy
            if not last_run and now > scheduled_time:
                should_run = True
                
            # CASO B: Corrió antes, pero no HOY, y ya pasó la hora
            elif last_run:
                if last_run.date() < now.date() and now > scheduled_time:
                    should_run = True
            
            if should_run:
                logger.warning(f"[AutoBackup] MISSED BACKUP DETECTED for Company {str_id}. Running NOW.")
                run_backup_for_company(int(str_id))
                
        except Exception as e:
            logger.error(f"[AutoBackup] Error checking missed backup for {str_id}: {e}")

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
                hour, minute = map(int, time_str.split(":"))
                
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
