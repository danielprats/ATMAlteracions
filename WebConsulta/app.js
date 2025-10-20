/**
 * Script principal de l'aplicació de consulta d'incidències de l'ATM
 * Coordina tots els mòduls i inicialitza l'aplicació
 */

class AlertsApp {
    constructor() {
        this.isInitialized = false;
        this.currentAlerts = [];
    }

    /**
     * Inicialitza l'aplicació
     */
    async init() {
        if (this.isInitialized) {
            return;
        }

        try {
            console.log('Inicialitzant aplicació d\'alertes de l\'ATM...');
            
            // Configurar els components UI
            this.setupUI();
            
            // Carregar les dades
            await this.loadData();
            
            // Mostrar les dades inicials
            await this.refreshDisplay();
            
            this.isInitialized = true;
            console.log('Aplicació inicialitzada correctament');
            
        } catch (error) {
            console.error('Error inicialitzant l\'aplicació:', error);
            uiComponents.showError(error.message);
        }
    }

    /**
     * Configura la interfície d'usuari
     */
    setupUI() {
        // Configurar filtres
        uiComponents.setupFilters((filters) => {
            this.handleFilterChange(filters);
        });

        // Configurar modal
        uiComponents.setupModal();

        // Configurar gestió d'errors globals
        window.addEventListener('error', (event) => {
            console.error('Error global:', event.error);
        });

        // Configurar gestió d'errors de promeses no capturades
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Promesa rebutjada no gestionada:', event.reason);
            event.preventDefault();
        });
    }

    /**
     * Carrega les dades dels CSV
     */
    async loadData() {
        uiComponents.showLoading();
        
        try {
            await dataManager.loadData();
            uiComponents.hideLoading();
            uiComponents.hideError();
            
        } catch (error) {
            uiComponents.hideLoading();
            throw new Error(`Error carregant les dades: ${error.message}`);
        }
    }

    /**
     * Refresca la visualització amb les dades actuals
     */
    async refreshDisplay(filters = {}) {
        try {
            // Obtenir alertes filtrades
            this.currentAlerts = dataManager.getAlerts(filters);
            
            // Renderitzar alertes
            uiComponents.renderAlerts(this.currentAlerts);
            
            // Actualitzar estadístiques
            const stats = dataManager.getStats();
            uiComponents.updateStats(stats);
            
        } catch (error) {
            console.error('Error refrescant la visualització:', error);
            uiComponents.showError('Error mostrant les dades');
        }
    }

    /**
     * Gestiona els canvis en els filtres
     */
    async handleFilterChange(filters) {
        try {
            await this.refreshDisplay(filters);
        } catch (error) {
            console.error('Error aplicant filtres:', error);
            uiComponents.showError('Error aplicant els filtres');
        }
    }

    /**
     * Recarrega completament les dades
     */
    async reload() {
        try {
            // Netejar dades existents
            dataManager.clearData();
            uiComponents.clearFilters();
            
            // Reinicialitzar
            this.isInitialized = false;
            await this.init();
            
        } catch (error) {
            console.error('Error recarregant l\'aplicació:', error);
            uiComponents.showError('Error recarregant les dades');
        }
    }

    /**
     * Exporta les dades actuals (funcionalitat futura)
     */
    exportData(format = 'json') {
        if (!this.currentAlerts || this.currentAlerts.length === 0) {
            alert('No hi ha dades per exportar');
            return;
        }

        try {
            let data;
            let filename;
            let mimeType;

            switch (format.toLowerCase()) {
                case 'json':
                    data = JSON.stringify(this.currentAlerts, null, 2);
                    filename = `alertes_atm_${this._getCurrentDateString()}.json`;
                    mimeType = 'application/json';
                    break;
                
                case 'csv':
                    data = this._convertToCSV(this.currentAlerts);
                    filename = `alertes_atm_${this._getCurrentDateString()}.csv`;
                    mimeType = 'text/csv';
                    break;
                    
                default:
                    throw new Error('Format no suportat');
            }

            this._downloadFile(data, filename, mimeType);
            
        } catch (error) {
            console.error('Error exportant dades:', error);
            alert('Error exportant les dades');
        }
    }

    /**
     * Converteix les dades a format CSV
     */
    _convertToCSV(data) {
        if (!data || data.length === 0) return '';

        const headers = Object.keys(data[0]);
        const csvRows = [
            headers.join(','),
            ...data.map(row => 
                headers.map(header => {
                    const value = row[header] || '';
                    // Escapar cometes i afegir cometes si cal
                    return `"${value.toString().replace(/"/g, '""')}"`;
                }).join(',')
            )
        ];

        return csvRows.join('\n');
    }

    /**
     * Descarrega un fitxer
     */
    _downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = window.URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.style.display = 'none';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        window.URL.revokeObjectURL(url);
    }

    /**
     * Retorna la data actual en format string
     */
    _getCurrentDateString() {
        const now = new Date();
        return now.toISOString().split('T')[0]; // YYYY-MM-DD
    }

    /**
     * Retorna informació sobre l'aplicació
     */
    getAppInfo() {
        return {
            name: 'Consulta d\'Incidències ATM',
            version: '1.0.0',
            description: 'Aplicació web per consultar les incidències del transport de l\'ATM',
            author: 'ATM - Autoritat del Transport Metropolità',
            lastUpdate: new Date().toISOString(),
            totalAlerts: this.currentAlerts ? this.currentAlerts.length : 0,
            isInitialized: this.isInitialized,
            dataLoaded: dataManager.isLoaded
        };
    }
}

// Crear instància global de l'aplicació
const alertsApp = new AlertsApp();

// Inicialitzar quan el DOM estigui carregat
document.addEventListener('DOMContentLoaded', () => {
    alertsApp.init().catch(error => {
        console.error('Error inicialitzant l\'aplicació:', error);
    });
});

// Funcions globals d'utilitat (opcionals, per consola del desenvolupador)
window.alertsApp = alertsApp;
window.dataManager = dataManager;
window.uiComponents = uiComponents;

// Gestió de la recàrrega de la pàgina
window.addEventListener('beforeunload', () => {
    // Netejar recursos si cal
    console.log('Tancant aplicació...');
});

// Registrar service worker per caché (funcionalitat futura)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        // Deixat per implementació futura del service worker
        console.log('Service Worker disponible per implementació futura');
    });
}