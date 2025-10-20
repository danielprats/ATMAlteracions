import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Any
import ast
import time  # nou

def crea_conn_postgis(
    host: str = "localhost",
    port: int = 5432,
    dbname: str = "meudb",
    user: str = "postgres",
    password: str = "secreto"
) -> psycopg2.extensions.connection:
    """
    Retorna una connexió a PostGIS amb autocommit habilitat.
    """
    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return conn

def actualitzaConnexions(
        data_inicial: str,
        temps_espera: int,
        num_hores: int,
        *,
        host: str = "192.168.1.251",
        port: int = 5432,
        dbname: str = "gisdb",
        user: str = "atm",
        password: str = "atm",
        tz: timezone = timezone.utc
    ) -> List[Optional[Any]]:
    """
    Genera els propers N timestamps cada 5 minuts a partir de data_inicial (DD/MM/YYYY),
    crida la funció SQL atm_sc.processa_sto_serv_disp5m(timestamp) per a cada un,
    i retorna la llista de resultats.
    """
    conn = crea_conn_postgis(host, port, dbname, user, password)
    cur = conn.cursor()

    # 1. Obtenir timestamps en segons UNIX amb una DELTA
    dt0 = datetime.strptime(data_inicial, "%Y/%m/%d").replace(tzinfo=tz)
    delta = timedelta(minutes=60)
    timestamps = [int((dt0 + i * delta).timestamp()) for i in range(num_hores)]
    
    # 2. Connexió i cursor
    resultats: List[Optional[Any]] = []

    try:            
        start = time.perf_counter()  # iniciem mesura
        i=0
        total = len(timestamps)
        for idx,ts in enumerate(timestamps, start=1):
            
            sql = """delete from serveis_projectats_tmp"""
            cur.execute(sql)

            sql = """insert into serveis_projectats_tmp 
                        select * from serveis_projectats sp \
                        where sp.temps_int >= %s
                            AND sp.temps_int < %s+(60*60)"""
            cur.execute(sql, (ts, ts))
        
            sql="UPDATE serveis_projectats sp\
                    SET lst_serv_arribada = null,\
                        lst_serv_sortida = null,\
                        num_serv_sortida = 0,\
                        num_serv_arribada = 0\
                    WHERE sp.temps_int >= %s and sp.temps_int < %s+(60*60);"
            cur.execute(sql, (ts, ts))

            sql="UPDATE serveis_projectats sp\
                SET lst_serv_arribada = subq.lst_arribada,\
                    lst_serv_sortida = subq.lst_sortida,\
                    num_serv_arribada = subq.num_lst_arribada,\
                    num_serv_sortida = subq.num_lst_sortida\
                FROM (\
                    SELECT sp_main.id as sp_id,\
                        string_agg(spp_arr.id::text,',') FILTER (WHERE spp_arr.id IS NOT NULL) as lst_arribada,\
                        string_agg(spp_sort.id::text,',') FILTER (WHERE spp_sort.id IS NOT NULL) as lst_sortida,\
                        count(spp_arr.id) FILTER (WHERE spp_arr.id IS NOT NULL) as num_lst_arribada,\
                        count(spp_sort.id) FILTER (WHERE spp_sort.id IS NOT NULL) as num_lst_sortida\
                    FROM serveis_projectats_tmp sp_main\
                    INNER JOIN sto_properes pp ON pp.stop_id = sp_main.stop_id\
                    LEFT JOIN serveis_projectats_tmp spp_arr ON pp.stop_id_propera = spp_arr.stop_id\
                        AND spp_arr.temps_int >= sp_main.temps_int - (60*%s)\
                        AND spp_arr.temps_int <= sp_main.temps_int\
                    LEFT JOIN serveis_projectats_tmp spp_sort ON pp.stop_id_propera = spp_sort.stop_id\
                        AND spp_sort.temps_int >= sp_main.temps_int\
                        AND spp_sort.temps_int <= sp_main.temps_int + (60*%s)\
                    WHERE sp_main.temps_int >= %s \
                    AND sp_main.temps_int < %s + (60*60) \
                    GROUP BY sp_main.id\
                ) subq\
                WHERE sp.id = subq.sp_id;"
            cur.execute(sql, (temps_espera, temps_espera, ts, ts))
            # nombre de registres actualitzats per aquesta execució
            row = (cur.rowcount,)
            x = row[0]
            
            # Càlcul d’ETA
            elapsed = time.perf_counter() - start
            avg_per_iter = elapsed / idx
            remaining = total - idx
            eta_secs = int(avg_per_iter * remaining)
            eta_str = str(timedelta(seconds=eta_secs))
            
            dt_str = datetime.fromtimestamp(ts, tz).strftime("%d/%m/%Y %H:%M")
            print(
                f"[{idx}/{total}] ({ts}){dt_str} --> parades generades: {x} "
                f"(ETA: {eta_str})"
            )
            i=i+1

        eta_str = str(timedelta(seconds=eta_secs))
        print(f"Temps total de procés: {timedelta(seconds=elapsed)}")

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

    return resultats

