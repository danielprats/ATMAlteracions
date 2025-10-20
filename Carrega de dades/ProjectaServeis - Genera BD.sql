Aquest fitxer conté els SQL per poder generar l''estructura de la BD que soporta les projeccions de serveis
-------------------------------------------------------------
-- CÀLCUL DE PROJECCIÓ DE SERVEIS
--
-- 1) CREAR LA TAULA PARTICIONADA DE SERVEIS PROJECTATS
-- atm.serveis_projectats definition

-- Drop table

-- DROP TABLE atm.serveis_projectats;

CREATE SEQUENCE atm.serveis_projectats_seq
	MINVALUE 0
	NO MAXVALUE
	START 0
	NO CYCLE;

CREATE TABLE atm.serveis_projectats (
	id int4 DEFAULT nextval('serveis_projectats_seq'::regclass) NOT NULL,
	temps_ts timestamp NULL,
	dia timestamp NULL,
	dow int4 NULL,
	monday int4 NULL,
	tuesday int4 NULL,
	wednesday int4 NULL,
	thursday int4 NULL,
	friday int4 NULL,
	saturday int4 NULL,
	sunday int4 NULL,
	service_id text NULL,
	start_date date NULL,
	end_date date NULL,
	trip_id text NULL,
	route_id text NULL,
	stop_id text NULL,
	stop_sequence int4 NULL,
	arrival_time text NULL,
	departure_time text NULL,
	shape_dist_traveled int4 NULL,
	stop_code text NULL,
	geom public.geometry(point, 25831) NULL,
	temps_int int4 NULL,
	connexions_sortida numeric NULL
);
CREATE INDEX idx_serveis_projectats_geom_idx ON atm.serveis_projectats (geom);
CREATE INDEX idx_serveis_projectats_id ON atm.serveis_projectats (id);
CREATE INDEX serveis_projectats_stop_id_idx ON atm.serveis_projectats (stop_id);
CREATE INDEX serveis_projectats_temps_int_idx ON atm.serveis_projectats (temps_int);
CREATE INDEX serveis_projectats_temps_int_stop_id_idx ON atm.serveis_projectats (temps_int,stop_id);
CREATE INDEX serveis_projectats_temps_ts_idx ON atm.serveis_projectats (temps_ts);
CREATE INDEX serveis_projectats_trip_id_idx ON atm.serveis_projectats (trip_id);

-------------------------------------------------------------
-- atm.serveis_projectats_tmp definition

-- Drop table

-- DROP TABLE atm.serveis_projectats_tmp;

CREATE TABLE atm.serveis_projectats_tmp (
	id int4 NULL,
	temps_ts timestamp NULL,
	dia timestamp NULL,
	dow int4 NULL,
	monday int4 NULL,
	tuesday int4 NULL,
	wednesday int4 NULL,
	thursday int4 NULL,
	friday int4 NULL,
	saturday int4 NULL,
	sunday int4 NULL,
	service_id text NULL,
	start_date date NULL,
	end_date date NULL,
	trip_id text NULL,
	route_id text NULL,
	stop_id text NULL,
	stop_sequence int4 NULL,
	arrival_time text NULL,
	departure_time text NULL,
	shape_dist_traveled int4 NULL,
	stop_code text NULL,
	geom public.geometry(point, 25831) NULL,
	temps_int int4 NULL,
	connexions_sortida numeric NULL
);
CREATE INDEX idx_serveis_projectats_tmp_geom_idx ON atm.serveis_projectats_tmp USING gist (geom);
CREATE INDEX idx_serveis_projectats_tmp_id ON atm.serveis_projectats_tmp USING btree (id);
CREATE INDEX serveis_projectats_tmp_stop_id_idx ON atm.serveis_projectats_tmp USING btree (stop_id);
CREATE INDEX serveis_projectats_tmp_temps_int_idx ON atm.serveis_projectats_tmp USING btree (temps_int);
CREATE INDEX serveis_projectats_tmp_temps_int_stop_id_idx ON atm.serveis_projectats_tmp USING btree (temps_int, stop_id);
CREATE INDEX serveis_projectats_tmp_temps_ts_idx ON atm.serveis_projectats_tmp USING btree (temps_ts);
CREATE INDEX serveis_projectats_tmp_trip_id_idx ON atm.serveis_projectats_tmp USING btree (trip_id);


-------------------------------------------------------------
ALTRES TAULES NECESSÀRIES PER AL CÀLCUL
--
CREATE TABLE atm.sto_properes (
	stop_id varchar NULL,
	num int4 NULL,
	stop_id_propera varchar NULL,
	distancia_m numeric NULL
);
CREATE INDEX sto_properes_stop_id_idx ON atm.sto_properes USING btree (stop_id);
CREATE INDEX sto_properes_stop_id_propera_idx ON atm.sto_properes USING btree (stop_id_propera);
CREATE INDEX sto_properes_stop_id_sto_properes_idx ON atm.sto_properes USING btree (stop_id, stop_id_propera);



