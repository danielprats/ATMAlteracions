# Consulta d'Incidències - ATM

Aplicació web per consultar les incidències de transport de l'Autoritat del Transport Metropolità (ATM) de Barcelona.

## Descripció

Aquesta aplicació permet visualitzar de manera interactiva les incidències del transport públic basant-se en tres fitxers CSV:
- `alerts.csv` - Definició de cada alerta
- `alert_routes.csv` - Rutes afectades per cada alerta  
- `alert_stops.csv` - Parades afectades per cada alerta

## Característiques

✅ **Llista d'alertes ordenada per data** (més recents primer)  
✅ **Filtres per estat** (Actiu, Actiu Antic, Inactiu)  
✅ **Cerca per text** en descripcions i IDs d'alerta  
✅ **Vista de detall** amb rutes i parades afectades  
✅ **Disseny responsive** adaptat a mòbils i tablets  
✅ **Interfície moderna** amb banner oficial de l'ATM  
✅ **Estadístiques en temps real**  
✅ **Codi modular** fàcil d'ampliar  

## Estructura del Projecte

```
WebConsulta/
├── index.html          # Pàgina principal
├── styles.css          # Estils CSS
├── app.js              # Script principal de l'aplicació
├── components.js       # Components de la interfície
├── data.js             # Gestió de dades CSV
├── alerts.csv          # Dades d'alertes
├── alert_routes.csv    # Dades de rutes afectades
├── alert_stops.csv     # Dades de parades afectades
└── README.md           # Aquesta documentació
```

## Instal·lació i Ús

### Opció 1: Servidor Web Local

1. Assegura't que tots els fitxers estan al mateix directori
2. Obre un terminal al directori del projecte
3. Inicia un servidor web local:

**Python 3:**
```bash
python -m http.server 8000
```

**Python 2:**
```bash
python -m SimpleHTTPServer 8000
```

**Node.js (amb npx):**
```bash
npx http-server
```

**PHP:**
```bash
php -S localhost:8000
```

4. Obre el navegador a `http://localhost:8000`

### Opció 2: Extensió VS Code

1. Instal·la l'extensió "Live Server" a VS Code
2. Fes clic dret sobre `index.html`
3. Selecciona "Open with Live Server"

## Tecnologies Utilitzades

- **HTML5** - Estructura semàntica
- **CSS3** - Estils moderns amb variables CSS i Flexbox/Grid  
- **JavaScript ES6+** - Programació modular amb classes
- **Font Awesome** - Icones
- **Google Fonts** - Tipografia Inter

## Arquitectura del Codi

### Mòduls Principals

#### `data.js` - Gestió de Dades
- **DataManager**: Classe per carregar i processar els CSV
- Funcions de filtratge i ordenació
- Gestió d'errors de càrrega
- Formatatge de dates i estats

#### `components.js` - Components UI  
- **UIComponents**: Classe per generar elements de la interfície
- Renderització de llistes d'alertes
- Modal de detall
- Gestió de filtres i cerques

#### `app.js` - Coordinador Principal
- **AlertsApp**: Classe principal de l'aplicació  
- Inicialització i coordinació de mòduls
- Gestió d'events globals
- Funcions d'exportació (preparades per ampliar)

### Flux de Dades

1. **Inicialització** (`app.js`)
   - Configuració de la UI
   - Càrrega dels CSV
   - Renderització inicial

2. **Processament** (`data.js`)
   - Parsing dels CSV
   - Filtratge segons criteris
   - Ordenació per data

3. **Visualització** (`components.js`)
   - Generació d'HTML dinàmic
   - Gestió d'events d'usuari
   - Actualització de l'estat visual

## Funcionalitats Implementades

### 📋 Llista d'Alertes
- Visualització paginada d'alertes
- Ordenació per data descendente (més recents primer)
- Informació resumida: ID, dates, estat, descripció

### 🔍 Sistema de Filtres
- **Filtre per estat**: Tots, Actiu, Actiu (Antic), Inactiu
- **Cerca textual**: Busca en descriptions i IDs
- **Debounce** en la cerca per optimitzar rendiment

### 📊 Estadístiques
- Total d'alertes carregades
- Nombre d'alertes actives
- Actualització automàtica segons filtres

### 🔎 Vista de Detall
- Modal amb informació completa de l'alerta
- Llista de rutes afectades
- Llista de parades afectades  
- Dates de creació i actualització

### 📱 Disseny Responsive
- Adaptació automàtica a diferents pantalles
- Menús col·lapsables en mòbil
- Grid responsive per les dades

## Personalització

### Colors i Estils