def creaParadesPuntuades(
        data_inicial: str,
        num_dies: int,
        host: str = "192.168.1.251",
        port: int = 5432,
        dbname: str = "gisdb",
        user: str = "atm",
        password: str = "atm",
        tz: timezone = timezone.utc
    ) -> List[Optional[Any]]:
    """
    Executa l'UPDATE de lst_serv_arribada i lst_serv_sortida amb string_agg
    per cada hora dels dies indicats per data_inicial i data_inicial+num_hores.
    """
    conn = crea_conn_postgis(host, port, dbname, user, password)
    cur = conn.cursor()

    # 1. Obtenir timestamps en segons UNIX cada hora
    dt0 = datetime.strptime(data_inicial, "%Y/%m/%d").replace(tzinfo=tz)
    delta = timedelta(hours=24)
    timestamps = [int((dt0 + i * delta).timestamp()) for i in range(num_dies)]
    
    resultats: List[Optional[Any]] = []

    try:
        start = time.perf_counter()
        total = len(timestamps)
        
        for idx, ts in enumerate(timestamps, start=1):
            # Crear datetime object per al timestamp actual
            dt_actual = datetime.fromtimestamp(ts, tz)

            sql="delete from serveis_projectats_tmp;"
            cur.execute(sql)
            sql="insert into serveis_projectats_tmp select * from serveis_projectats where temps_int>=%s and temps_int<%s+(60*60*24);"
            cur.execute(sql, (ts, ts,))

            sql = """delete from sto_puntuades where dia=to_timestamp(%s)::date"""
            cur.execute(sql, (ts,))

            # SQL amb string_agg en lloc d'array_agg
            sql = """INSERT INTO atm.sto_puntuades (
                        stop_id, 
                        dia, 
                        dia_timestamp,
                        lst_serv_arribada_dia,
                        lst_serv_sortida_dia,
                        lst_serv_arribada_setmana,
                        lst_serv_sortida_setmana,
                        num_serv_arribada_dia,
                        num_serv_sortida_dia,
                        num_serv_arribada_setmana,
                        num_serv_sortida_setmana,
                        geom	)
                    WITH 
                    serveis_agrupats AS (
                        SELECT 
                            sp.stop_id,
                            (TO_TIMESTAMP(%s) AT TIME ZONE 'UTC')::DATE as dia_consulta,
                            string_agg(sp.lst_serv_arribada, ',') 
                                FILTER (WHERE sp.lst_serv_arribada != '' and sp.temps_int<%s+(60*60*24)) AS arribada_ids_dia,
                            string_agg(sp.lst_serv_sortida, ',') 
                                FILTER (WHERE sp.lst_serv_sortida != '' and sp.temps_int<%s+(60*60*24)) AS sortida_ids_dia,
                            string_agg(sp.lst_serv_arribada, ',') 
                                FILTER (WHERE sp.lst_serv_arribada != '' ) AS arribada_ids_setmana,
                            string_agg(sp.lst_serv_sortida, ',') 
                                FILTER (WHERE sp.lst_serv_sortida != '') AS sortida_ids_setmana
                        FROM atm.serveis_projectats_tmp sp
                        WHERE sp.temps_int >= %s
                        AND sp.temps_int < %s+(60*60*24*7)
                        AND sp.stop_id IS NOT NULL
                        GROUP BY sp.stop_id
                    )
                    SELECT 
                        so.stop_id,
                        so.dia_consulta AS dia,
                        so.dia_consulta::TIMESTAMP AS dia_timestamp,
                        so.arribada_ids_dia AS lst_serv_arribada_dia,
                        so.sortida_ids_dia AS lst_serv_sortida_dia,
                        so.arribada_ids_setmana AS lst_serv_arribada_setmana,
                        so.sortida_ids_setmana AS lst_serv_sortida_setmana,
                        array_length(string_to_array(so.arribada_ids_dia, ','), 1) AS num_arribades_dia,
                        array_length(string_to_array(so.sortida_ids_dia, ','), 1) AS num_sortides_dia,
                        array_length(string_to_array(so.arribada_ids_setmana, ','), 1) AS num_arribades_setmana,
                        array_length(string_to_array(so.sortida_ids_setmana, ','), 1) AS num_sortides_setmana,
                        s.geom
                    FROM serveis_agrupats so left join sto s on s.stop_id=so.stop_id;
                """

            cur.execute(sql, (ts,ts,ts,ts,ts))
            
            # Recompte de registres actualitzats
            row_count = cur.rowcount
            
            # Càlcul d'ETA
            elapsed = time.perf_counter() - start
            avg_per_iter = elapsed / idx
            remaining = total - idx
            eta_secs = int(avg_per_iter * remaining)
            eta_str = str(timedelta(seconds=eta_secs))
            
            dt_display = dt_actual.strftime("%d/%m/%Y %H:%M")
            print(
                f"[{idx}/{total}] ({ts}) {dt_display} --> registres actualitzats: {row_count} "
                f"(ETA: {eta_str})"
            )
            
            resultats.append(row_count)

        elapsed_final = time.perf_counter() - start

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

    return resultats

if __name__ == "__main__":
    # Exemple: processar primer arrays i després strings
    print("=== FASE 1: Actualitzant amb arrays ===")
    #res1 = actualitzaConnexions(data_inicial="2025/10/20", temps_espera=20, num_hores=24*10)
    
    print("\n=== FASE 2: Actualitzant amb string aggregation ===")
    res2 = creaParadesPuntuades(data_inicial="2025/10/20", num_dies=10)
    