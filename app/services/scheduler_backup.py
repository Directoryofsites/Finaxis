
import os
import json
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services import migracion as migracion_service
from app.models.empresa import Empresa # Corrected import

# Config
CONFIG_FILE = "backup_config.json"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"enabled": False, "hora_ejecucion": "03:00", "ruta_local": "C:/Backups_Finaxis", "dias_retencion": 30}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {"enabled": False, "hora_ejecucion": "03:00", "ruta_local": "C:/Backups_Finaxis", "dias_retencion": 30}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    # Reschedule on save
    schedule_backup_job()

def run_auto_backup():
    config = load_config()
    if not config.get("enabled", False):
        logger.info("[AutoBackup] Backup disabled. Skipping.")
        return

    path = config.get("ruta_local", "C:/Backups_Finaxis")
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except Exception as e:
            logger.error(f"[AutoBackup] Failed to create directory {path}: {e}")
            return

    logger.info("[AutoBackup] Starting automatic backup process...")
    db: Session = SessionLocal()
    try:
        empresas = db.query(Empresa).all()
        for emp in empresas:
            try:
                logger.info(f"[AutoBackup] Processing Company: {emp.razon_social} (ID: {emp.id})")
                # Generate FULL Backup (No filters = Full Safety Snapshot)
                backup_data = migracion_service.generar_backup_json(db, emp.id, filtros=None)
                
                # Sanitize filename
                safe_name = "".join([c for c in emp.razon_social if c.isalnum() or c in (' ', '-', '_')]).strip()
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                filename = f"BACKUP_AUTO_{safe_name}_{timestamp}.json"
                full_path = os.path.join(path, filename)
                
                with open(full_path, "w", encoding="utf-8") as f:
                    json.dump(backup_data, f, default=str)
                
                logger.info(f"[AutoBackup] Success! Saved to {full_path}")
            except Exception as e:
                logger.error(f"[AutoBackup] Error backing up company {emp.id}: {e}")

        # Retention Policy
        _apply_retention_policy(path, config.get("dias_retencion", 30))

    except Exception as e:
        logger.error(f"[AutoBackup] Fatal error in backup job: {e}")
    finally:
        db.close()

def _apply_retention_policy(path, days):
    try:
        now = datetime.now()
        for f in os.listdir(path):
            if f.startswith("BACKUP_AUTO_") and f.endswith(".json"):
                fpath = os.path.join(path, f)
                mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                if (now - mtime).days > days:
                    os.remove(fpath)
                    logger.info(f"[AutoBackup] Deleted old backup: {f}")
    except Exception as e:
        logger.warning(f"[AutoBackup] Retention policy error: {e}")

def schedule_backup_job():
    config = load_config()
    scheduler.remove_all_jobs()
    
    if config.get("enabled", False):
        time_str = config.get("hora_ejecucion", "03:00")
        try:
            hour, minute = map(int, time_str.split(":"))
            scheduler.add_job(run_auto_backup, CronTrigger(hour=hour, minute=minute), id="daily_backup")
            logger.info(f"[AutoBackup] Scheduled daily backup at {time_str}")
        except ValueError:
            logger.error("[AutoBackup] Invalid time format. Scheduler not started.")
    else:
        logger.info("[AutoBackup] Backup is disabled.")

def start_scheduler():
    config = load_config()
    # Initial Schedule
    if config.get("enabled", False):
        schedule_backup_job()
    
    if not scheduler.running:
        scheduler.start()
        logger.info("[AutoBackup] Scheduler started.")
