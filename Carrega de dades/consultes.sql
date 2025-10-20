-- CONTROL QUALITAT DADES IN GTFS
select count(t.*) from tri t where not exists ( select 1 from cal c where c.service_id=t.service_id ) and not exists ( select 1 from cal_d cd where cd.service_id=t.service_id and cd.exception_type=1);
select count(r.*) from rou r where not exists ( select 1 from tri t where t.route_id=r.route_id ); --32
select count(st.*) from sto_t st where not exists ( select 1 from tri t where t.trip_id=st.trip_id ); --0
select count(s.*) from sto s where not exists ( select 1 from sto_t st where st.stop_id=s.stop_id ); --695


------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- CONSULTES SERVEIS_PROJECTATS
select * from serveis_projectats sp where true
order by temps_int desc;
select count(*) from serveis_projectats sp ;

with all_s as (select count(s.stop_id) as total_sto from sto s ),
	sto_sp as (select count(s.stop_id) as sto_wo_sp from sto s where not exists ( select 1 from serveis_projectats sp where sp.stop_id=s.stop_id))
select all_s.*, sto_sp.* from all_s, sto_sp;

VACUUM ANALYZE atm.serveis_projectats;

-- Serveis entre dates
select count(*) from serveis_projectats sp where sp.temps_int >= EXTRACT(EPOCH FROM '2025/10/13 00:00:00'::TIMESTAMP) and sp.temps_int < EXTRACT(EPOCH FROM '2025/10/13 00:00:00'::TIMESTAMP)+(60*60);






------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- AVALUACIÓ DE PARADES
delete from sto_puntuades;
select count(*) from sto_puntuades sp where sp.num_serv_sortida_diais not null

-- Actualistza llista de serveis arribada/sortida per cada servei/parada
-- Procés manual
delete from serveis_projectats_tmp ;
insert into serveis_projectats_tmp (
	select * from serveis_projectats sp WHERE sp.temps_int >=EXTRACT(EPOCH FROM '2025/10/13 00:00:00'::TIMESTAMP)  
    AND sp.temps_int <EXTRACT(EPOCH FROM '2025/10/13 00:00:00'::TIMESTAMP) + (60*60)   
    );

UPDATE serveis_projectats sp 
SET lst_serv_arribada = null,
        lst_serv_sortida = null,
        num_serv_sortida = 0,
        num_serv_arribada = 0
    WHERE sp.temps_int >=EXTRACT(EPOCH FROM '2025/10/13 00:00:00'::TIMESTAMP)  
    AND sp.temps_int <EXTRACT(EPOCH FROM '2025/10/13 00:00:00'::TIMESTAMP) + (60*60) 

UPDATE serveis_projectats sp
SET lst_serv_arribada = subq.lst_arribada,
    lst_serv_sortida = subq.lst_sortida,
    num_serv_arribada = subq.num_lst_arribada,
    num_serv_sortida = subq.num_lst_sortida
FROM (
    SELECT sp_main.id as sp_id,
        array_agg(spp_arr.id) FILTER (WHERE spp_arr.id IS NOT NULL) as lst_arribada,
        array_agg(spp_sort.id) FILTER (WHERE spp_sort.id IS NOT NULL) as lst_sortida,
        count(spp_arr.id) FILTER (WHERE spp_arr.id IS NOT NULL) as num_lst_arribada,
        count(spp_sort.id) FILTER (WHERE spp_sort.id IS NOT NULL) as num_lst_sortida
    FROM serveis_projectats_tmp sp_main
    INNER JOIN sto_properes pp ON pp.stop_id = sp_main.stop_id
    LEFT JOIN serveis_projectats_tmp spp_arr ON pp.stop_id_propera = spp_arr.stop_id
        AND spp_arr.temps_int >= sp_main.temps_int - (60*20)
        AND spp_arr.temps_int <= sp_main.temps_int
    LEFT JOIN serveis_projectats_tmp spp_sort ON pp.stop_id_propera = spp_sort.stop_id
        AND spp_sort.temps_int >= sp_main.temps_int
        AND spp_sort.temps_int <= sp_main.temps_int + (60*20)
    WHERE sp_main.temps_int >=EXTRACT(EPOCH FROM '2025/10/13 00:00:00'::TIMESTAMP)  
    AND sp_main.temps_int <EXTRACT(EPOCH FROM '2025/10/13 00:00:00'::TIMESTAMP) + (60*60) 
    GROUP BY sp_main.id
) subq
WHERE sp.id = subq.sp_id;

select * from serveis_projectats sp 
WHERE sp.temps_int >=EXTRACT(EPOCH FROM '2025/10/13 00:00:00'::TIMESTAMP)  
	AND sp.temps_int <EXTRACT(EPOCH FROM '2025/10/13 00:00:00'::TIMESTAMP) + (60*60) 
	
	
-- CONSULTA STO_PUNTUADES
select * from sto_puntuades sp where sp.dia =to_date('2025/10/13', 'YYYY/MM/DD');