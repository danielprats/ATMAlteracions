-----------------------------------------------------------------------
WITH reg_ids AS (
    SELECT 
        sp.id AS taula_a_id,
        sp.lst_serv_arribada ,
        trim(unnest(string_to_array(sp.lst_serv_arribada, ',')))::INTEGER AS id,
        sp.stop_id
    FROM sto_puntuades sp
    WHERE sp.lst_serv_arribada IS NOT NULL 
      AND sp.lst_serv_arribada != ''
      --and sp.stop_id='COS_19100'
),
tr as (SELECT sp.route_id,
		    sp.trip_id,
		    reg_ids.stop_id
		FROM serveis_projectats sp
		INNER JOIN reg_ids ON sp.id = reg_ids.id)
select string_agg(distinct age.agency_name,',') as lst,
	count(distinct age.agency_name) as num,
	tr.stop_id
from rou, tri, age, tr  
where rou.route_id=tr.route_id 
	and tr.trip_id=tri.trip_id
	and rou.agency_id=age.agency_id
	--and tr.stop_id='COS_19100'
group by tr.stop_id