#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'exemple per analitzar les dades d'alertes ATM des de la base de dades PostgreSQL
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import pandas as pd
from collections import Counter
import sys
from datetime import datetime

def connect_db(host="192.168.1.251", port=5432, dbname="gisdb", user="atm", password="atm"):
    """Estableix connexió amb la base de dades"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except psycopg2.Error as e:
        print(f"Error en connectar a la base de dades: {e}")
        return None

def analyze_alerts_from_db():
    """Analitza les alertes des de la base de dades"""
    
    conn = connect_db()
    if not conn:
        print("No s'ha pogut connectar a la base de dades")
        return False
    
    try:
        print("=" * 60)
        print("ANÀLISI D'ALERTES ATM - DES DE BASE DE DADES")
        print("=" * 60)
        print(f"Data d'anàlisi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Carregar dades des de la vista completa
        print("Carregant dades des de la base de dades...")
        df = pd.read_sql_query("""
            SELECT * FROM atm_sc.v_alerts_complete 
            ORDER BY download_timestamp DESC
        """, conn)
        
        if df.empty:
            print("No s'han trobat alertes a la base de dades")
            return True
        
        print(f"Total registres carregats: {len(df)}")
        print()
        
        # Estadístiques bàsiques
        print("=== ESTADÍSTIQUES BÀSIQUES ===")
        print(f"Total alertes: {len(df)}")
        print(f"Alertes úniques: {df['alert_id'].nunique()}")
        print(f"Període de dades: {df['download_timestamp'].min()} - {df['download_timestamp'].max()}")
        print()
        
        # Últimes descàrregues
        print("=== ÚLTIMES DESCÀRREGUES ===")
        latest_downloads = df['download_timestamp'].value_counts().head(5)
        for timestamp, count in latest_downloads.items():
            print(f"{timestamp}: {count} alertes")
        print()
        
        # Tipus d'efectes
        print("=== TIPUS D'EFECTES ===")
        effects = df['effect'].value_counts()
        for effect, count in effects.items():
            print(f"{effect}: {count}")
        print()
        
        # Rutes més afectades
        print("=== RUTES MÉS AFECTADES ===")
        all_routes = []
        for routes in df['affected_routes'].dropna():
            if routes and routes.strip():
                all_routes.extend([r.strip() for r in routes.split(';') if r.strip()])
        
        if all_routes:
            most_affected_routes = Counter(all_routes).most_common(10)
            for route, count in most_affected_routes:
                print(f"{route}: {count} alertes")
        else:
            print("No s'han trobat rutes afectades")
        print()
        
        # Parades més afectades
        print("=== PARADES MÉS AFECTADES ===")
        all_stops = []
        for stops in df['affected_stops'].dropna():
            if stops and stops.strip():
                all_stops.extend([s.strip() for s in stops.split(';') if s.strip()])
        
        if all_stops:
            most_affected_stops = Counter(all_stops).most_common(10)
            for stop, count in most_affected_stops:
                print(f"{stop}: {count} alertes")
        else:
            print("No s'han trobat parades afectades")
        print()
        
        # Alertes actives (des de la vista d'actives)
        active_df = pd.read_sql_query("SELECT * FROM atm_sc.v_alerts_active", conn)
        print(f"=== ALERTES ACTIVES ===")
        print(f"Total alertes actives: {len(active_df)}")
        
        if len(active_df) > 0:
            print("\nPrimeres 5 alertes actives:")
            for idx, row in active_df.head().iterrows():
                print(f"- ID: {row['alert_id']}")
                print(f"  Efecte: {row['effect']}")
                desc = row['description_cat'] or ''
                print(f"  Descripció: {desc[:100]}{'...' if len(desc) > 100 else ''}")
                print(f"  Inici: {row['active_start']}")
                print()
        
        # Estadístiques per efecte (des de la vista d'estadístiques)
        print("=== ESTADÍSTIQUES PER EFECTE ===")
        stats_df = pd.read_sql_query("SELECT * FROM atm_sc.v_alerts_stats", conn)
        for idx, row in stats_df.iterrows():
            print(f"{row['effect']}: {row['total_alerts']} total, {row['active_alerts']} actives")
        print()
        
        # Evolució temporal
        print("=== EVOLUCIÓ TEMPORAL (ÚLTIMS DIES) ===")
        temporal_df = pd.read_sql_query("""
            SELECT 
                DATE(download_timestamp) as dia,
                COUNT(*) as total_alertes,
                COUNT(DISTINCT alert_id) as alertes_uniques
            FROM atm_sc.alerts 
            WHERE download_timestamp >= NOW() - INTERVAL '7 days'
            GROUP BY DATE(download_timestamp)
            ORDER BY dia DESC
        """, conn)
        
        for idx, row in temporal_df.iterrows():
            print(f"{row['dia']}: {row['total_alertes']} alertes ({row['alertes_uniques']} úniques)")
        
        # Exportar resum
        summary_file = f"alerts_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"RESUM D'ALERTES ATM - BD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Total alertes a la BD: {len(df)}\n")
            f.write(f"Alertes úniques: {df['alert_id'].nunique()}\n")
            f.write(f"Alertes actives: {len(active_df)}\n\n")
            
            f.write("Tipus d'efectes:\n")
            for effect, count in effects.items():
                f.write(f"  {effect}: {count}\n")
            
            f.write("\nRutes més afectades:\n")
            if all_routes:
                for route, count in Counter(all_routes).most_common(10):
                    f.write(f"  {route}: {count}\n")
            
            f.write("\nEstadístiques per efecte:\n")
            for idx, row in stats_df.iterrows():
                f.write(f"  {row['effect']}: {row['total_alerts']} total, {row['active_alerts']} actives\n")
        
        print(f"\nResum guardat a: {summary_file}")
        
    except Exception as e:
        print(f"Error en analitzar les dades: {e}")
        return False
    finally:
        conn.close()
    
    return True

def export_to_csv():
    """Exporta les dades de la BD a CSV per compatibilitat"""
    conn = connect_db()
    if not conn:
        return False
    
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Exportar alertes completes
        print("Exportant alertes a CSV...")
        df = pd.read_sql_query("SELECT * FROM atm_sc.v_alerts_complete", conn)
        csv_filename = f"atm_alerts_from_db_{timestamp}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig', sep=';')
        print(f"Alertes exportades a: {csv_filename}")
        
        # Exportar només alertes actives
        active_df = pd.read_sql_query("SELECT * FROM atm_sc.v_alerts_active", conn)
        active_csv = f"atm_alerts_active_{timestamp}.csv"
        active_df.to_csv(active_csv, index=False, encoding='utf-8-sig', sep=';')
        print(f"Alertes actives exportades a: {active_csv}")
        
        return True
        
    except Exception as e:
        print(f"Error en exportar: {e}")
        return False
    finally:
        conn.close()

def main():
    """Funció principal"""
    print("Script d'anàlisi d'alertes ATM - Base de Dades")
    print("Opcions disponibles:")
    print("1. Anàlisi complet")
    print("2. Exportar a CSV")
    print("3. Tots dos")
    
    if len(sys.argv) > 1:
        option = sys.argv[1]
    else:
        option = input("\nTrieu una opció (1-3) [1]: ").strip() or "1"
    
    success = True
    
    if option in ["1", "3"]:
        success &= analyze_alerts_from_db()
    
    if option in ["2", "3"]:
        print("\n" + "=" * 60)
        success &= export_to_csv()
    
    print("\n" + "=" * 60)
    if success:
        print("ANÀLISI COMPLETADA CORRECTAMENT")
    else:
        print("ERRORS DURANT L'ANÀLISI")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()