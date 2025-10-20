# Script PowerShell per automatitzar la descàrrega d'alertes ATM a la base de dades
# Autor: GitHub Copilot
# Data: Octubre 2025

Write-Host "========================================" -ForegroundColor Green
Write-Host "DESCÀRREGA AUTOMÀTICA D'ALERTES ATM - BD" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Data: $(Get-Date)" -ForegroundColor Yellow
Write-Host ""

# Canviar al directori del script
Set-Location $PSScriptRoot

try {
    # Executar script Python
    Write-Host "Executant descàrrega a la base de dades..." -ForegroundColor Yellow
    & python download_alerts.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "DESCÀRREGA COMPLETADA CORRECTAMENT" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "Dades guardades a la base de dades atm_sc.alerts" -ForegroundColor Cyan
        
        # Opcional: Executar anàlisi automàtica
        Write-Host ""
        Write-Host "Executant anàlisi de dades..." -ForegroundColor Yellow
        & python analyze_alerts_db.py 1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Anàlisi completada." -ForegroundColor Green
        } else {
            Write-Warning "Error en l'anàlisi de dades."
        }
        
    } else {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "ERROR EN LA DESCÀRREGA" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "Codi d'error: $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
    
} catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "ERROR INESPERAT" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Procés finalitzat a les $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Yellow

# Opcional: Pausa per veure els resultats
# Read-Host "Premeu Enter per continuar"