CREATE TABLE atm.serveis_tmp (
	id int8 NULL,
	monday int8 NULL,
	tuesday int8 NULL,
	wednesday int8 NULL,
	thursday int8 NULL,
	friday int8 NULL,
	saturday int8 NULL,
	sunday int8 NULL,
	service_id text NULL,
	start_date date NULL,
	end_date date NULL,
	trip_id text NULL,
	route_id text NULL,
	stop_id text NULL,
	stop_sequence int8 NULL,
	arrival_time text NULL,
	departure_time text NULL,
	shape_dist_traveled float8 NULL,
	stop_code text NULL,
	geom public.geometry(point, 25831) NULL
);


-------------------------------------------------------------




















-- S'EXECUTA EL PY PROJECTASERVEIS.PY



-------------------------------------------------------------
-- CÀLCUL DE NODES
--
-- 1) CREAR LA TAULA DE SERVEIS DISPONIBLES I NODES
-- atm.sto_serv_disp definition

-- Drop table

-- DROP TABLE atm.sto_serv_disp;

CREATE TABLE atm.sto_serv_disp (
	stop_id text NULL,
	temps_finestra_int int4 NULL,
	temps timestamptz NULL,
	serv_sortida int8 NULL,
	serv_arribada int8 NULL,
	lst_serv_arribada varchar NULL,
	node_pare varchar NULL,
	es_node bool NULL,
	num_serv_arribada int4 NULL,
	num_serv_sortida int4 NULL,
	id int8 DEFAULT nextval('atm.seq_sto_serv_disp_id'::regclass) NOT NULL,
	lst_serv_sortida varchar NULL,
	temps_int int8 NULL,
	geom public.geometry(point, 25831) NULL,
	temps_finestra timestamptz NULL
);
CREATE INDEX sto_serv_disp_es_pare_idx ON atm.sto_serv_disp USING btree (es_node);
CREATE INDEX sto_serv_disp_geom_idx ON atm.sto_serv_disp USING gist (geom);
CREATE INDEX sto_serv_disp_id_idx ON atm.sto_serv_disp USING btree (id);
CREATE INDEX sto_serv_disp_node_pare_idx ON atm.sto_serv_disp USING btree (node_pare);
CREATE INDEX sto_serv_disp_num_serv_sortida_idx ON atm.sto_serv_disp USING btree (num_serv_sortida);
CREATE INDEX sto_serv_disp_stop_id_idx ON atm.sto_serv_disp USING btree (stop_id);
CREATE INDEX sto_serv_disp_temps_finestra_int_idx ON atm.sto_serv_disp USING btree (temps_finestra_int);
CREATE INDEX sto_serv_disp_temps_int_idx ON atm.sto_serv_disp USING btree (temps_int);



-- CREACIÓ DE LA TAULA TEMPORAL DE CÀCUL
-- atm.serveis_projectats_tmp definition
-- Drop table
-- DROP TABLE atm.serveis_projectats_tmp;
CREATE TABLE atm.serveis_projectats_tmp (
	id int4 NULL,
	temps_ts timestamp NULL,
	dia timestamp NULL,
	dow int4 NULL,
	monday int4 NULL,
	tuesday int4 NULL,
	wednesday int4 NULL,
	thursday int4 NULL,
	friday int4 NULL,
	saturday int4 NULL,
	sunday int4 NULL,
	service_id text NULL,
	start_date date NULL,
	end_date date NULL,
	trip_id text NULL,
	route_id text NULL,
	stop_id text NULL,
	stop_sequence int4 NULL,
	arrival_time text NULL,
	departure_time text NULL,
	shape_dist_traveled int4 NULL,
	stop_code text NULL,
	geom public.geometry(point, 25831) NULL,
	temps_int int4 NULL,
	connexions_sortida numeric NULL
);
CREATE INDEX idx_serveis_projectats_tmp_geom_idx ON atm.serveis_projectats_tmp USING gist (geom);
CREATE INDEX idx_serveis_projectats_tmp_id ON atm.serveis_projectats_tmp USING btree (id);
CREATE INDEX serveis_projectats_tmp_stop_id_idx ON atm.serveis_projectats_tmp USING btree (stop_id);
CREATE INDEX serveis_projectats_tmp_temps_int_idx ON atm.serveis_projectats_tmp USING btree (temps_int);
CREATE INDEX serveis_projectats_tmp_temps_int_stop_id_idx ON atm.serveis_projectats_tmp USING btree (temps_int, stop_id);
CREATE INDEX serveis_projectats_tmp_temps_ts_idx ON atm.serveis_projectats_tmp USING btree (temps_ts);
CREATE INDEX serveis_projectats_tmp_trip_id_idx ON atm.serveis_projectats_tmp USING btree (trip_id);


-- Executar el PY PROJECTASERVEIS.PY



-------------------------------------------------------------
-- CÀRREGA D'ALTERACIONS
---- atm.seq_srv_prj_id definition

-- DROP SEQUENCE atm.seq_srv_prj_id;

CREATE SEQUENCE atm.seq_trip_updates_od
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;

CREATE TABLE IF NOT EXISTS atm.trip_updates_od (
    id int4 DEFAULT nextval('atm.seq_trip_updates_od'::regclass) NOT NULL,
    vehicle_id    TEXT      NOT NULL,
    trip_id       TEXT      NOT NULL,
    start_date    DATE      NOT NULL,
    stop_id       TEXT      NOT NULL,
    arrival_time  TIMESTAMPTZ,
    departure_time TIMESTAMPTZ,
    PRIMARY KEY (id)
);