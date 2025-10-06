CREATE OR REPLACE FUNCTION atm.calcula_serv_arr_sor_stops_finestra(inici integer, recalcula boolean)
 RETURNS TABLE(serveis_insertats integer)
 LANGUAGE plpgsql
AS $function$ 
DECLARE
  rec_serv RECORD;
  rec RECORD;
  parades_totals INTEGER;
  processed INTEGER := 0;
  remaining INTEGER;
  start_time TIMESTAMP;
  elapsed INTERVAL;
  avg_per_route INTERVAL;
  eta INTERVAL;
  exec_end_time TIMESTAMP;
  exec_start_time  TIMESTAMP=clock_timestamp();
  serveis_insertats integer=0;
  tmp integer;
  _stop varchar='';

begin
  	RAISE NOTICE 'INICI';

	if reCalcula then 
	--Recalculem PARADES_PROPERES
		delete from sto_properes;
		INSERT INTO sto_properes (stop_id, stop_id_propera, distancia_m)
		SELECT 
		  s1.stop_id,
		  s2.stop_id,
		  ST_Distance(s1.geom, s2.geom)::numeric(10,2) AS distancia_m
		FROM sto s1
		JOIN sto s2
		  ON s1.stop_id <> s2.stop_id
		 AND ST_DWithin(s1.geom, s2.geom, 300);

	-- Inicialitzem taula temporal de SERVEIS PROJECTATS
		delete from sto_serv_disp 
		where temps_finestra_int=inici;
	  	RAISE NOTICE 'Esborrats';

		delete from serveis_projectats_tmp;
		insert into serveis_projectats_tmp select * from serveis_projectats
		where temps_int>=inici-(60*60) and temps_int<inici+(60*60) ;
	  	RAISE NOTICE 'SERVEIS PROJECTATS de càlcul actualitzats';

	-- 1) Comptem el total de routes a processar
		select count(stop_id) into parades_totals 
		from serveis_projectats sp
		where sp.temps_int >=inici and sp.temps_int<inici+((60*60));	
	  	RAISE NOTICE 'Total de parades: %', parades_totals;
	
	-- 2) Marquem l'inici del processament
	  	start_time := clock_timestamp();
	
	-- 3) Avaluem cada parada de servei per calcular (sto_serv_disp) :
			-- serv_sortida
			-- serv_arribada
			-- num_serv_sortida
			-- num_serv_arribada
			-- lst_serv_sortida
			-- lst_serv_arribada
		FOR rec_serv IN
			select (((sp.temps_int /(60*60))::int)*60*60) as temps_finestra_int, * 
			from serveis_projectats_tmp sp
			where sp.temps_int >=inici-(60*60) and sp.temps_int<inici+(60*60)
		LOOP
		    processed := processed + 1;
		    remaining := parades_totals - processed;
		
		    -- calculem temps transcorregut i ETA
		    elapsed := clock_timestamp() - start_time;
		    avg_per_route := elapsed / processed;
		    eta := avg_per_route * remaining;
		 
		    --RAISE NOTICE '[%/%] Ruta % — queden % — transcorregut: % — ETA: %',processed,parades_totals,rec.route_id,remaining,elapsed,eta;
			INSERT INTO atm.sto_serv_disp (temps_finestra_int, stop_id, temps_int, temps_ts, temps_serv_sortida, temps_serv_arribada, num_serv_sortida, num_serv_arribada, lst_stop_sortida, lst_stop_arribada, lst_trip_arribada, lst_trip_sortida, node_pare, es_node, geom)
				with serveis as ( 
					select (((sp.temps_int /(60*60))::int)*60*60) as temps_finestra_int, * 
					from serveis_projectats_tmp sp
					where sp.stop_id=rec_serv.stop_id and sp.temps_int >=inici-(60*60) and sp.temps_int<inici+(60*60)
				),
				data as (
					select serveis.temps_finestra_int, tmp.trip_id, serveis.stop_id as stop_id, serveis.temps_ts as temps_ts, serveis.temps_int as temps_int, tmp.stop_id as stop_rel, tmp.route_id, tmp.temps_ts as temps_ts_rel, tmp.temps_int as temps_int_rel, (tmp.temps_int-serveis.temps_int)/60 as temps_dif,serveis.geom as geom
					FROM serveis_projectats_tmp as tmp, serveis
					where tmp.stop_id in(select stop_id from sto_properes sp where sp.stop_id_propera = serveis.stop_id and tmp.temps_int BETWEEN serveis.temps_int - 3600 AND serveis.temps_int + 3600) or tmp.stop_id =serveis.stop_id 
				)
				select data.temps_finestra_int, data.stop_id, data.temps_int, data.temps_ts,
					sum(case when (temps_dif>=0) then (data.temps_dif)::int else 0 end ) as temps_serv_sortida,
					sum(case when (temps_dif<0) then (-data.temps_dif)::int else 0 end ) as temps_serv_arribada,
					sum(case when (temps_dif>=0) then 1 else 0 end) as num_serv_sortida,
					sum(case when (temps_dif<0) then 1 else 0 end) as num_serv_arribada,
				    COALESCE(string_agg(CASE WHEN (temps_dif>=0) THEN data.stop_rel::text END, ',' ORDER BY data.stop_rel),'') as lst_stop_sortida,
				    COALESCE(string_agg(CASE WHEN (temps_dif<0) THEN data.stop_rel::text END, ',' ORDER BY data.stop_rel),'') as lst_stop_arribada,
				    COALESCE(string_agg(CASE WHEN (temps_dif>=0) THEN data.trip_id END, ',' ORDER BY data.trip_id),'') as lst_trip_sortida,
				    COALESCE(string_agg(CASE WHEN (temps_dif<0) THEN data.trip_id END, ',' ORDER BY data.trip_id),'') as lst_trip_arribada,
					null as node_pare, false as es_node,
					data.geom
				from data
				group by data.temps_finestra_int,data.stop_id, data.temps_int, data.temps_ts, data.geom;

			--end if;	
	 		GET DIAGNOSTICS tmp = ROW_COUNT;
		    RAISE NOTICE 'STO_SERV_DISP inserted= %',tmp;

			serveis_insertats:=serveis_insertats+tmp;
		END LOOP;
		--COMMIT;
	end IF;
	
	-- Finalitzar i calcular duració
	exec_end_time := clock_timestamp();
	elapsed := exec_end_time - exec_start_time;
    RAISE NOTICE '(items %) TEMPS PROCÉS CERCA: %',serveis_insertats, elapsed;
	processed:=0;
	select count(*) into remaining
	from sto_serv_disp ssd 
	where not es_node and node_pare is null and 
		ssd.temps_int >=inici and ssd.temps_int<inici+(60*60) and ssd.num_serv_sortida>1;
	
	--Identifiquem i Etiquetem els nodes de servei, agrupant per SERVEIS que SURTEN 
	-- Primer, identificar grups de parades relacionades i marcar només el node principal de cada grup
	FOR rec IN
		select * 
		from sto_serv_disp ssd 
		where not es_node and node_pare is null and 
			ssd.temps_int >=inici-(60*60) and ssd.temps_int<inici+(60*60) and ssd.num_serv_sortida>1
		order by num_serv_sortida desc, stop_id
	LOOP
		remaining:=remaining-1;
		
		-- Verificar si aquest registre ja ha estat processat (si ja té node_pare assignat o és node)
		if NOT EXISTS (
			SELECT 1 FROM sto_serv_disp 
			WHERE id = rec.id AND (es_node = true OR node_pare IS NOT NULL)
		) then 
			-- Verificar si alguna de les parades de la seva llista ja és un node principal
			IF NOT EXISTS (
				SELECT 1 FROM sto_serv_disp sd
				WHERE sd.es_node = true 
				AND sd.temps_int >= inici-(60*60) 
				AND sd.temps_int < inici+(60*60)
				AND (
					sd.stop_id = rec.stop_id OR
					sd.stop_id IN (
						SELECT (regexp_split_to_table(rec.lst_stop_sortida, ','))::text
						WHERE rec.lst_stop_sortida IS NOT NULL AND rec.lst_stop_sortida <> ''
					)
				)
			) THEN
				-- Aquest és el node principal del grup
				RAISE NOTICE 'Etiquetant node principal: % (num_serv_sortida: %)', rec.stop_id, rec.num_serv_sortida;
				
				UPDATE sto_serv_disp sd
				SET es_node = true 
				WHERE id = rec.id;
				
				-- Etiquetem als FILLS del mateix grup
				UPDATE sto_serv_disp sd
				SET node_pare = rec.stop_id
				WHERE sd.stop_id IN (
					SELECT (regexp_split_to_table(rec.lst_stop_sortida, ','))::text
					WHERE rec.lst_stop_sortida IS NOT NULL AND rec.lst_stop_sortida <> ''
				) 
				AND sd.temps_int >= inici 
				AND sd.temps_int < inici+(60*60) 
				AND sd.stop_id <> rec.stop_id
				AND sd.node_pare IS NULL
				AND sd.es_node = false;
				
				GET DIAGNOSTICS tmp = ROW_COUNT;
				RAISE NOTICE 'Fills assignats al node %: %', rec.stop_id, tmp;
				serveis_insertats := serveis_insertats + tmp;
			ELSE
				-- Ja existeix un node principal per aquest grup, assignar com a fill
				UPDATE sto_serv_disp sd
				SET node_pare = (
					SELECT sd2.stop_id FROM sto_serv_disp sd2
					WHERE sd2.es_node = true 
					AND sd2.temps_int >= inici-(60*60) 
					AND sd2.temps_int < inici+(60*60)
					AND (
						sd2.stop_id IN (
							SELECT (regexp_split_to_table(rec.lst_stop_sortida, ','))::text
							WHERE rec.lst_stop_sortida IS NOT NULL AND rec.lst_stop_sortida <> ''
						) OR
						rec.stop_id IN (
							SELECT (regexp_split_to_table(sd2.lst_stop_sortida, ','))::text
							WHERE sd2.lst_stop_sortida IS NOT NULL AND sd2.lst_stop_sortida <> ''
						)
					)
					ORDER BY sd2.num_serv_sortida DESC
					LIMIT 1
				)
				WHERE id = rec.id;
			END IF;
		end if;
	END LOOP;


	exec_end_time := clock_timestamp();
	elapsed := exec_end_time - exec_start_time;
    RAISE NOTICE 'TEMPS TOTAL: %',elapsed;

  	RETURN QUERY
    	SELECT serveis_insertats;
END;
$function$
;