# PROTOCOLO DE RESCATE KIRO
Write-Host "=== PROTOCOLO DE RESCATE KIRO ===" -ForegroundColor Green

# Configurar entorno sin paginador
$env:GIT_PAGER = ""
$env:LESS = ""

Write-Host "Configurando Git..." -ForegroundColor Yellow
& git config --local core.pager ""

Write-Host "Verificando rama actual..." -ForegroundColor Yellow
$currentBranch = & git branch --show-current
Write-Host "Rama actual: $currentBranch" -ForegroundColor Cyan

Write-Host "Cambiando a kiro-rama..." -ForegroundColor Yellow
& git checkout kiro-rama

Write-Host "Verificando estado de archivos..." -ForegroundColor Yellow
& git status --porcelain

Write-Host "Agregando archivos (excluyendo .env)..." -ForegroundColor Yellow
& git add .
& git reset HEAD .env 2>$null

Write-Host "Verificando cambios preparados..." -ForegroundColor Yellow
& git status --porcelain --cached

Write-Host "Haciendo commit..." -ForegroundColor Yellow
& git commit -m "feat(conciliacion): Modulo completo y optimizaciones (Rescate version Kiro)"

Write-Host "Subiendo a GitHub..." -ForegroundColor Yellow
& git push origin kiro-rama

Write-Host "=== RESCATE COMPLETADO ===" -ForegroundColor Green