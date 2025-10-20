# Guia d'ús del script download_alerts.py

## Descripció
Aquest script descarrega alertes en temps real de l'API de T-mobilitat d'ATM i les guarda en format CSV.

## Requisits
- Python 3.6 o superior
- Llibreries: requests, pandas

## Instal·lació de dependències
```bash
pip install requests pandas
```

## Ús bàsic

### 1. Execució simple (nom de fitxer automàtic)
```bash
python download_alerts.py
```
Genera un fitxer amb nom automàtic: `atm_alerts_YYYYMMDD_HHMMSS.csv`

### 2. Execució amb nom de fitxer personalitzat
```bash
python download_alerts.py alertes_atm.csv
```

### 3. Execució des de PowerShell
```powershell
python .\download_alerts.py
```

## Estructura del CSV generat

El fitxer CSV conté les següents columnes:

| Columna | Descripció |
|---------|------------|
| download_timestamp | Data i hora de descàrrega |
| api_timestamp | Timestamp de l'API |
| gtfs_version | Versió GTFS Realtime |
| incrementality | Tipus d'actualització |
| alert_id | ID únic de l'alerta |
| effect | Tipus d'efecte (SIGNIFICANT_DELAYS, NO_SERVICE, etc.) |
| active_start | Data i hora d'inici de l'alerta |
| active_end | Data i hora de finalització de l'alerta |
| header_cat | Títol en català |
| header_es | Títol en castellà |
| header_en | Títol en anglès |
| description_cat | Descripció en català |
| description_es | Descripció en castellà |
| description_en | Descripció en anglès |
| affected_routes | Rutes afectades (separades per ;) |
| affected_stops | Parades afectades (separades per ;) |
| url_cat | URL amb més informació en català |
| url_es | URL amb més informació en castellà |
| url_en | URL amb més informació en anglès |

## Exemples de codi per integració

### Carregar dades des de Python
```python
import pandas as pd

# Carregar el CSV
df = pd.read_csv('atm_alerts_20251006_143022.csv', sep=';')

# Mostrar alertes actives
print(f"Total alertes: {len(df)}")

# Filtrar per tipus d'efecte
delays = df[df['effect'] == 'SIGNIFICANT_DELAYS']
print(f"Alertes amb retards: {len(delays)}")

# Mostrar rutes més afectades
all_routes = []
for routes in df['affected_routes'].dropna():
    all_routes.extend(routes.split(';'))

from collections import Counter
most_affected = Counter(all_routes).most_common(5)
print("Rutes més afectades:", most_affected)
```

### Automatització amb programador de tasques

#### Windows (Task Scheduler)
1. Obrir "Programador de tasques"
2. Crear tasca bàsica
3. Configurar per executar cada 15 minuts
4. Acció: Iniciar programa
   - Programa: `python`
   - Arguments: `C:\ruta\al\download_alerts.py`

#### Linux (crontab)
```bash
# Executar cada 15 minuts
*/15 * * * * /usr/bin/python3 /ruta/al/download_alerts.py

# Executar cada hora a les 00 minuts
0 * * * * /usr/bin/python3 /ruta/al/download_alerts.py
```

## Gestió d'errors

El script gestiona automàticament:
- Errors de connexió a internet
- Timeouts de l'API
- Errors de format JSON
- Problemes d'escriptura de fitxers

En cas d'error, el script mostrarà un missatge descriptiu i sortirà amb codi 1.

## Monitorització

Per monitoritzar l'execució, pots redirigir la sortida a un fitxer de log:

```bash
python download_alerts.py >> download_log.txt 2>&1
```

## API de T-mobilitat

- URL: https://t-mobilitat.atm.cat/opendata/alerts/json/user/token/open
- Format: GTFS Realtime en JSON
- Actualització: En temps real
- Accés: Públic, sense autenticació