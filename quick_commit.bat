@echo off
set GIT_PAGER=
set PAGER=
git reset HEAD .env >nul 2>&1
git add .kiro/
git add app/
git add frontend/
git add alembic/versions/create_bank_reconciliation_module.py
git add *.md
git add test_*.py
git add *_permissions.py
git add optimize_database.py
git add verify_integration.py
git add create_bank_reconciliation_tables.py
git commit -m "Actualización Kiro: Módulo conciliación bancaria completo - Implementado módulo completo de conciliación bancaria - Agregadas mejoras de navegación en contabilidad - Optimizaciones de rendimiento y caché - Tests integrales para todas las funcionalidades - Documentación completa de tareas y soluciones"
git push origin kiro-rama
echo Actualización completada!