Els colors de l'ATM estan definits a `styles.css` com a variables CSS:

```css
:root {
    --atm-primary: #003d6b;    /* Blau corporatiu ATM */
    --atm-secondary: #0066cc;   /* Blau secundari */
    --atm-light: #e6f2ff;      /* Blau clar */
    --atm-accent: #ff6b35;     /* Color d'accent */
    /* ... més variables ... */
}
```

### Afegir Noves Funcionalitats

#### 1. Nous Filtres

Edita `components.js` per afegir nous controls de filtre:

```javascript
// Afegir nou filtre de dates al setupFilters()
const dateFilter = document.getElementById('date-filter');
dateFilter.addEventListener('change', (e) => {
    this.currentFilters.dateRange = e.target.value;
    onFilterChange(this.currentFilters);
});
```

#### 2. Noves Visualitzacions

Crea nous mètodes a `UIComponents`:

```javascript
renderChart(data) {
    // Implementar gràfics amb Chart.js o similar
}

renderMap(alerts) {
    // Implementar mapa amb Leaflet o Google Maps
}
```

#### 3. Exportació de Dades

L'estructura per exportar ja està preparada a `app.js`:

```javascript
// Exportar a Excel
alertsApp.exportData('xlsx');

// Exportar a PDF
alertsApp.exportData('pdf');
```

## Extensions Recomanades

### 📈 Gràfics i Estadístiques
- **Chart.js**: Gràfics de barres, línies, pastís
- **D3.js**: Visualitzacions avançades
- **Plotly.js**: Gràfics interactius

### 🗺️ Mapes
- **Leaflet**: Mapes lleugers i personalitzables
- **Mapbox**: Mapes avançats
- **Google Maps API**: Integració amb Google

### 📊 Processament de Dades
- **Papa Parse**: Millor parsing de CSV
- **Lodash**: Utilitats de manipulació de dades
- **Moment.js**: Gestió avançada de dates

### 🎨 UI/UX
- **Bootstrap**: Framework CSS
- **Material-UI**: Components Material Design
- **Animate.css**: Animacions predefinides

## Resolució de Problemes

### Error de Càrrega de CSV

Si els fitxers CSV no es carreguen:

1. **Verifica la ubicació**: Els CSV han d'estar al mateix directori que `index.html`
2. **Configura CORS**: Utilitza un servidor web local, no obris directament l'HTML
3. **Revisa la consola**: Obre les Developer Tools per veure errors detallats

### Rendiment amb Moltes Dades

Per millorar el rendiment amb moltes alertes:

1. **Paginació**: Implementa paginació a `components.js`
2. **Lazy Loading**: Carrega alertes sota demanda
3. **Virtual Scrolling**: Per llistes molt llargues

### Problemes de Responsivitat

1. **Testa en diferents dispositius**: Utilitza les Developer Tools
2. **Ajusta breakpoints**: Modifica les media queries a `styles.css`
3. **Optimitza imatges**: Comprimeix el logo de l'ATM

## Manteniment

### Actualització de Dades

1. Substitueix els fitxers CSV per versions actualitzades
2. Mantén la mateixa estructura de columnes
3. L'aplicació detectarà automàticament els canvis

### Backups

Recomendable fer còpies de seguretat de:
- Fitxers CSV originals
- Configuracions personalitzades
- Extensions implementades

## Roadmap Futur

### V1.1 (Curt termini)
- [ ] Paginació de resultats
- [ ] Exportació a Excel/PDF
- [ ] Cache local per millor rendiment
- [ ] Mode fosc/clar

### V1.2 (Mitjà termini)  
- [ ] Mapa interactiu amb rutes i parades
- [ ] Gràfics estadístics
- [ ] Notificacions push per noves alertes
- [ ] API REST per accés extern

### V2.0 (Llarg termini)
- [ ] Base de dades per emmagatzematge persistent
- [ ] Autenticació d'usuaris
- [ ] Dashboard d'administració
- [ ] App mòbil nativa

## Contribució

Per contribuir al projecte:

1. Mantén l'estructura modular existent
2. Comenta el codi de manera clara
3. Segueix les convencions de nomenclatura
4. Testa les noves funcionalitats
5. Actualitza aquesta documentació

## Contacte

Per dubtes o suggeriments sobre l'aplicació:
- **Organisme**: ATM - Autoritat del Transport Metropolità
- **Web**: [www.atm.cat](https://www.atm.cat)

## Llicència

© 2025 Autoritat del Transport Metropolità (ATM)  
Aquest projecte està desenvolupat per ús intern de l'ATM.