# ============================================================
# INSTALADOR POSTGRESQL 16 — Fetal Medical Bolivia
# Ejecutar como Administrador en PowerShell:
#   Right-click → "Ejecutar como administrador"
#   .\instalar_postgres.ps1
# ============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Instalando PostgreSQL 16 para el sistema  " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# 1. Instalar via winget (requiere admin)
Write-Host "`n[1/4] Instalando PostgreSQL via winget..." -ForegroundColor Yellow
winget install -e --id PostgreSQL.PostgreSQL.16 `
    --accept-package-agreements `
    --accept-source-agreements `
    --silent

if ($LASTEXITCODE -ne 0) {
    Write-Host "winget fallo. Descargando instalador directo..." -ForegroundColor Yellow
    $installer = "$env:TEMP\postgresql_installer.exe"
    Invoke-WebRequest `
        -Uri "https://get.enterprisedb.com/postgresql/postgresql-16.8-1-windows-x64.exe" `
        -OutFile $installer
    Start-Process $installer `
        -ArgumentList "--mode unattended --superpassword 25693 --serverport 5432 --datadir C:\PostgreSQL\data" `
        -Wait
}

# 2. Agregar PostgreSQL al PATH
Write-Host "`n[2/4] Configurando PATH..." -ForegroundColor Yellow
$pgBin = "C:\Program Files\PostgreSQL\16\bin"
if (Test-Path $pgBin) {
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
    if ($currentPath -notlike "*$pgBin*") {
        [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$pgBin", "Machine")
        $env:PATH += ";$pgBin"
        Write-Host "PATH actualizado con: $pgBin" -ForegroundColor Green
    } else {
        Write-Host "PostgreSQL ya esta en PATH" -ForegroundColor Green
    }
}

# 3. Iniciar servicio
Write-Host "`n[3/4] Iniciando servicio PostgreSQL..." -ForegroundColor Yellow
$service = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($service) {
    Start-Service $service.Name
    Write-Host "Servicio '$($service.Name)' iniciado" -ForegroundColor Green
} else {
    Write-Host "Servicio no encontrado. Iniciando manualmente con pg_ctl..." -ForegroundColor Yellow
    $pgCtl = "C:\Program Files\PostgreSQL\16\bin\pg_ctl.exe"
    if (Test-Path $pgCtl) {
        & $pgCtl start -D "C:\Program Files\PostgreSQL\16\data"
    }
}

# 4. Crear base de datos
Write-Host "`n[4/4] Creando base de datos 'historial'..." -ForegroundColor Yellow
$psql = "C:\Program Files\PostgreSQL\16\bin\psql.exe"
if (Test-Path $psql) {
    $env:PGPASSWORD = "25693"
    & $psql -U postgres -c "CREATE DATABASE historial;" 2>&1
    & $psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE historial TO postgres;" 2>&1
    Write-Host "Base de datos 'historial' creada" -ForegroundColor Green
}

Write-Host "`n============================================" -ForegroundColor Green
Write-Host "  Instalacion completada!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Ahora ejecuta en otra terminal (como admin):" -ForegroundColor Cyan
Write-Host "  cd Backend" -ForegroundColor White
Write-Host "  python manage.py migrate" -ForegroundColor White
Write-Host "  python manage.py createsuperuser" -ForegroundColor White
Write-Host "  python manage.py runserver" -ForegroundColor White
Write-Host ""
Write-Host "--- MODO DESARROLLO SIN POSTGRESQL (alternativa rapida) ---" -ForegroundColor Yellow
Write-Host "  cd Backend" -ForegroundColor White
Write-Host '  $env:USE_SQLITE="true"' -ForegroundColor White
Write-Host "  python manage.py migrate" -ForegroundColor White
Write-Host "  python manage.py runserver" -ForegroundColor White
