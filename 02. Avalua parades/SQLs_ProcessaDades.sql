-- atm.sto_serv_disp definition

-- Drop table

-- DROP TABLE atm.sto_serv_disp;
CREATE SEQUENCE atm.seq_sto_serv_disp_id
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;

-- atm.sto_serv_disp definition

-- Drop table

-- DROP TABLE atm.sto_serv_disp;

CREATE TABLE atm.sto_serv_disp (
	temps_finestra_int int4 NULL,
	stop_id text NULL,
	temps_int int4 NULL,
	temps_ts timestamp NULL,
	temps_serv_sortida int4 NULL,
	temps_serv_arribada int4 NULL,
	num_serv_sortida int4 NULL,
	num_serv_arribada int4 NULL,
	lst_stop_sortida text NULL,
	lst_stop_arribada text NULL,
	lst_route_sortida text NULL,
	lst_route_arribada text NULL,
	node_pare text NULL,
	es_node bool NULL,
	geom public.geometry(point, 25831) NULL,
	id int4 DEFAULT nextval('seq_sto_serv_disp_id'::regclass) NULL,
	trip_id text NULL,
	lst_trip_arribada text NULL,
	lst_trip_sortida text NULL
);
CREATE INDEX sto_serv_disp_es_pare_idx ON atm.sto_serv_disp USING btree (es_node);
CREATE INDEX sto_serv_disp_geom_idx ON atm.sto_serv_disp USING gist (geom);
CREATE INDEX sto_serv_disp_id_idx ON atm.sto_serv_disp USING btree (id);
CREATE INDEX sto_serv_disp_node_pare_idx ON atm.sto_serv_disp USING btree (node_pare);
CREATE INDEX sto_serv_disp_num_serv_sortida_idx ON atm.sto_serv_disp USING btree (num_serv_sortida);
CREATE INDEX sto_serv_disp_stop_id_idx ON atm.sto_serv_disp USING btree (stop_id);
CREATE INDEX sto_serv_disp_temps_finestra_int_idx ON atm.sto_serv_disp USING btree (temps_finestra_int);
CREATE INDEX sto_serv_disp_temps_int_idx ON atm.sto_serv_disp USING btree (temps_int);