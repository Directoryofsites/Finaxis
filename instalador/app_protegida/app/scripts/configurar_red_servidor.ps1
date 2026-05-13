# app/scripts/configurar_red_servidor.ps1
<#
.SYNOPSIS
    Configura el Firewall de Windows para permitir que Finaxis funcione en red.
    Debe ejecutarse como ADMINISTRADOR en la PC que servirá como SERVIDOR.
#>

$ErrorActionPreference = "Stop"

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "   FINAXIS: CONFIGURADOR DE RED (MODO SERVIDOR)    " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# 1. Verificar Privilegios de Administrador
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "❌ ERROR: Debe ejecutar este script como ADMINISTRADOR." -ForegroundColor Red
    return
}

# 2. Abrir Puertos en el Firewall
Write-Host "`n[1/3] Configurando Firewall de Windows..." -ForegroundColor Yellow

$rules = @(
    @{ Name="Finaxis_PostgreSQL"; Port=5432; Desc="Puerto de Base de Datos PostgreSQL" },
    @{ Name="Finaxis_API"; Port=8002; Desc="Puerto del Servidor Backend Finaxis" },
    @{ Name="Finaxis_Frontend"; Port=3000; Desc="Puerto de la Interfaz de Usuario" }
)

foreach ($rule in $rules) {
    if (Get-NetFirewallRule -Name $rule.Name -ErrorAction SilentlyContinue) {
        Write-Host "   - Regla '$($rule.Name)' ya existe. Actualizando..."
        Remove-NetFirewallRule -Name $rule.Name
    }
    New-NetFirewallRule -Name $rule.Name -DisplayName $rule.Name -Description $rule.Desc -Direction Inbound -Protocol TCP -LocalPort $rule.Port -Action Allow -Enabled True
    Write-Host "   ✅ Puerto $($rule.Port) abierto ($($rule.Name))." -ForegroundColor Green
}

# 3. Detectar IP Local
Write-Host "`n[2/3] Detectando dirección de red..." -ForegroundColor Yellow
$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" -and $_.IPv4Address -notlike "169.*" }).IPv4Address | Select-Object -First 1
$hostname = $env:COMPUTERNAME

Write-Host "   - Nombre del Servidor: $hostname" -ForegroundColor White
Write-Host "   - Dirección IP Local: $ip" -ForegroundColor White
Write-Host "   - URL de Conexión Recomendada: http://$hostname:3000" -ForegroundColor Cyan

# 4. Instrucciones Manuales para PostgreSQL
Write-Host "`n[3/3] REQUISITO CRÍTICO: Configurar PostgreSQL para Red" -ForegroundColor Yellow
Write-Host "   Para que otros equipos se conecten, debe editar dos archivos en su servidor Postgres:"

Write-Host "`n   A. Editar 'postgresql.conf':" -ForegroundColor White
Write-Host "      Busque la línea: #listen_addresses = 'localhost'"
Write-Host "      Cámbiela por: listen_addresses = '*'" -ForegroundColor Green

Write-Host "`n   B. Editar 'pg_hba.conf':" -ForegroundColor White
Write-Host "      Agregue esta línea al final para permitir su red local:"
Write-Host "      host    all             all             0.0.0.0/0               md5" -ForegroundColor Green

Write-Host "`n====================================================" -ForegroundColor Cyan
Write-Host "   CONFIGURACIÓN COMPLETADA CON ÉXITO             " -ForegroundColor Cyan
Write-Host "   Recuerde reiniciar el servicio de PostgreSQL.  " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

Pause
