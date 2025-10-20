-- UPDATE per actualitzar una taula amb els resultats de la consulta
-- Assumint que vols actualitzar la taula 'sto_puntuades' amb camps per les agències

-- OPCIÓ 1: Si vols afegir nous camps a sto_puntuades
-- ALTER TABLE sto_puntuades 
-- ADD COLUMN IF NOT EXISTS lst_agencies TEXT,
-- ADD COLUMN IF NOT EXISTS num_agencies INTEGER DEFAULT 0;

-- UPDATE principal
UPDATE sto_puntuades sp
SET lst_agencies = subq.lst,
    num_agencies = subq.num
FROM (
    WITH reg_ids AS (
        SELECT 
            sp.id AS taula_a_id,
            sp.lst_serv_arribada,
            trim(unnest(string_to_array(sp.lst_serv_arribada, ',')))::INTEGER AS id,
            sp.stop_id
        FROM sto_puntuades sp
        WHERE sp.lst_serv_arribada IS NOT NULL 
          AND sp.lst_serv_arribada != ''
    ),
    tr AS (
        SELECT 
            sp.route_id,
            sp.trip_id,
            reg_ids.stop_id
        FROM serveis_projectats sp
        INNER JOIN reg_ids ON sp.id = reg_ids.id
    )
    SELECT 
        string_agg(DISTINCT age.agency_name, ',') AS lst,
        count(DISTINCT age.agency_name) AS num,
        tr.stop_id
    FROM rou, tri, age, tr  
    WHERE rou.route_id = tr.route_id 
      AND tr.trip_id = tri.trip_id
      AND rou.agency_id = age.agency_id
    GROUP BY tr.stop_id
) subq
WHERE sp.stop_id = subq.stop_id;

-- OPCIÓ 2: Si vols crear/actualitzar una taula diferent
-- CREATE TABLE IF NOT EXISTS stop_agencies (
--     stop_id TEXT PRIMARY KEY,
--     lst_agencies TEXT,
--     num_agencies INTEGER DEFAULT 0,
--     data_actualizacio TIMESTAMP DEFAULT NOW()
-- );

-- INSERT INTO stop_agencies (stop_id, lst_agencies, num_agencies)
-- WITH reg_ids AS (
--     SELECT 
--         sp.id AS taula_a_id,
--         sp.lst_serv_arribada,
--         trim(unnest(string_to_array(sp.lst_serv_arribada, ',')))::INTEGER AS id,
--         sp.stop_id
--     FROM sto_puntuades sp
--     WHERE sp.lst_serv_arribada IS NOT NULL 
--       AND sp.lst_serv_arribada != ''
-- ),
-- tr AS (
--     SELECT 
--         sp.route_id,
--         sp.trip_id,
--         reg_ids.stop_id
--     FROM serveis_projectats sp
--     INNER JOIN reg_ids ON sp.id = reg_ids.id
-- )
-- SELECT 
--     tr.stop_id,
--     string_agg(DISTINCT age.agency_name, ',') AS lst,
--     count(DISTINCT age.agency_name) AS num
-- FROM rou, tri, age, tr  
-- WHERE rou.route_id = tr.route_id 
--   AND tr.trip_id = tri.trip_id
--   AND rou.agency_id = age.agency_id
-- GROUP BY tr.stop_id
-- ON CONFLICT (stop_id) 
-- DO UPDATE SET
--     lst_agencies = EXCLUDED.lst_agencies,
--     num_agencies = EXCLUDED.num_agencies,
--     data_actualizacio = NOW();

-- OPCIÓ 3: Si la taula de destí té noms de camps diferents
-- UPDATE nom_taula_destinacio td
-- SET camp_llista_agencies = subq.lst,
--     camp_numero_agencies = subq.num,
--     data_modificacio = NOW()
-- FROM (
--     WITH reg_ids AS (
--         SELECT 
--             sp.id AS taula_a_id,
--             sp.lst_serv_arribada,
--             trim(unnest(string_to_array(sp.lst_serv_arribada, ',')))::INTEGER AS id,
--             sp.stop_id
--         FROM sto_puntuades sp
--         WHERE sp.lst_serv_arribada IS NOT NULL 
--           AND sp.lst_serv_arribada != ''
--     ),
--     tr AS (
--         SELECT 
--             sp.route_id,
--             sp.trip_id,
--             reg_ids.stop_id
--         FROM serveis_projectats sp
--         INNER JOIN reg_ids ON sp.id = reg_ids.id
--     )
--     SELECT 
--         string_agg(DISTINCT age.agency_name, ',') AS lst,
--         count(DISTINCT age.agency_name) AS num,
--         tr.stop_id
--     FROM rou, tri, age, tr  
--     WHERE rou.route_id = tr.route_id 
--       AND tr.trip_id = tri.trip_id
--       AND rou.agency_id = age.agency_id
--     GROUP BY tr.stop_id
-- ) subq
-- WHERE td.stop_id = subq.stop_id;

-- CONSULTA DE VERIFICACIÓ per comprovar els resultats
-- SELECT 
--     stop_id,
--     lst_agencies,
--     num_agencies,
--     length(lst_agencies) AS longitud_text,
--     array_length(string_to_array(lst_agencies, ','), 1) AS nombre_agencies_calculat
-- FROM sto_puntuades 
-- WHERE lst_agencies IS NOT NULL
-- ORDER BY num_agencies DESC, stop_id
-- LIMIT 20;