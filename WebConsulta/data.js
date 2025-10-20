/**
 * Mòdul per gestionar les dades dels CSV d'alertes de l'ATM
 * Proporciona funcions per carregar, processar i filtrar les dades
 */

class DataManager {
    constructor() {
        this.alerts = [];
        this.alertRoutes = [];
        this.alertStops = [];
        this.stopOperators = [];
        this.isLoaded = false;
        this.loadingPromise = null;
    }

    /**
     * Carrega tots els fitxers CSV
     */
    async loadData() {
        if (this.loadingPromise) {
            return this.loadingPromise;
        }

        this.loadingPromise = this._performDataLoad();
        return this.loadingPromise;
    }

    async _performDataLoad() {
        try {
            console.log('Iniciant càrrega de dades...');
            
            // Carregar els quatre fitxers CSV en paral·lel
            const [alertsData, routesData, stopsData, operatorsData] = await Promise.all([
                this._loadCSV('alerts.csv'),
                this._loadCSV('alert_routes.csv'),
                this._loadCSV('alert_stops.csv'),
                this._loadCSV('sto_puntuades.csv')
            ]);

            // Processar les dades
            this.alerts = this._parseCSV(alertsData);
            this.alertRoutes = this._parseCSV(routesData);
            this.alertStops = this._parseCSV(stopsData);
            this.stopOperators = this._parseCSV(operatorsData);

            // Debug: mostrar capçaleres i primer registre dels operadors
            const operatorsHeaders = this._parseCSVLine(operatorsData.trim().split('\n')[0]);
            const firstOperatorLine = this._parseCSVLine(operatorsData.trim().split('\n')[1]);
            console.log('Debug - Capçaleres CSV operadors:', operatorsHeaders);
            console.log('Debug - Primera línia dades CSV operadors:', firstOperatorLine);
            console.log('Debug - Primer registre processat:', this.stopOperators[0]);
            
            // Debug: mostrar un mostratge de les dades d'operadors
            console.log('Debug - Primeres 3 entrades d\'operadors:', this.stopOperators.slice(0, 3));
            
            // Debug: mostrar dates úniques disponibles
            const uniqueDates = [...new Set(this.stopOperators.map(op => op.dia))].slice(0, 5);
            console.log('Debug - Dates úniques disponibles als operadors:', uniqueDates);

            // Validar que les dades s'han carregat correctament
            if (this.alerts.length === 0) {
                throw new Error('No s\'han pogut carregar les alertes');
            }

            console.log(`Carregades ${this.alerts.length} alertes, ${this.alertRoutes.length} rutes afectades, ${this.alertStops.length} parades afectades i ${this.stopOperators.length} registres d'operadors`);
            
            this.isLoaded = true;
            return true;

        } catch (error) {
            console.error('Error carregant les dades:', error);
            throw new Error(`Error carregant les dades: ${error.message}`);
        }
    }

    /**
     * Carrega un fitxer CSV
     */
    async _loadCSV(fileName) {
        try {
            const response = await fetch(fileName);
            if (!response.ok) {
                throw new Error(`Error carregant ${fileName}: ${response.status} ${response.statusText}`);
            }
            return await response.text();
        } catch (error) {
            if (error instanceof TypeError) {
                throw new Error(`No es pot accedir al fitxer ${fileName}. Assegura't que el fitxer existeix i és accessible.`);
            }
            throw error;
        }
    }

    /**
     * Parseja el contingut CSV i retorna un array d'objectes
     */
    _parseCSV(csvText) {
        const lines = csvText.trim().split('\n');
        if (lines.length < 2) {
            return [];
        }

        // Obtenir les capçaleres
        const headers = this._parseCSVLine(lines[0]);
        
        // Processar cada línia de dades
        const data = [];
        for (let i = 1; i < lines.length; i++) {
            const values = this._parseCSVLine(lines[i]);
            if (values.length === headers.length) {
                const row = {};
                headers.forEach((header, index) => {
                    row[header] = values[index];
                });
                data.push(row);
            }
        }

        return data;
    }

