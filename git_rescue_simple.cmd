@echo off
set GIT_PAGER=
set LESS=
echo === RESCATE KIRO - SIMPLE ===
git config core.pager ""
git branch --show-current
git checkout kiro-rama
git status
git add .
git reset HEAD .env
git commit -m "feat(conciliacion): Modulo completo y optimizaciones (Rescate version Kiro)"
git push origin kiro-rama
echo === COMPLETADO ===