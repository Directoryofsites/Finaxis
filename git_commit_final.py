#!/usr/bin/env python3
import subprocess
import os
import sys

def run_git_command(cmd, timeout=30):
    """Ejecuta un comando git con configuración para evitar paginador"""
    env = os.environ.copy()
    env['GIT_PAGER'] = ''
    env['PAGER'] = ''
    env['LESS'] = ''
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            env=env,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"

print("=== Actualización Git para rama kiro-rama ===")

# 1. Verificar rama actual
print("\n1. Verificando rama actual...")
code, out, err = run_git_command("git branch --show-current")
if code == 0:
    current_branch = out.strip()
    print(f"Rama actual: {current_branch}")
    if current_branch != "kiro-rama":
        print("Cambiando a kiro-rama...")
        code, out, err = run_git_command("git checkout kiro-rama")
        if code != 0:
            print(f"Error cambiando rama: {err}")
else:
    print("Asumiendo que estamos en kiro-rama...")

# 2. Remover .env del staging si existe
print("\n2. Removiendo .env del staging...")
run_git_command("git reset HEAD .env")

# 3. Agregar archivos específicos
print("\n3. Agregando archivos...")
files_to_add = [
    ".kiro/",
    "app/api/conciliacion_bancaria/",
    "app/models/conciliacion_bancaria.py",
    "app/schemas/conciliacion_bancaria.py", 
    "app/services/conciliacion_bancaria.py",
    "app/core/cache.py",
    "app/core/file_processor.py",
    "app/core/monitoring.py",
    "frontend/app/conciliacion-bancaria/",
    "frontend/components/ui/",
    "alembic/versions/create_bank_reconciliation_module.py",
    "*.md",
    "test_*.py",
    "*_permissions.py",
    "optimize_database.py",
    "verify_integration.py",
    "create_bank_reconciliation_tables.py"
]

for file in files_to_add:
    code, out, err = run_git_command(f"git add {file}")
    if code == 0:
        print(f"✓ {file}")
    else:
        print(f"✗ {file}: {err}")

# 4. Verificar estado
print("\n4. Verificando estado...")
code, out, err = run_git_command("git status --porcelain")
if code == 0:
    lines = out.strip().split('\n') if out.strip() else []
    print(f"Archivos en staging: {len(lines)}")
    # Verificar que .env no esté incluido
    env_in_staging = any('.env' in line for line in lines)
    if env_in_staging:
        print("⚠️  ADVERTENCIA: .env detectado en staging")
        run_git_command("git reset HEAD .env")
    else:
        print("✓ .env no está en staging")

# 5. Hacer commit
print("\n5. Creando commit...")
commit_msg = """Actualización Kiro: Módulo conciliación bancaria completo

- Implementado módulo completo de conciliación bancaria
- Agregadas mejoras de navegación en contabilidad
- Optimizaciones de rendimiento y caché
- Tests integrales para todas las funcionalidades
- Documentación completa de tareas y soluciones"""

code, out, err = run_git_command(f'git commit -m "{commit_msg}"', timeout=60)
if code == 0:
    print("✓ Commit creado exitosamente")
    print(out)
else:
    print(f"✗ Error en commit: {err}")
    sys.exit(1)

# 6. Push a GitHub
print("\n6. Subiendo a GitHub (rama kiro-rama)...")
code, out, err = run_git_command("git push origin kiro-rama", timeout=120)
if code == 0:
    print("✓ Push exitoso!")
    print(out)
else:
    print(f"✗ Error en push: {err}")
    sys.exit(1)

print("\n🎉 ¡Actualización completada exitosamente!")