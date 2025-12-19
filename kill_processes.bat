@echo off
echo Matando procesos colgados...
taskkill /F /IM less.exe 2>nul
taskkill /F /IM git.exe 2>nul
echo Configurando Git...
git config --global core.pager "cat"
echo Listo!
pause