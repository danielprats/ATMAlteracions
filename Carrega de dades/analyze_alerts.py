#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'exemple per analitzar les dades d'alertes ATM descarregades
"""

import pandas as pd
from collections import Counter
import sys

def analyze_alerts(csv_file):
    """Analitza el fitxer CSV d'alertes"""
    
    try:
        # Carregar dades
        print(f"Carregant dades de: {csv_file}")
        df = pd.read_csv(csv_file, sep=';')
        print(f"Total registres carregats: {len(df)}")
        print()
        
        # Estadístiques bàsiques
        print("=== ESTADÍSTIQUES BÀSIQUES ===")
        print(f"Total alertes: {len(df)}")
        print(f"Alertes úniques: {df['alert_id'].nunique()}")
        print(f"Periode de dades: {df['download_timestamp'].min()} - {df['download_timestamp'].max()}")
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
            if routes:  # Si no està buit
                all_routes.extend(routes.split(';'))
        
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
            if stops:  # Si no està buit
                all_stops.extend(stops.split(';'))
        
        if all_stops:
            most_affected_stops = Counter(all_stops).most_common(10)
            for stop, count in most_affected_stops:
                print(f"{stop}: {count} alertes")
        else:
            print("No s'han trobat parades afectades")
        print()
        
        # Alertes actives (sense data de finalització)
        active_alerts = df[df['active_end'].isna() | (df['active_end'] == '')]
        print(f"=== ALERTES ACTIVES ===")
        print(f"Total alertes actives: {len(active_alerts)}")
        
        if len(active_alerts) > 0:
            print("\nPrimeres 5 alertes actives:")
            for idx, row in active_alerts.head().iterrows():
                print(f"- ID: {row['alert_id']}")
                print(f"  Efecte: {row['effect']}")
                print(f"  Descripció: {row['description_cat'][:100]}...")
                print(f"  Inici: {row['active_start']}")
                print()
        
        # Exportar resum
        summary_file = csv_file.replace('.csv', '_summary.txt')
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"RESUM D'ALERTES ATM - {df['download_timestamp'].iloc[0]}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total alertes: {len(df)}\n")
            f.write(f"Alertes úniques: {df['alert_id'].nunique()}\n")
            f.write(f"Alertes actives: {len(active_alerts)}\n\n")
            
            f.write("Tipus d'efectes:\n")
            for effect, count in effects.items():
                f.write(f"  {effect}: {count}\n")
            
            f.write("\nRutes més afectades:\n")
            if all_routes:
                for route, count in Counter(all_routes).most_common(10):
                    f.write(f"  {route}: {count}\n")
        
        print(f"Resum guardat a: {summary_file}")
        
    except Exception as e:
        print(f"Error en analitzar les dades: {e}")
        return False
    
    return True

def main():
    """Funció principal"""
    if len(sys.argv) != 2:
        print("Ús: python analyze_alerts.py <fitxer_csv>")
        print("Exemple: python analyze_alerts.py test_alerts.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    print("=" * 60)
    print("ANÀLISI D'ALERTES ATM")
    print("=" * 60)
    
    success = analyze_alerts(csv_file)
    
    if not success:
        sys.exit(1)
    
    print("=" * 60)
    print("ANÀLISI COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    main()