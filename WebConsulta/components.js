/**
 * Mòdul de components per a la interfície d'alertes de l'ATM
 * Conté funcions per generar i gestionar elements de la interfície
 */

class UIComponents {
    constructor() {
        this.currentFilters = {
            status: '',
            search: ''
        };
    }

    /**
     * Renderitza la llista d'alertes
     */
    renderAlerts(alerts) {
        const container = document.getElementById('alerts-container');
        const noResults = document.getElementById('no-results');
        
        if (!alerts || alerts.length === 0) {
            container.style.display = 'none';
            noResults.style.display = 'block';
            return;
        }

        container.style.display = 'block';
        noResults.style.display = 'none';

        // Ordenar alertes per data d'inici més propera a l'actual
        const sortedAlerts = this._sortAlertsByStartDate(alerts);

        container.innerHTML = sortedAlerts.map(alert => this._createAlertItem(alert)).join('');

        // Afegir event listeners per obrir el modal
        container.querySelectorAll('.alert-item').forEach(item => {
            item.addEventListener('click', (e) => {
                // No obrir el modal si s'ha fet clic en el botó URL
                if (e.target.closest('.url-btn')) {
                    return;
                }
                
                const alertId = item.dataset.alertId;
                this.showAlertDetail(alertId);
            });
        });

        // Afegir event listeners específics per al botó "Veure detall"
        container.querySelectorAll('.view-detail-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const alertItem = btn.closest('.alert-item');
                const alertId = alertItem.dataset.alertId;
                this.showAlertDetail(alertId);
            });
        });
    }

    /**
     * Obté la URL de l'alerta si està disponible
     */
    _getAlertUrl(alert) {
        // Prioritat: català, espanyol, anglès
        if (alert.url_cat && alert.url_cat.trim() !== '') {
            return alert.url_cat.trim();
        }
        if (alert.url_es && alert.url_es.trim() !== '') {
            return alert.url_es.trim();
        }
        if (alert.url_en && alert.url_en.trim() !== '') {
            return alert.url_en.trim();
        }

        // Si no hi ha URL específica, buscar dins les descripcions
        const descriptions = [
            alert.description_cat,
            alert.header_cat,
            alert.description_es,
            alert.header_es,
            alert.description_en,
            alert.header_en
        ];

        for (const desc of descriptions) {
            if (desc) {
                const urlMatch = desc.match(/https?:\/\/[^\s,)]+/i);
                if (urlMatch) {
                    return urlMatch[0];
                }
            }
        }

        return null;
    }

    /**
     * Crea un element HTML per una alerta
     */
    _createAlertItem(alert) {
        const startDate = dataManager.formatDate(alert.active_start);
        const endDate = alert.active_end ? dataManager.formatDate(alert.active_end) : 'Sense final';
        const status = dataManager.formatStatus(alert.status);
        const statusClass = dataManager.getStatusClass(alert.status);

        // Escapar HTML per seguretat
        const description = this._escapeHtml(alert.header_cat || alert.description_cat || 'Sense descripció');
        const truncatedDescription = description.length > 200 ? 
            description.substring(0, 200) + '...' : description;

        // Verificar si hi ha URL disponible
        const alertUrl = this._getAlertUrl(alert);
        const urlButton = alertUrl ? `
            <button class="btn btn-primary url-btn" type="button" onclick="window.open('${alertUrl}', '_blank')" title="Obrir informació adicional">
                <i class="fas fa-external-link-alt"></i>
                Més info
            </button>
        ` : '';

        // Obtenir informació dels operadors
        const operatorsInfo = dataManager.getOperatorsInfoForAlert(alert.alert_id);
        const operatorsPreview = operatorsInfo && operatorsInfo.totalUniqueOperators > 0 ? `
            <div class="alert-operators">
                <span class="operators-label">
                    <i class="fas fa-users"></i>
                    ${operatorsInfo.totalUniqueOperators} operador${operatorsInfo.totalUniqueOperators !== 1 ? 's' : ''} afectat${operatorsInfo.totalUniqueOperators !== 1 ? 's' : ''}
                    ${operatorsInfo.isDateRange ? ' (període complet)' : ''}
                </span>
            </div>
        ` : '';

        // Determinar si l'alerta està tancada
        const isClosedByStatus = alert.status === 'CLOSED' || alert.status === 'INACTIVE';
        const isClosedByDate = alert.active_end && new Date(alert.active_end) < new Date();
        const isClosedAlert = isClosedByStatus || isClosedByDate;
        const closedClass = isClosedAlert ? ' closed' : '';

        return `
            <div class="alert-item${closedClass}" data-alert-id="${alert.alert_id}">
                <div class="alert-content">
                    <div class="alert-header">
                        <div class="alert-info">
                            <div class="alert-id">Alerta #${alert.alert_id}</div>
                            <div class="alert-dates">
                                <div class="alert-date">
                                    <span class="date-label">Inici</span>
                                    <span class="date-value">${startDate}</span>
                                </div>
                                <div class="alert-date">
                                    <span class="date-label">Final</span>
                                    <span class="date-value">${endDate}</span>
                                </div>
                            </div>
                        </div>
                        <div class="alert-status">
                            <span class="status-badge ${statusClass}">${status}</span>
                            <div class="alert-actions">
                                ${urlButton}
                                <button class="btn btn-secondary view-detail-btn" type="button">
                                    <i class="fas fa-eye"></i>
                                    Veure detall
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="alert-description">${truncatedDescription}</div>
                    ${operatorsPreview}
                </div>
            </div>
        `;
    }

    /**
     * Mostra el modal amb el detall de l'alerta
     */
    async showAlertDetail(alertId) {
        try {
            const alert = dataManager.getAlertById(alertId);
            if (!alert) {
                this.showError('No s\'ha trobat l\'alerta especificada');
                return;
            }

            const routes = dataManager.getRoutesForAlert(alertId);
            const stops = dataManager.getStopsForAlert(alertId);
            const operatorsInfo = dataManager.getOperatorsInfoForAlert(alertId);

            const modal = document.getElementById('alert-modal');
            const modalTitle = document.getElementById('modal-title');
            const modalContent = document.getElementById('modal-content');

            modalTitle.textContent = `Detall de l'alerta #${alertId}`;
            modalContent.innerHTML = this._createAlertDetailContent(alert, routes, stops, operatorsInfo);

            modal.classList.add('show');

            // Event listener per tancar el modal
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideAlertDetail();
                }
            });

        } catch (error) {
            console.error('Error mostrant el detall de l\'alerta:', error);
            this.showError('Error carregant el detall de l\'alerta');
        }
    }

    /**
     * Crea el contingut del modal de detall de l'alerta
     */
    _createAlertDetailContent(alert, routes, stops, operatorsInfo) {
        const startDate = dataManager.formatDate(alert.active_start);
        const endDate = alert.active_end ? dataManager.formatDate(alert.active_end) : 'Sense final';
        const createdDate = dataManager.formatDate(alert.created_at);
        const updatedDate = dataManager.formatDate(alert.updated_at);
        const status = dataManager.formatStatus(alert.status);

        const headerCat = this._escapeHtml(alert.header_cat || 'No disponible');
        const descriptionCat = this._escapeHtml(alert.description_cat || 'No disponible');
        const effect = alert.effect || 'No especificat';

        // Verificar si hi ha URL disponible
        const alertUrl = this._getAlertUrl(alert);
        const urlSection = alertUrl ? `
            <div class="modal-section">
                <h4><i class="fas fa-link"></i> Informació Adicional</h4>
                <div class="url-container">
                    <a href="${alertUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-primary url-link">
                        <i class="fas fa-external-link-alt"></i>
                        Obrir enllaç informatiu
                    </a>
                    <div class="url-preview">
                        <span class="url-label">URL:</span>
                        <span class="url-text">${this._escapeHtml(alertUrl)}</span>
                    </div>
                </div>
            </div>
        ` : '';

        // Generar llista de rutes afectades
        const routesHtml = routes.length > 0 ? 
            routes.map(route => `<span class="route-item">${route.route_id}</span>`).join('') :
            '<p style="color: var(--text-secondary); font-style: italic;">Cap ruta afectada</p>';

        // Generar llista de parades afectades
        const stopsHtml = stops.length > 0 ? 
            stops.map(stop => `<span class="stop-item">${stop.stop_id}</span>`).join('') :
            '<p style="color: var(--text-secondary); font-style: italic;">Cap parada afectada</p>';

        // Generar informació dels operadors
        const operatorsSection = operatorsInfo && operatorsInfo.totalUniqueOperators > 0 ? `
            <div class="modal-section">
                <h4><i class="fas fa-users"></i> Operadors Afectats</h4>
                <div class="operators-summary">
                    <div class="detail-grid">
                        <div class="detail-item">
                            <span class="detail-label">Total d'operadors únics</span>
                            <span class="detail-value">${operatorsInfo.totalUniqueOperators}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Parades amb operadors</span>
                            <span class="detail-value">${operatorsInfo.stopsWithOperators} / ${operatorsInfo.totalStops}</span>
                        </div>
                        ${operatorsInfo.isDateRange ? `
                        <div class="detail-item">
                            <span class="detail-label">Període analitzat</span>
                            <span class="detail-value">${operatorsInfo.dateRange} ${operatorsInfo.isOpenAlert ? '(alerta oberta)' : ''}</span>
                        </div>
                        ` : ''}
                    </div>
                    <div class="operators-list">
                        <span class="detail-label">Operadors ${operatorsInfo.isDateRange ? (operatorsInfo.isOpenAlert ? '(des de l\'inici fins avui)' : '(tots els dies del període)') : ''}:</span>
                        <div class="operators-tags">
                            ${operatorsInfo.allOperators.map(op => `<span class="operator-tag">${this._escapeHtml(op)}</span>`).join('')}
                        </div>
                    </div>
                    ${operatorsInfo.isDateRange ? `
                    <div class="date-range-info">
                        <p><i class="fas fa-info-circle"></i> ${operatorsInfo.isOpenAlert ? 
                            'Els operadors mostrats corresponen a tots els dies des de l\'inici de l\'alerta fins avui (alerta encara activa).' :
                            'Els operadors mostrats corresponen a tots els dies del període d\'activitat de l\'alerta.'
                        }</p>
                    </div>
                    ` : ''}
                </div>
            </div>
        ` : '';

        return `
            <div class="modal-section">
                <h4><i class="fas fa-info-circle"></i> Informació General</h4>
                <div class="detail-grid">
                    <div class="detail-item">
                        <span class="detail-label">ID de l'alerta</span>
                        <span class="detail-value">${alert.alert_id}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Estat</span>
                        <span class="detail-value">${status}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Efecte</span>
                        <span class="detail-value">${effect}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Data d'inici</span>
                        <span class="detail-value">${startDate}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Data de final</span>
                        <span class="detail-value">${endDate}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Creat el</span>
                        <span class="detail-value">${createdDate}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Actualitzat el</span>
                        <span class="detail-value">${updatedDate}</span>
                    </div>
                </div>
            </div>

            <div class="modal-section">
                <h4><i class="fas fa-comment"></i> Descripció</h4>
                <div class="detail-item">
                    <span class="detail-label">Títol</span>
                    <span class="detail-value">${headerCat}</span>
                </div>
                <div class="detail-item" style="margin-top: 15px;">
                    <span class="detail-label">Descripció completa</span>
                    <span class="detail-value" style="line-height: 1.6;">${descriptionCat}</span>
                </div>
            </div>

            ${urlSection}

            <div class="modal-section">
                <h4><i class="fas fa-route"></i> Rutes Afectades (${routes.length})</h4>
                <div class="routes-list">
                    ${routesHtml}
                </div>
            </div>

            <div class="modal-section">
                <h4><i class="fas fa-bus-stop"></i> Parades Afectades (${stops.length})</h4>
                <div class="stops-list">
                    ${stopsHtml}
                </div>
            </div>

            ${operatorsSection}
        `;
    }

    /**
     * Amaga el modal de detall
     */
    hideAlertDetail() {
        const modal = document.getElementById('alert-modal');
        modal.classList.remove('show');
    }

    /**
     * Actualitza les estadístiques mostrades
     */
    updateStats(stats) {
        const totalElement = document.getElementById('total-alerts');
        const activeElement = document.getElementById('active-alerts');

        if (totalElement) {
            totalElement.textContent = stats.total.toLocaleString();
        }

        if (activeElement) {
            const totalActive = stats.active + stats.activeOld;
            activeElement.textContent = totalActive.toLocaleString();
        }
    }

    /**
     * Mostra l'estat de càrrega
     */
    showLoading() {
        document.getElementById('loading').style.display = 'block';
        document.getElementById('alerts-container').style.display = 'none';
        document.getElementById('error-message').style.display = 'none';
        document.getElementById('no-results').style.display = 'none';
    }

    /**
     * Amaga l'estat de càrrega
     */
    hideLoading() {
        document.getElementById('loading').style.display = 'none';
    }

    /**
     * Mostra un missatge d'error
     */
    showError(message) {
        const errorElement = document.getElementById('error-message');
        const errorText = errorElement.querySelector('p');
        
        if (errorText) {
            errorText.textContent = message;
        }
        
        document.getElementById('loading').style.display = 'none';
        document.getElementById('alerts-container').style.display = 'none';
        document.getElementById('no-results').style.display = 'none';
        errorElement.style.display = 'block';
    }

    /**
     * Amaga el missatge d'error
     */
    hideError() {
        document.getElementById('error-message').style.display = 'none';
    }

    /**
     * Configura els event listeners per als filtres
     */
    setupFilters(onFilterChange) {
        const statusFilter = document.getElementById('status-filter');
        const searchInput = document.getElementById('search-input');
        const refreshBtn = document.getElementById('refresh-btn');

        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.currentFilters.status = e.target.value;
                onFilterChange(this.currentFilters);
            });
        }

        if (searchInput) {
            // Afegir debounce per la cerca
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.currentFilters.search = e.target.value;
                    onFilterChange(this.currentFilters);
                }, 300);
            });
        }

        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                // Recarregar les dades
                window.location.reload();
            });
        }
    }

    /**
     * Configura els event listeners per al modal
     */
    setupModal() {
        const modal = document.getElementById('alert-modal');
        const closeBtn = document.getElementById('close-modal');

        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.hideAlertDetail();
            });
        }

        // Tancar modal amb ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.classList.contains('show')) {
                this.hideAlertDetail();
            }
        });
    }

    /**
     * Escapa caràcters HTML per seguretat
     */
    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Neteja tots els filtres
     */
    clearFilters() {
        this.currentFilters = {
            status: '',
            search: ''
        };

        const statusFilter = document.getElementById('status-filter');
        const searchInput = document.getElementById('search-input');

        if (statusFilter) statusFilter.value = '';
        if (searchInput) searchInput.value = '';
    }

    /**
     * Ordena les alertes per data d'inici més propera a l'actual
     */
    _sortAlertsByStartDate(alerts) {
        const currentDate = new Date();
        
        return [...alerts].sort((a, b) => {
            // Convertir les dates d'inici a objectes Date
            const dateA = a.active_start ? new Date(a.active_start) : null;
            const dateB = b.active_start ? new Date(b.active_start) : null;
            
            // Si alguna data és null, posar-la al final
            if (!dateA && !dateB) return 0;
            if (!dateA) return 1;
            if (!dateB) return -1;
            
            // Calcular la diferència absoluta amb la data actual
            const diffA = Math.abs(currentDate - dateA);
            const diffB = Math.abs(currentDate - dateB);
            
            // Ordenar per diferència més petita (més propera a l'actual)
            return diffA - diffB;
        });
    }
}

// Crear una instància global dels components UI
const uiComponents = new UIComponents();