import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Any
import ast
import time  # nou

#BCN-->WHERE ST_Within(s.geom,ST_MakeEnvelope(424200, 4600000, 438900, 4605000, 25831))\

# Per regenerar la taula de serveis_projectats
    # delete from serveis_projectats ;
    # VACUUM (FULL, ANALYZE) serveis_projectats;
    # REINDEX TABLE serveis_projectats;

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

def processar_dades(
        data_inici: str,
        periode: int,
        host: str = "192.168.1.251",
        port: int = 5432,
        dbname: str = "gisdb",
        user: str = "atm",
        password: str = "atm",
        tz: timezone = timezone.utc
    ) -> None:
    """
    Processa les dades de rutes GTFS per un període determinat.
    
    Args:
        data_inici: Data d'inici en format 'YYYY/MM/DD'
        periode: Període en hores a processar
        host: Host de la base de dades
        port: Port de la base de dades
        dbname: Nom de la base de dades
        user: Usuari de la base de dades
        password: Contrasenya de la base de dades
        tz: Zona horària (no utilitzada actualment)
    """
    finestra = timedelta(hours=periode)
    data_fi = (datetime.strptime(data_inici, "%Y/%m/%d") + finestra).strftime("%Y/%m/%d")
    conn = crea_conn_postgis(host, port, dbname, user, password)
    
    # Primer actualitzem la taula serveis_tmp
    print("Actualitzant taula serveis_tmp...")
    cur_tmp = conn.cursor()
    try:
        start_time = time.perf_counter()
        #cur_tmp.execute("SELECT atm.actualitza_serveis_tmp();")
        #result = cur_tmp.fetchone()
        elapsed_time = time.perf_counter() - start_time
        
        print(f"Taula serveis_tmp actualitzada correctament")
        #print(f"Resultat: {result[0] if result else 'Completat'}")
        print(f"Temps d'actualització: {timedelta(seconds=elapsed_time)}")
    except psycopg2.Error as e:
        print(f"Error actualitzant serveis_tmp: {e}")
        raise
    finally:
        cur_tmp.close()
    
    # Ara continuem amb el processament normal
    cur1 = conn.cursor()
    cur2 = conn.cursor()

    sql="SELECT DISTINCT t.route_id as route_id\
        FROM atm.cal c\
            LEFT JOIN atm.tri t ON c.service_id = t.service_id\
            --LEFT JOIN atm.sto_t st ON t.trip_id = st.trip_id\
            --LEFT JOIN atm.sto s ON st.stop_id = s.stop_id\
            WHERE to_date(c.start_date::text, 'YYYYMMDD') <= to_date(%s, 'YYYY/MM/DD')\
            AND to_date(c.end_date::text, 'YYYYMMDD')   >= to_date(%s, 'YYYY/MM/DD')\
        order by route_id;"
    # ST_Within(s.geom,ST_MakeEnvelope(424200, 4600000, 438900, 4605000, 25831)) AND 
    # # and s.stop_id in ('COS_19100','COS_19150','COS_16131') \  

    cur1.execute(sql, (data_inici, data_fi,));

    try:
        start = time.perf_counter()  # iniciem mesura
        i = 0
        total = cur1.rowcount
        eta_secs = 0  # inicialitzar per evitar errors
        elapsed = 0   # inicialitzar per evitar errors
        
        for row in cur1:
            i+=1

            sql=f"select atm.projecta_serveis_route('{row[0]}', to_date('{data_inici}', 'YYYY/MM/DD'), to_date('{data_fi}', 'YYYY/MM/DD'))"
            cur2.execute(
                "select atm.projecta_serveis_route(%s, to_date(%s, 'YYYY/MM/DD'), to_date(%s, 'YYYY/MM/DD'));",
                (row[0], data_inici, data_fi,)  # tuple amb un sol element
            )
            row_in = cur2.fetchone()
            
            # Càlcul d’ETA
            elapsed = time.perf_counter() - start
            avg_per_iter = elapsed / i
            remaining = total - i
            eta_secs = int(avg_per_iter * remaining)
            eta_str = str(timedelta(seconds=eta_secs))
            
            print( f"ROUTE: {row[0]} ->[{i}/{total}] ETA: {eta_str})" )

        # Càlcul final del temps total
        elapsed = time.perf_counter() - start
        print(f"Temps total de procés: {timedelta(seconds=elapsed)}")


    except psycopg2.Error as e:
        print(f"Error de base de dades: {e}")
        conn.rollback()
        raise
    except Exception as e:
        print(f"Error general durant el processament: {e}")
        conn.rollback()
        raise
    finally:
        cur1.close()


if __name__ == "__main__":
    # Exemple: processar 12 períodes de 5 minuts a partir del 04/05/2025
    res = processar_dades(data_inici="2025/10/20", periode=24*10)

