@echo off
REM Script per automatitzar la descàrrega d'alertes ATM a la base de dades
REM Autor: GitHub Copilot
REM Data: Octubre 2025

echo ========================================
echo DESCÀRREGA AUTOMÀTICA D'ALERTES ATM - BD
echo ========================================
echo Data: %date% %time%
echo.

REM Canviar al directori del script
cd /d "%~dp0"

echo Executant descàrrega a la base de dades...
echo.

REM Executar script Python
python download_alerts.py

REM Comprovar si l'execució ha estat exitosa
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo DESCÀRREGA COMPLETADA CORRECTAMENT
    echo ========================================
    echo Dades guardades a la base de dades atm_sc.alerts
    
    REM Opcional: Executar anàlisi automàtica
    echo.
    echo Executant anàlisi de dades...
    python analyze_alerts_db.py 1
    
    if %ERRORLEVEL% EQU 0 (
        echo Anàlisi completada.
    ) else (
        echo Avís: Error en l'anàlisi de dades.
    )
    
) else (
    echo.
    echo ========================================
    echo ERROR EN LA DESCÀRREGA
    echo ========================================
    echo Codi d'error: %ERRORLEVEL%
)

REM Opcional: Mantenir la finestra oberta per a depuració
REM pause

echo.
echo Procés finalitzat a les %time%