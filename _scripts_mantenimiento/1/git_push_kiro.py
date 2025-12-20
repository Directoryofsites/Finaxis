import subprocess
import os

# Configurar el entorno para evitar el paginador
env = os.environ.copy()
env['GIT_PAGER'] = ''
env['PAGER'] = ''

# Cambiar a la rama kiro-rama
print("Cambiando a rama kiro-rama...")
result = subprocess.run(['git', 'checkout', 'kiro-rama'], 
                       capture_output=True, text=True, env=env)
print(result.stdout)
if result.stderr:
    print(result.stderr)

# Agregar archivos
print("\nAgregando archivos...")
files_to_add = [
    '.kiro/',
    'app/api/conciliacion_bancaria/',
    'app/models/conciliacion_bancaria.py',
    'app/schemas/conciliacion_bancaria.py',
    'app/services/conciliacion_bancaria.py',
    'app/core/cache.py',
    'app/core/file_processor.py',
    'app/core/monitoring.py',
    'frontend/app/conciliacion-bancaria/',
    'frontend/components/ui/',
    'alembic/versions/create_bank_reconciliation_module.py',
    '*.md',
    'test_*.py',
    'create_bank_reconciliation_tables.py',
    'migrate_conciliacion_permissions.py',
    'optimize_database.py',
    'verify_integration.py',
    'update_permissions.py'
]

for file in files_to_add:
    result = subprocess.run(['git', 'add', file], 
                           capture_output=True, text=True, env=env)
    if result.returncode == 0:
        print(f"✓ Agregado: {file}")
    else:
        print(f"✗ Error agregando {file}: {result.stderr}")

# Verificar estado
print("\nVerificando estado...")
result = subprocess.run(['git', 'status', '--short'], 
                       capture_output=True, text=True, env=env)
print(result.stdout)

# Hacer commit
print("\nCreando commit...")
commit_message = """Actualización Kiro: Módulo conciliación bancaria completo

- Implementado módulo completo de conciliación bancaria
- Agregadas mejoras de navegación en contabilidad
- Optimizaciones de rendimiento y caché
- Tests integrales para todas las funcionalidades
- Documentación completa de tareas y soluciones"""

result = subprocess.run(['git', 'commit', '-m', commit_message], 
                       capture_output=True, text=True, env=env)
print(result.stdout)
if result.stderr:
    print(result.stderr)

# Push a la rama kiro-rama
print("\nSubiendo cambios a GitHub (rama kiro-rama)...")
result = subprocess.run(['git', 'push', 'origin', 'kiro-rama'], 
                       capture_output=True, text=True, env=env)
print(result.stdout)
if result.stderr:
    print(result.stderr)

print("\n✓ Actualización completada!")
