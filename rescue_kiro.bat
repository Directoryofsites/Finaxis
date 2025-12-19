@echo off
echo === PROTOCOLO DE RESCATE KIRO ===
echo Configurando Git sin paginador...
set GIT_PAGER=
git config --local core.pager ""

echo Verificando rama actual...
git branch --show-current

echo Cambiando a kiro-rama...
git checkout kiro-rama

echo Verificando estado de archivos...
git status --porcelain

echo Agregando archivos (excluyendo .env)...
git add .
git reset HEAD .env 2>nul

echo Verificando cambios preparados...
git status --porcelain --cached

echo Haciendo commit...
git commit -m "feat(conciliacion): Modulo completo y optimizaciones (Rescate version Kiro)"

echo Subiendo a GitHub...
git push origin kiro-rama

echo === RESCATE COMPLETADO ===
pause