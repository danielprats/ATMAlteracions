-- download_alerts_DROP_ONLY.sql
-- Script NOMÉS per eliminar l'esquema d'alertes ATM
-- Autor: GitHub Copilot  
-- Data: Octubre 2025
-- 
-- ATENCIÓ: Aquest script ELIMINA TOTES les dades d'alertes!
-- Fes un backup abans d'executar.

-- ========================================
-- DROPS per eliminar completament l'esquema
-- ========================================

-- Eliminar vistes (han de ser abans que les taules)
DROP VIEW IF EXISTS atm.v_alert_stops_by_status CASCADE;
DROP VIEW IF EXISTS atm.v_alert_routes_by_status CASCADE;
DROP VIEW IF EXISTS atm.v_alerts_by_status CASCADE;
DROP VIEW IF EXISTS atm.v_alerts_stats CASCADE;
DROP VIEW IF EXISTS atm.v_alerts_active CASCADE;
DROP VIEW IF EXISTS atm.v_alerts_complete CASCADE;

-- Eliminar triggers
DROP TRIGGER IF EXISTS update_alerts_modtime ON atm.alerts;

-- Eliminar funcions
DROP FUNCTION IF EXISTS atm.cleanup_old_alerts(INTEGER);
DROP FUNCTION IF EXISTS atm.update_modified_column();

-- Eliminar taules (ordre invers per dependencies)
DROP TABLE IF EXISTS atm.alert_stops CASCADE;
DROP TABLE IF EXISTS atm.alert_routes CASCADE;
DROP TABLE IF EXISTS atm.alerts CASCADE;

-- Opcional: Eliminar esquema completament (descomenta si necessari)
-- DROP SCHEMA IF EXISTS atm CASCADE;

-- Confirmació
SELECT 'Esquema d''alertes ATM eliminat completament.' AS status;
SELECT 'Executa download_alerts_Genera BD.sql per recrear-lo.' AS next_step;