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

def processar_dades(
        data_inicial: str,
        n: int,
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
    # 1. Obtenir timestamps en segons UNIX amb una DELTA
    dt0 = datetime.strptime(data_inicial, "%d/%m/%Y").replace(tzinfo=tz)
    delta = timedelta(minutes=60)
    timestamps = [int((dt0 + i * delta).timestamp()) for i in range(n)]
    
    # 2. Connexió i cursor
    conn = crea_conn_postgis(host, port, dbname, user, password)
    cur = conn.cursor()
    resultats: List[Optional[Any]] = []

    try:
        start = time.perf_counter()  # iniciem mesura
        i=0
        total = len(timestamps)
        for idx,ts in enumerate(timestamps, start=1):
            cur.execute(
                "SELECT atm.calcula_serv_arr_sor_stops_finestra(%s, true);",
                (ts,)  # tuple amb un sol element
            )
            row = cur.fetchone()
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

if __name__ == "__main__":
    # Exemple: processar 12 períodes de 5 minuts a partir del 04/05/2025
    res = processar_dades("10/02/2025", 24*7)