    /**
     * Parseja una línia CSV tenint en compte les comes dins de cometes
     */
    _parseCSVLine(line) {
        const result = [];
        let current = '';
        let inQuotes = false;
        
        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            
            if (char === '"') {
                inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
                result.push(current.trim()); // Afegir trim per eliminar espais
                current = '';
            } else {
                current += char;
            }
        }
        
        result.push(current.trim()); // Afegir trim per eliminar espais
        
        // Netejar cometes dels valors
        return result.map(value => {
            if (value.startsWith('"') && value.endsWith('"')) {
                return value.slice(1, -1);
            }
            return value;
        });
    }

    /**
     * Retorna totes les alertes ordenades per data descendent
     */
    getAlerts(filters = {}) {
        if (!this.isLoaded) {
            throw new Error('Les dades no han estat carregades encara');
        }

        let filteredAlerts = [...this.alerts];

        // Aplicar filtres
        if (filters.status && filters.status !== '') {
            filteredAlerts = filteredAlerts.filter(alert => 
                alert.status === filters.status
            );
        }

        if (filters.search && filters.search.trim() !== '') {
            const searchTerm = filters.search.toLowerCase().trim();
            filteredAlerts = filteredAlerts.filter(alert => 
                (alert.header_cat && alert.header_cat.toLowerCase().includes(searchTerm)) ||
                (alert.description_cat && alert.description_cat.toLowerCase().includes(searchTerm)) ||
                (alert.alert_id && alert.alert_id.includes(searchTerm))
            );
        }

        // Ordenar per data descendent (més recent primer)
        filteredAlerts.sort((a, b) => {
            const dateA = new Date(a.active_start || a.created_at);
            const dateB = new Date(b.active_start || b.created_at);
            return dateB - dateA;
        });

        return filteredAlerts;
    }

    /**
     * Retorna una alerta específica per ID
     */
    getAlertById(alertId) {
        if (!this.isLoaded) {
            throw new Error('Les dades no han estat carregades encara');
        }

        return this.alerts.find(alert => alert.alert_id === alertId);
    }

    /**
     * Retorna les rutes afectades per una alerta específica
     */
    getRoutesForAlert(alertId) {
        if (!this.isLoaded) {
            throw new Error('Les dades no han estat carregades encara');
        }

        return this.alertRoutes.filter(route => route.alert_id === alertId);
    }

    /**
     * Retorna les parades afectades per una alerta específica
     */
    getStopsForAlert(alertId) {
        if (!this.isLoaded) {
            throw new Error('Les dades no han estat carregades encara');
        }

        return this.alertStops.filter(stop => stop.alert_id === alertId);
    }

    /**
     * Retorna els operadors que passen per una parada en un rang de dates
     */
    getOperatorsForStopInDateRange(stopId, startDate, endDate) {
        if (!this.isLoaded) {
            throw new Error('Les dades no han estat carregades encara');
        }

        const startDateString = this._formatDateForOperators(startDate);
        const endDateString = this._formatDateForOperators(endDate);
        
        console.log(`Debug - Buscant operadors per parada ${stopId} del ${startDateString} al ${endDateString}`);
        
        // Generar totes les dates del rang
        const dateRange = this._generateDateRange(startDateString, endDateString);
        console.log(`Debug - Dates del rang:`, dateRange);
        
        const allOperators = new Set();
        let daysWithData = 0;
        const operatorsByDate = {};
        
        dateRange.forEach(dateString => {
            const operatorData = this.stopOperators.filter(op => 
                op.stop_id === stopId && op.dia === dateString
            );
            
            if (operatorData.length > 0) {
                daysWithData++;
                operatorsByDate[dateString] = [];
                
                operatorData.forEach(opRecord => {
                    if (opRecord.lst) {
                        const operators = opRecord.lst.split(',').map(op => op.trim());
                        operators.forEach(op => {
                            allOperators.add(op);
                            operatorsByDate[dateString].push(op);
                        });
                    }
                });
            }
        });

        console.log(`Debug - Trobat per ${stopId} en rang: ${allOperators.size} operadors únics en ${daysWithData} dies`);
        console.log(`Debug - Operadors per data:`, operatorsByDate);
        
        return {
            operators: Array.from(allOperators),
            count: allOperators.size,
            daysWithData: daysWithData,
            operatorsByDate: operatorsByDate
        };
    }

    /**
     * Genera un array de dates entre dues dates (format YYYY-MM-DD)
     */
    _generateDateRange(startDate, endDate) {
        const dates = [];
        const start = new Date(startDate);
        const end = new Date(endDate);
        
        if (isNaN(start.getTime()) || isNaN(end.getTime())) {
            console.log(`Debug - Dates invàlides: ${startDate}, ${endDate}`);
            return [];
        }
        
        const current = new Date(start);
        while (current <= end) {
            dates.push(current.toISOString().split('T')[0]);
            current.setDate(current.getDate() + 1);
        }
        
        return dates;
    }

    /**
     * Retorna els operadors que passen per una parada en una data específica
     */
    getOperatorsForStop(stopId, date) {
        if (!this.isLoaded) {
            throw new Error('Les dades no han estat carregades encara');
        }

        const dateString = this._formatDateForOperators(date);
        console.log(`Debug - Buscant operadors per parada ${stopId} en data ${dateString}`);
        
        // Debug: mostrar primer alguns registres del CSV per verificar el parsing
        console.log(`Debug - Primeres 3 entrades stopOperators:`, this.stopOperators.slice(0, 3));
        
        // Debug: mostrar registres que coincideixen amb el stop_id
        const matchingStops = this.stopOperators.filter(op => op.stop_id === stopId);
        console.log(`Debug - Registres per parada ${stopId}:`, matchingStops);
        
        // Buscar NOMÉS data exacta
        const operatorData = this.stopOperators.find(op => {
            const stopMatch = op.stop_id === stopId;
            const dateMatch = op.dia === dateString;
            console.log(`Debug - Comparant: stop_id="${op.stop_id}" === "${stopId}" (${stopMatch}), dia="${op.dia}" === "${dateString}" (${dateMatch})`);
            return stopMatch && dateMatch;
        });

        if (operatorData) {
            console.log(`Debug - Trobat: ${operatorData.lst} (${operatorData.num} operadors)`);
            return {
                operators: operatorData.lst ? operatorData.lst.split(',').map(op => op.trim()) : [],
                count: parseInt(operatorData.num) || 0
            };
        }

        console.log(`Debug - No trobat per parada ${stopId} en data exacta ${dateString}`);
        return {
            operators: [],
            count: 0
        };
    }

    /**
     * Retorna informació dels operadors per totes les parades afectades d'una alerta
     */
    getOperatorsInfoForAlert(alertId) {
        if (!this.isLoaded) {
            throw new Error('Les dades no han estat carregades encara');
        }

        const alert = this.getAlertById(alertId);
        if (!alert) return null;

        const stops = this.getStopsForAlert(alertId);
        
        // Determinar si l'alerta té data de final o està oberta
        const hasExplicitEndDate = alert.active_end && alert.active_end.trim() !== '';
        const isActiveAlert = alert.status === 'ACTIVE' || alert.status === 'ACTIVE_OLD';
        const useCurrentDate = !hasExplicitEndDate && isActiveAlert;
        
        // Si l'alerta està oberta sense data final, utilitzar la data actual
        const effectiveEndDate = hasExplicitEndDate ? alert.active_end : 
                                (useCurrentDate ? new Date().toISOString() : null);
        
        const shouldUseRange = hasExplicitEndDate || useCurrentDate;
        
        // Debug: mostrar informació de l'alerta
        console.log(`Debug - Alerta ${alertId}: data inici=${alert.active_start}, data final=${alert.active_end}, estat=${alert.status}, usa rang=${shouldUseRange}, data efectiva final=${effectiveEndDate}, parades=${stops.length}`);
        
        const dateRangeText = shouldUseRange ? 
            `${this._formatDateForOperators(alert.active_start)} a ${useCurrentDate ? 'avui' : this._formatDateForOperators(effectiveEndDate)}` :
            this._formatDateForOperators(alert.active_start);
        
        const operatorsInfo = {
            totalStops: stops.length,
            stopsWithOperators: 0,
            allOperators: new Set(),
            stopDetails: [],
            dateRange: dateRangeText,
            isOpenAlert: useCurrentDate
        };

        stops.forEach(stop => {
            let operatorData;
            
            if (shouldUseRange) {
                // Buscar operadors per tots els dies del període (fins a data final o avui)
                operatorData = this.getOperatorsForStopInDateRange(stop.stop_id, alert.active_start, effectiveEndDate);
                console.log(`Debug - Parada ${stop.stop_id} en període ${dateRangeText}: operadors únics=${operatorData.count}, dies amb dades=${operatorData.daysWithData}`);
            } else {
                // Buscar operadors només per la data d'inici
                operatorData = this.getOperatorsForStop(stop.stop_id, alert.active_start);
                console.log(`Debug - Parada ${stop.stop_id} en data ${this._formatDateForOperators(alert.active_start)}: operadors=${operatorData.count}, llista=${operatorData.operators.join(', ')}`);
            }
            
            if (operatorData.count > 0) {
                operatorsInfo.stopsWithOperators++;
                operatorData.operators.forEach(op => operatorsInfo.allOperators.add(op));
            }

            operatorsInfo.stopDetails.push({
                stopId: stop.stop_id,
                operators: operatorData.operators,
                count: operatorData.count,
                daysWithData: operatorData.daysWithData || 1
            });
        });

        const result = {
            ...operatorsInfo,
            allOperators: Array.from(operatorsInfo.allOperators),
            totalUniqueOperators: operatorsInfo.allOperators.size,
            isDateRange: shouldUseRange
        };
        
        console.log(`Debug - Resultat final per alerta ${alertId}:`, result);
        return result;
    }

    /**
     * Retorna estadístiques de les alertes
     */
    getStats() {
        if (!this.isLoaded) {
            return {
                total: 0,
                active: 0,
                activeOld: 0,
                inactive: 0
            };
        }

        const stats = {
            total: this.alerts.length,
            active: 0,
            activeOld: 0,
            inactive: 0
        };

        this.alerts.forEach(alert => {
            switch (alert.status) {
                case 'ACTIVE':
                    stats.active++;
                    break;
                case 'ACTIVE_OLD':
                    stats.activeOld++;
                    break;
                case 'INACTIVE':
                    stats.inactive++;
                    break;
            }
        });

        return stats;
    }

    /**
     * Formata una data per mostrar-la a la interfície
     */
    formatDate(dateString) {
        if (!dateString) return 'No especificada';
        
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) return 'Data invàlida';
            
            return date.toLocaleDateString('ca-ES', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return 'Data invàlida';
        }
    }

    /**
     * Formata l'estat de l'alerta per mostrar-lo a la interfície
     */
    formatStatus(status) {
        const statusMap = {
            'ACTIVE': 'Actiu',
            'ACTIVE_OLD': 'Actiu (Antic)',
            'INACTIVE': 'Inactiu'
        };
        
        return statusMap[status] || status;
    }

    /**
     * Retorna la classe CSS per l'estat de l'alerta
     */
    getStatusClass(status) {
        const classMap = {
            'ACTIVE': 'status-active',
            'ACTIVE_OLD': 'status-active-old',
            'INACTIVE': 'status-inactive'
        };
        
        return classMap[status] || 'status-inactive';
    }

    /**
     * Formata una data per buscar operadors (format YYYY-MM-DD)
     */
    _formatDateForOperators(dateString) {
        if (!dateString) return null;
        
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) return null;
            
            const formatted = date.toISOString().split('T')[0];
            console.log(`Debug - Formatant data: ${dateString} -> ${formatted}`);
            return formatted;
        } catch (error) {
            console.log(`Debug - Error formatant data: ${dateString}`, error);
            return null;
        }
    }

    /**
     * Neteja les dades carregades
     */
    clearData() {
        this.alerts = [];
        this.alertRoutes = [];
        this.alertStops = [];
        this.stopOperators = [];
        this.isLoaded = false;
        this.loadingPromise = null;
    }
}

// Crear una instància global del gestor de dades
const dataManager = new DataManager();