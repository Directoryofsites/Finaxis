@echo off
set GIT_PAGER=
git add .kiro/
git add app/
git add frontend/
git add *.md
git add *.py
git commit -m "Actualización Kiro: Módulo conciliación bancaria y mejoras sistema"
git push origin kiro-rama