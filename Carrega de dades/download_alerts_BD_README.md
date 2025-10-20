# Sistema de Descàrrega d'Alertes ATM - Base de Dades

## Descripció
Sistema automatitzat per descarregar alertes de transport públic de l'API T-mobilitat i guardar-les en una base de dades PostgreSQL.

## Components del Sistema

### 1. Scripts Principals

#### `download_alerts.py`
Script principal que descarrega les alertes de l'API i les guarda a la base de dades.

**Funcionalitats:**
- Connexió a l'API de T-mobilitat
- Processament de dades d'alertes GTFS Realtime
- Emmagatzematge en base de dades PostgreSQL
- Gestió d'errors i logs
- Normalització de dades en taules relacionals

**Ús:**
```bash
python download_alerts.py
```

#### `analyze_alerts_db.py`
Script d'anàlisi que llegeix les dades de la base de dades i genera estadístiques.

**Funcionalitats:**
- Anàlisi estadístic d'alertes
- Evolució temporal
- Exportació a CSV opcional
- Comparativa de dades

**Ús:**
```bash
# Anàlisi ràpida (últimes 24h)
python analyze_alerts_db.py

# Anàlisi personalitzada (últims N dies)
python analyze_alerts_db.py 7

# Exportar a CSV
python analyze_alerts_db.py export
```

### 2. Base de Dades

#### Esquema: `atm_sc`

##### Taula `alerts`
Taula principal d'alertes:
- `id`: Clau primària única
- `alert_id`: ID de l'alerta de l'API
- `cause`: Causa de l'alerta
- `effect`: Efecte de l'alerta
- `header_text`: Títol de l'alerta
- `description_text`: Descripció detallada
- `url`: URL amb més informació
- `creation_time`: Timestamp de creació
- `start_time`: Inici de l'alerta
- `end_time`: Final de l'alerta
- `downloaded_at`: Timestamp de descàrrega

##### Taula `alert_routes`
Rutes afectades per cada alerta:
- `id`: Clau primària
- `alert_id`: Referència a la taula alerts
- `route_id`: ID de la ruta afectada

##### Taula `alert_stops`
Parades afectades per cada alerta:
- `id`: Clau primària
- `alert_id`: Referència a la taula alerts
- `stop_id`: ID de la parada afectada

#### Vista `vw_alerts_complete`
Vista que uneix totes les dades d'alertes amb les seves rutes i parades.

#### Procediment `sp_cleanup_old_alerts(days INTEGER)`
Procediment per eliminar alertes antigues automàticament.

### 3. Scripts d'Automatització

#### `run_download.ps1` (PowerShell)
Script d'automatització per a Windows PowerShell:
- Executa la descàrrega automàticament
- Mostra informació de progrés
- Executa anàlisi opcional
- Gestió d'errors integrada

#### `run_download.bat` (Batch)
Script d'automatització per a Windows CMD:
- Funcionalitat equivalent al PowerShell
- Compatible amb sistemes més antics

### 4. Configuració de Base de Dades

#### `download_alerts_Genera BD.sql`
Script SQL per crear l'estructura de base de dades:
- Creació d'esquema
- Taules amb claus primàries i estrangeres
- Índexs per a rendiment
- Vista de consulta
- Procediments emmagatzemats

## Configuració

### Prerequisits
1. **Python 3.6+** amb les següents llibreries:
   ```
   requests
   pandas
   psycopg2-binary
   protobuf
   gtfs-realtime-bindings
   ```

2. **PostgreSQL** amb accés a la base de dades:
   - Host: 192.168.1.251
   - Port: 5432
   - Base de dades: gisdb
   - Usuari: atm
   - Contrasenya: atm

### Instal·lació

1. **Crear l'estructura de base de dades:**
   ```sql
   -- Executar el fitxer SQL
   \i download_alerts_Genera BD.sql
   ```

2. **Instal·lar dependències Python:**
   ```bash
   pip install -r REQUIREMENTS.txt
   ```

3. **Provar la connexió:**
   ```bash
   python download_alerts.py
   ```

## Funcionament

### Flux de Dades
1. **Descàrrega**: L'API retorna dades en format GTFS Realtime (Protocol Buffers)
2. **Processament**: Les dades es descodifiquen i normalitzen
3. **Emmagatzematge**: S'insereixen a la base de dades en taules relacionals
4. **Anàlisi**: Es generen estadístiques i informes

### Estructura de Dades API
L'API retorna alertes amb la següent estructura:
- **header**: Informació bàsica (títol, descripció)
- **active_period**: Període d'activitat
- **informed_entity**: Entitats afectades (rutes, parades)
- **cause/effect**: Causa i efecte de l'alerta

### Gestió d'Errors
- Connexió a base de dades amb reintentos
- Validació de dades abans d'inserir
- Logs detallats d'operacions
- Rollback automàtic en cas d'error

## Automatització

### Programació de Tasques

#### Windows (Task Scheduler)
```powershell
# Crear tasca que s'executi cada hora
schtasks /create /tn "ATM_Alerts_Download" /tr "powershell.exe -File C:\path\to\run_download.ps1" /sc hourly
```

#### Linux (Cron)
```bash
# Afegir al crontab per executar cada hora
0 * * * * cd /path/to/scripts && python download_alerts.py
```

### Monitoratge
- Revisar logs regularment
- Comprovar integritat de dades
- Verificar connexions de base de dades

## Consultes Útils

### Alertes Actives
```sql
SELECT * FROM atm_sc.vw_alerts_complete 
WHERE start_time <= NOW() AND (end_time IS NULL OR end_time >= NOW());
```

### Estadístiques Diàries
```sql
SELECT DATE(downloaded_at) as dia, COUNT(*) as alertes
FROM atm_sc.alerts 
GROUP BY DATE(downloaded_at)
ORDER BY dia DESC;
```

### Rutes Més Afectades
```sql
SELECT ar.route_id, COUNT(*) as num_alertes
FROM atm_sc.alert_routes ar
JOIN atm_sc.alerts a ON ar.alert_id = a.alert_id
WHERE a.downloaded_at >= NOW() - INTERVAL '7 days'
GROUP BY ar.route_id
ORDER BY num_alertes DESC;
```

## Manteniment

### Neteja de Dades Antigues
```sql
-- Eliminar alertes de més de 30 dies
CALL atm_sc.sp_cleanup_old_alerts(30);
```

### Reindexació
```sql
-- Reindexar taules per mantenir rendiment
REINDEX TABLE atm_sc.alerts;
REINDEX TABLE atm_sc.alert_routes;
REINDEX TABLE atm_sc.alert_stops;
```

## Solució de Problemes

### Error de Connexió
- Verificar credencials de base de dades
- Comprovar connectivitat de xarxa
- Revisar configuració de firewall

### Errors de Dades
- Verificar format de resposta de l'API
- Comprovar logs de Python
- Validar estructura de taules

### Rendiment
- Revisar índexs de base de dades
- Optimitzar consultes
- Considerar particionat per dates

## Contacte
Per a suport tècnic o millores, contactar amb l'equip de desenvolupament.