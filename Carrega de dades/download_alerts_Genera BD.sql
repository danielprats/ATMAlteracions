-- download_alerts_Genera BD.sql
-- Script per crear les taules necessàries per al sistema d'alertes ATM
-- Autor: GitHub Copilot
-- Data: Octubre 2025

-- ========================================
-- DROPS per recrear l'esquema completament
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


-- Taula principal d'alertes
CREATE TABLE IF NOT EXISTS atm.alerts (
    id SERIAL PRIMARY KEY,
    download_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    api_timestamp TIMESTAMP WITH TIME ZONE,
    gtfs_version VARCHAR(10),
    incrementality VARCHAR(50),
    alert_id VARCHAR(50) NOT NULL,
    effect VARCHAR(100),
    active_start TIMESTAMP WITH TIME ZONE,
    active_end TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    header_cat TEXT,
    header_es TEXT,
    header_en TEXT,
    description_cat TEXT,
    description_es TEXT,
    description_en TEXT,
    url_cat TEXT,
    url_es TEXT,
    url_en TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Taula per a les rutes afectades
CREATE TABLE IF NOT EXISTS atm.alert_routes (
    id SERIAL PRIMARY KEY,
    alert_table_id INTEGER REFERENCES atm.alerts(id) ON DELETE CASCADE,
    alert_id VARCHAR(50) NOT NULL,
    route_id VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Taula per a les parades afectades
CREATE TABLE IF NOT EXISTS atm.alert_stops (
    id SERIAL PRIMARY KEY,
    alert_table_id INTEGER REFERENCES atm.alerts(id) ON DELETE CASCADE,
    alert_id VARCHAR(50) NOT NULL,
    stop_id VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índexs per millorar el rendiment
CREATE INDEX IF NOT EXISTS idx_alerts_alert_id ON atm.alerts(alert_id);
CREATE INDEX IF NOT EXISTS idx_alerts_download_timestamp ON atm.alerts(download_timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_active_start ON atm.alerts(active_start);
CREATE INDEX IF NOT EXISTS idx_alerts_active_end ON atm.alerts(active_end);
CREATE INDEX IF NOT EXISTS idx_alerts_effect ON atm.alerts(effect);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON atm.alerts(status);

CREATE INDEX IF NOT EXISTS idx_alert_routes_alert_id ON atm.alert_routes(alert_id);
CREATE INDEX IF NOT EXISTS idx_alert_routes_route_id ON atm.alert_routes(route_id);
CREATE INDEX IF NOT EXISTS idx_alert_routes_alert_table_id ON atm.alert_routes(alert_table_id);
CREATE INDEX IF NOT EXISTS idx_alert_routes_status ON atm.alert_routes(status);

CREATE INDEX IF NOT EXISTS idx_alert_stops_alert_id ON atm.alert_stops(alert_id);
CREATE INDEX IF NOT EXISTS idx_alert_stops_stop_id ON atm.alert_stops(stop_id);
CREATE INDEX IF NOT EXISTS idx_alert_stops_alert_table_id ON atm.alert_stops(alert_table_id);
CREATE INDEX IF NOT EXISTS idx_alert_stops_status ON atm.alert_stops(status);

-- Constraint per evitar duplicats en la mateixa descàrrega
CREATE UNIQUE INDEX IF NOT EXISTS idx_alerts_unique_download 
ON atm.alerts(alert_id, download_timestamp);

-- Función para actualizar el timestamp de modificación
CREATE OR REPLACE FUNCTION atm.update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para actualizar automáticamente updated_at
DROP TRIGGER IF EXISTS update_alerts_modtime ON atm.alerts;
CREATE TRIGGER update_alerts_modtime 
    BEFORE UPDATE ON atm.alerts 
    FOR EACH ROW 
    EXECUTE FUNCTION atm.update_modified_column();

-- Vista per obtenir alertes amb rutes i parades
CREATE OR REPLACE VIEW atm.v_alerts_complete AS
SELECT 
    a.id,
    a.download_timestamp,
    a.api_timestamp,
    a.gtfs_version,
    a.incrementality,
    a.alert_id,
    a.effect,
    a.active_start,
    a.active_end,
    a.status,
    a.header_cat,
    a.header_es,
    a.header_en,
    a.description_cat,
    a.description_es,
    a.description_en,
    a.url_cat,
    a.url_es,
    a.url_en,
    a.created_at,
    a.updated_at,
    string_agg(DISTINCT ar.route_id, ';' ORDER BY ar.route_id) AS affected_routes,
    string_agg(DISTINCT ast.stop_id, ';' ORDER BY ast.stop_id) AS affected_stops
FROM atm.alerts a
LEFT JOIN atm.alert_routes ar ON a.id = ar.alert_table_id
LEFT JOIN atm.alert_stops ast ON a.id = ast.alert_table_id
GROUP BY 
    a.id, a.download_timestamp, a.api_timestamp, a.gtfs_version, 
    a.incrementality, a.alert_id, a.effect, a.active_start, a.active_end, a.status,
    a.header_cat, a.header_es, a.header_en, a.description_cat, 
    a.description_es, a.description_en, a.url_cat, a.url_es, a.url_en,
    a.created_at, a.updated_at;

-- Vista per alertes actives (sense data de finalització o futura)
CREATE OR REPLACE VIEW atm.v_alerts_active AS
SELECT * FROM atm.v_alerts_complete
WHERE status IN ('ACTIVE', 'ACTIVE_OLD');

-- Vista per estadístiques d'alertes
CREATE OR REPLACE VIEW atm.v_alerts_stats AS
SELECT 
    effect,
    status,
    COUNT(*) as total_alerts,
    MIN(download_timestamp) as first_seen,
    MAX(download_timestamp) as last_seen
FROM atm.alerts
GROUP BY effect, status
ORDER BY effect, status;

-- Vista per alertes per status específic
CREATE OR REPLACE VIEW atm.v_alerts_by_status AS
SELECT 
    status,
    COUNT(*) as total,
    COUNT(DISTINCT alert_id) as unique_alerts,
    MIN(active_start) as earliest_start,
    MAX(active_start) as latest_start,
    COUNT(CASE WHEN active_end IS NULL THEN 1 END) as without_end_date
FROM atm.alerts
GROUP BY status
ORDER BY 
    CASE status 
        WHEN 'ACTIVE' THEN 1 
        WHEN 'ACTIVE_OLD' THEN 2 
        WHEN 'CLOSED' THEN 3 
        ELSE 4 
    END;

-- Vista per alertes de routes per status
CREATE OR REPLACE VIEW atm.v_alert_routes_by_status AS
SELECT 
    ar.route_id,
    ar.status,
    COUNT(*) as total_alerts,
    MIN(a.active_start) as first_alert,
    MAX(a.active_start) as last_alert
FROM atm.alert_routes ar
JOIN atm.alerts a ON ar.alert_table_id = a.id
GROUP BY ar.route_id, ar.status
ORDER BY ar.route_id, ar.status;

-- Vista per alertes de stops per status  
CREATE OR REPLACE VIEW atm.v_alert_stops_by_status AS
SELECT 
    ast.stop_id,
    ast.status,
    COUNT(*) as total_alerts,
    MIN(a.active_start) as first_alert,
    MAX(a.active_start) as last_alert
FROM atm.alert_stops ast
JOIN atm.alerts a ON ast.alert_table_id = a.id
GROUP BY ast.stop_id, ast.status
ORDER BY ast.stop_id, ast.status;

-- Procedure per netejar alertes antigues segons status
CREATE OR REPLACE FUNCTION atm.cleanup_old_alerts(days_to_keep INTEGER DEFAULT 30)
RETURNS TABLE(deleted_count INTEGER, status_summary TEXT) AS $$
DECLARE
    closed_deleted INTEGER;
    old_deleted INTEGER;
    total_deleted INTEGER;
BEGIN
    -- Eliminar alertes CLOSED més antigues que days_to_keep
    DELETE FROM atm.alerts 
    WHERE status = 'CLOSED' 
    AND download_timestamp < NOW() - (days_to_keep || ' days')::INTERVAL;
    
    GET DIAGNOSTICS closed_deleted = ROW_COUNT;
    
    -- Eliminar alertes ACTIVE_OLD molt antigues (més del doble de dies)
    DELETE FROM atm.alerts 
    WHERE status = 'ACTIVE_OLD' 
    AND download_timestamp < NOW() - ((days_to_keep * 2) || ' days')::INTERVAL;
    
    GET DIAGNOSTICS old_deleted = ROW_COUNT;
    
    total_deleted := closed_deleted + old_deleted;
    
    RETURN QUERY SELECT 
        total_deleted,
        format('CLOSED: %s, ACTIVE_OLD: %s, Total: %s', 
               closed_deleted, old_deleted, total_deleted);
END;
$$ LANGUAGE plpgsql;

-- Comentaris a les taules
COMMENT ON TABLE atm.alerts IS 'Taula principal que emmagatzema les alertes de T-mobilitat ATM';
COMMENT ON TABLE atm.alert_routes IS 'Taula que relaciona alertes amb les rutes afectades';
COMMENT ON TABLE atm.alert_stops IS 'Taula que relaciona alertes amb les parades afectades';

COMMENT ON COLUMN atm.alerts.status IS 'Status de l''alerta: ACTIVE, ACTIVE_OLD, CLOSED (gestionat per l''aplicació)';
COMMENT ON COLUMN atm.alert_routes.status IS 'Status de l''alerta per la ruta (gestionat per l''aplicació)';
COMMENT ON COLUMN atm.alert_stops.status IS 'Status de l''alerta per la parada (gestionat per l''aplicació)';

COMMENT ON VIEW atm.v_alerts_complete IS 'Vista completa d''alertes amb rutes i parades agregades';
COMMENT ON VIEW atm.v_alerts_active IS 'Vista d''alertes amb status ACTIVE o ACTIVE_OLD';
COMMENT ON VIEW atm.v_alerts_stats IS 'Vista amb estadístiques d''alertes per efecte i status';
COMMENT ON VIEW atm.v_alerts_by_status IS 'Vista amb resum d''alertes agrupades per status';
COMMENT ON VIEW atm.v_alert_routes_by_status IS 'Vista d''alertes de rutes agrupades per status';
COMMENT ON VIEW atm.v_alert_stops_by_status IS 'Vista d''alertes de parades agrupades per status';

-- Grants per l'usuari atm
GRANT USAGE ON SCHEMA atm TO atm;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA atm TO atm;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA atm TO atm;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA atm TO atm;

-- Informació del sistema
SELECT 'Taules d''alertes ATM creades correctament' AS status;

-- Consultes d'exemple per verificar els status
SELECT 'Exemples de consultes per status (gestionat per aplicació):' AS info;

-- Resum per status
SELECT '1. Resum d''alertes per status:' AS consulta;
-- SELECT * FROM atm.v_alerts_by_status;

-- Alertes actives
SELECT '2. Alertes actives (ACTIVE):' AS consulta;
-- SELECT COUNT(*) FROM atm.alerts WHERE status = 'ACTIVE';

-- Alertes antigues
SELECT '3. Alertes antigues (ACTIVE_OLD):' AS consulta;
-- SELECT COUNT(*) FROM atm.alerts WHERE status = 'ACTIVE_OLD';

-- Alertes tancades
SELECT '4. Alertes tancades (CLOSED):' AS consulta;
-- SELECT COUNT(*) FROM atm.alerts WHERE status = 'CLOSED';

-- Rutes amb més alertes actives
SELECT '5. Rutes amb alertes actives:' AS consulta;
-- SELECT route_id, COUNT(*) as alertes_actives FROM atm.alert_routes WHERE status IN ('ACTIVE', 'ACTIVE_OLD') GROUP BY route_id ORDER BY alertes_actives DESC LIMIT 10;

-- Parades amb més alertes actives  
SELECT '6. Parades amb alertes actives:' AS consulta;
-- SELECT stop_id, COUNT(*) as alertes_actives FROM atm.alert_stops WHERE status IN ('ACTIVE', 'ACTIVE_OLD') GROUP BY stop_id ORDER BY alertes_actives DESC LIMIT 10;

-- ========================================
-- INFORMACIÓ D'ÚS DEL SCRIPT
-- ========================================

SELECT '========================================' AS separator;
SELECT 'SCRIPT COMPLETAT CORRECTAMENT' AS status;
SELECT '========================================' AS separator;

SELECT 'Aquest script inclou DROPs per poder recrear l''esquema completament.' AS info;
SELECT 'Executa aquest script per:' AS info;
SELECT '1. Eliminar completament l''esquema existent' AS step;
SELECT '2. Recrear totes les taules, vistes i funcions' AS step;
SELECT '3. Configurar índexs i permisos' AS step;

SELECT 'ATENCIÓ: Els DROPs eliminaran TOTES les dades existents!' AS warning;
SELECT 'Fes un backup abans d''executar en producció.' AS warning;