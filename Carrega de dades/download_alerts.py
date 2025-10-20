#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script per descarregar alertes de T-mobilitat ATM i guardar-les a la base de dades PostgreSQL
URL API: https://t-mobilitat.atm.cat/opendata/alerts/json/user/token/open

Autor: GitHub Copilot
Data: Octubre 2025
"""

import requests
import json
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import pandas as pd
from datetime import datetime, timedelta, timezone
import sys
import time

class ATMAlertDownloader:
    """Classe per descarregar i processar alertes de l'API ATM i guardar-les a PostgreSQL"""
    
    def __init__(self, 
                 host: str = "192.168.1.251",
                 port: int = 5432,
                 dbname: str = "gisdb", 
                 user: str = "atm",
                 password: str = "atm"):
        """
        Inicialitza el downloader amb la configuració de la BD
        """
        self.api_url = "https://t-mobilitat.atm.cat/opendata/alerts/json/user/token/open"
        self.db_config = {
            'host': host,
            'port': port,
            'dbname': dbname,
            'user': user,
            'password': password
        }
        self.conn = None
        
    def calculate_status(self, active_start, active_end):
        """
        Calcula l'status de l'alerta segons els criteris:
        - CLOSED: active_end és anterior a ara
        - ACTIVE_OLD: active_end és NULL i active_start fa més de 7 dies
        - ACTIVE: active_end és NULL o posterior a ara
        """
        # Utilitzar datetime amb timezone per evitar errors de comparació
        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)
        
        # Assegurar-se que les dates de la BD també tenen timezone si no en tenen
        if active_start is not None and active_start.tzinfo is None:
            active_start = active_start.replace(tzinfo=timezone.utc)
        if active_end is not None and active_end.tzinfo is None:
            active_end = active_end.replace(tzinfo=timezone.utc)
        
        if active_end is not None and active_end <= now:
            return 'CLOSED'
        elif active_end is None and active_start is not None and active_start < seven_days_ago:
            return 'ACTIVE_OLD'
        else:
            return 'ACTIVE'
        
    def update_existing_statuses(self):
        """
        Actualitza el status de totes les alertes existents a la BD
        """
        if not self.conn:
            print("Error: No hi ha connexió a la base de dades")
            return False
        
        try:
            cursor = self.conn.cursor()
            
            # Obtenir totes les alertes existents
            cursor.execute("""
                SELECT id, active_start, active_end 
                FROM atm.alerts 
                WHERE status != 'CLOSED' OR status IS NULL
            """)
            
            alerts_to_update = cursor.fetchall()
            updated_count = 0
            
            for alert_id, active_start, active_end in alerts_to_update:
                # Calcular nou status
                new_status = self.calculate_status(active_start, active_end)
                
                # Actualitzar alerta principal
                cursor.execute("""
                    UPDATE atm.alerts 
                    SET status = %s 
                    WHERE id = %s
                """, (new_status, alert_id))
                
                # Actualitzar rutes relacionades
                cursor.execute("""
                    UPDATE atm.alert_routes 
                    SET status = %s 
                    WHERE alert_table_id = %s
                """, (new_status, alert_id))
                
                # Actualitzar parades relacionades
                cursor.execute("""
                    UPDATE atm.alert_stops 
                    SET status = %s 
                    WHERE alert_table_id = %s
                """, (new_status, alert_id))
                
                updated_count += 1
            
            print(f"Actualitzats {updated_count} registres d'alertes amb nous status")
            return True
            
        except psycopg2.Error as e:
            print(f"Error en actualitzar els status: {e}")
            return False
        
    def connect_db(self):
        """Estableix connexió amb la base de dades"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            print("Connexió a la base de dades establerta correctament")
            return True
        except psycopg2.Error as e:
            print(f"Error en connectar a la base de dades: {e}")
            return False
    
    def disconnect_db(self):
        """Tanca la connexió amb la base de dades"""
        if self.conn:
            self.conn.close()
            self.conn = None
            print("Connexió a la base de dades tancada")
        
    def download_data(self):
        """Descarrega les dades de l'API"""
        try:
            print(f"Descarregant dades de: {self.api_url}")
            response = requests.get(self.api_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            print(f"Dades descarregades correctament. Timestamp: {data.get('header', {}).get('timestamp', 'N/A')}")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"Error en descarregar les dades: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error en processar el JSON: {e}")
            return None
    
    def process_alerts(self, data):
        """Processa les alertes i les converteix en una llista de diccionaris per a la BD"""
        if not data or 'entity' not in data:
            print("No hi ha dades d'alertes per processar")
            return []
        
        alerts_list = []
        
        # Informació del header
        header_info = data.get('header', {})
        gtfs_version = header_info.get('gtfs_realtime_version', '')
        incrementality = header_info.get('incrementality', '')
        timestamp = header_info.get('timestamp', '')
        
        # Convertir timestamp UNIX a data llegible
        api_timestamp = None
        if timestamp:
            try:
                api_timestamp = datetime.fromtimestamp(timestamp)
            except:
                api_timestamp = None
        
        for entity in data.get('entity', []):
            alert = entity.get('alert', {})
            alert_id = entity.get('id', '')
            
            # Informació dels períodes actius
            active_periods = alert.get('active_period', [])
            if not active_periods:
                # Si no hi ha períodes actius, crear un amb valors buits
                active_periods = [{}]
            
            for period in active_periods:
                start_time = period.get('start', '')
                end_time = period.get('end', '')
                
                # Convertir timestamps a dates
                active_start = None
                active_end = None
                
                if start_time:
                    try:
                        active_start = datetime.fromtimestamp(start_time)
                    except:
                        active_start = None
                
                if end_time:
                    try:
                        active_end = datetime.fromtimestamp(end_time)
                    except:
                        active_end = None
                
                # Efecte de l'alerta
                effect = alert.get('effect', '')
                
                # Textos de descripció i capçalera
                description_texts = alert.get('description_text', {}).get('translation', [])
                header_texts = alert.get('header_text', {}).get('translation', [])
                
                # Extreure texts per idioma
                desc_cat = desc_es = desc_en = ''
                header_cat = header_es = header_en = ''
                
                for desc in description_texts:
                    lang = desc.get('language', '')
                    text = desc.get('text', '')
                    if lang == 'cat':
                        desc_cat = text
                    elif lang == 'es':
                        desc_es = text
                    elif lang == 'en':
                        desc_en = text
                
                for header in header_texts:
                    lang = header.get('language', '')
                    text = header.get('text', '')
                    if lang == 'cat':
                        header_cat = text
                    elif lang == 'es':
                        header_es = text
                    elif lang == 'en':
                        header_en = text
                
                # Entitats informades (rutes i parades afectades)
                informed_entities = alert.get('informed_entity', [])
                routes = []
                stops = []
                
                for entity_info in informed_entities:
                    if 'route_id' in entity_info:
                        routes.append(entity_info['route_id'])
                    if 'stop_id' in entity_info:
                        stops.append(entity_info['stop_id'])
                
                # URLs
                url_translations = alert.get('url', {}).get('translation', [])
                url_cat = url_es = url_en = ''
                
                for url in url_translations:
                    lang = url.get('language', '')
                    text = url.get('text', '')
                    if lang == 'cat':
                        url_cat = text
                    elif lang == 'es':
                        url_es = text
                    elif lang == 'en':
                        url_en = text
                
                # Calcular status de l'alerta
                status = self.calculate_status(active_start, active_end)
                
                # Crear registre per a la BD
                alert_record = {
                    'api_timestamp': api_timestamp,
                    'gtfs_version': gtfs_version,
                    'incrementality': incrementality,
                    'alert_id': alert_id,
                    'effect': effect,
                    'active_start': active_start,
                    'active_end': active_end,
                    'status': status,
                    'header_cat': header_cat,
                    'header_es': header_es,
                    'header_en': header_en,
                    'description_cat': desc_cat,
                    'description_es': desc_es,
                    'description_en': desc_en,
                    'url_cat': url_cat,
                    'url_es': url_es,
                    'url_en': url_en,
                    'routes': routes,
                    'stops': stops
                }
                
                alerts_list.append(alert_record)
        
        print(f"Processades {len(alerts_list)} alertes")
        return alerts_list
    
    def save_to_database(self, alerts_list):
        """Guarda les alertes a la base de dades PostgreSQL"""
        if not alerts_list:
            print("No hi ha alertes per guardar")
            return False
        
        if not self.conn:
            print("Error: No hi ha connexió a la base de dades")
            return False
        
        try:
            cursor = self.conn.cursor()
            saved_count = 0
            
            for alert in alerts_list:
                # Inserir alerta principal
                insert_alert_sql = """
                INSERT INTO atm.alerts (
                    api_timestamp, gtfs_version, incrementality, alert_id, 
                    effect, active_start, active_end, status, header_cat, header_es, 
                    header_en, description_cat, description_es, description_en,
                    url_cat, url_es, url_en
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) 
                ON CONFLICT (alert_id, download_timestamp) DO NOTHING
                RETURNING id;
                """
                
                cursor.execute(insert_alert_sql, (
                    alert['api_timestamp'],
                    alert['gtfs_version'],
                    alert['incrementality'], 
                    alert['alert_id'],
                    alert['effect'],
                    alert['active_start'],
                    alert['active_end'],
                    alert['status'],
                    alert['header_cat'],
                    alert['header_es'],
                    alert['header_en'],
                    alert['description_cat'],
                    alert['description_es'],
                    alert['description_en'],
                    alert['url_cat'],
                    alert['url_es'],
                    alert['url_en']
                ))
                
                result = cursor.fetchone()
                if result:
                    alert_table_id = result[0]
                    saved_count += 1
                    
                    # Inserir rutes afectades
                    for route_id in alert['routes']:
                        insert_route_sql = """
                        INSERT INTO atm.alert_routes (alert_table_id, alert_id, route_id, status)
                        VALUES (%s, %s, %s, %s)
                        """
                        cursor.execute(insert_route_sql, (alert_table_id, alert['alert_id'], route_id, alert['status']))
                    
                    # Inserir parades afectades
                    for stop_id in alert['stops']:
                        insert_stop_sql = """
                        INSERT INTO atm.alert_stops (alert_table_id, alert_id, stop_id, status)
                        VALUES (%s, %s, %s, %s)
                        """
                        cursor.execute(insert_stop_sql, (alert_table_id, alert['alert_id'], stop_id, alert['status']))
            
            print(f"Alertes guardades correctament a la base de dades")
            print(f"Total de registres nous: {saved_count}")
            print(f"Total d'alertes processades: {len(alerts_list)}")
            
            return True
            
        except psycopg2.Error as e:
            print(f"Error en guardar les alertes a la base de dades: {e}")
            return False
    
    def run(self):
        """Executa tot el procés de descàrrega i guardatge a la BD"""
        print("=" * 60)
        print("DESCÀRREGA D'ALERTES ATM T-MOBILITAT")
        print("=" * 60)
        print(f"Inici del procés: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Connectar a la BD
        if not self.connect_db():
            print("ERROR: No s'ha pogut connectar a la base de dades")
            return False
        
        try:
            # Actualitzar status d'alertes existents primer
            print("Actualitzant status d'alertes existents...")
            self.update_existing_statuses()
            print()
            
            # Descarregar dades
            data = self.download_data()
            if data is None:
                print("ERROR: No s'han pogut descarregar les dades")
                return False

            print()

            # Processar alertes
            alerts = self.process_alerts(data)
            if not alerts:
                print("ERROR: No s'han pogut processar les alertes")
                return False

            print()

            # Guardar a la BD
            success = self.save_to_database(alerts)
            if success:
                print()
                print("PROCÉS COMPLETAT CORRECTAMENT!")
                print("Dades guardades a la base de dades atm.alerts")
            else:
                print("ERROR: No s'han pogut guardar les dades a la base de dades")
                return False
            
        finally:
            # Tancar connexió
            self.disconnect_db()
        
        print("=" * 60)
        return True

def main():
    """Funció principal"""
    downloader = ATMAlertDownloader()
    
    # Executar el procés
    success = downloader.run()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()