# Software ATM - Processament de dades GTFS i Alertes

El software s'encarrega de fer els següents processos amb l'ordre que cal executar-los:
cada procés té un fitxer amb el nom `xxxxxxxxxxxxxx - Genera BD.sql`, que permet crear l'estructura i PLs de la BD que permet executar el procés.

## Processos disponibles:

### 1. gtfs_to_postgresql.py
Carrega les dades provinents dels fitxers GTFS de dades de ATM, de la carpeta `./dades/` a la BD indicada a les credencials.
- 1.1 Cal revisar paràmetres de connexió

### 2. ProjectaServeis.py
Aquest procés filtra les parades per una capça contenidora (línia 106) i dins un rang de dates establert a `data_inici` i `periode`

### 3. AvaluaServeisDisponibles.py
Aquest procés calcula els serveis disponibles a cada moment a cada parada, per tal de poder estimar quants serveis tenen connexió d'ARRIBADA i quants de SORTIDA d'una parada.

### 4. download_alerts.py ⭐ **NOU**
Aquest procés descarrega les alertes en temps real de l'API de T-mobilitat d'ATM i les guarda en format CSV local.
- 4.1 URL API: https://t-mobilitat.atm.cat/opendata/alerts/json/user/token/open
- 4.2 Genera un fitxer CSV amb timestamp automàtic: `atm_alerts_YYYYMMDD_HHMMSS.csv`
- 4.3 Processa totes les alertes amb traduccions en català, castellà i anglès
- 4.4 Inclou informació de rutes i parades afectades
- 4.5 Scripts d'automatització inclosos: `run_download.bat` i `run_download.ps1`
- 4.6 Script d'anàlisi: `analyze_alerts.py` per generar estadístiques
- 4.7 Documentació completa a: `download_alerts_README.md`

## Ús ràpid del nou sistema d'alertes:

### Descàrrega manual:
```bash
python download_alerts.py
```

### Descàrrega automàtica (PowerShell):
```powershell
.\run_download.ps1
```

### Anàlisi de dades:
```bash
python analyze_alerts.py nom_fitxer.csv
```

## Estructura de fitxers generats:

- `atm_alerts_YYYYMMDD_HHMMSS.csv` - Dades d'alertes en format CSV
- `atm_alerts_YYYYMMDD_HHMMSS_summary.txt` - Resum estadístic de les alertes
- Logs d'execució amb timestamps

## Requisits:

Veure `REQUIREMENTS.txt` per a la llista completa de dependències Python necessàries.

Dependències principals per al sistema d'alertes:
- `requests` - Per a les peticions HTTP a l'API
- `pandas` - Per al processament i anàlisi de dades
- `python-dateutil` - Per al maneig de dates




# PROCÉS EN SQL PUR PAS A PAS

- 