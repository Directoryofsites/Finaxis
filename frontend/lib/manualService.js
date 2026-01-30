/**
 * Servicio para gestión de manuales de usuario
 */
class ManualService {
    constructor() {
        this.basePath = '/Manual/ph/';
        this.cache = new Map();
    }

    /**
     * Abre un manual en una nueva ventana
     * @param {string} manualPath - Ruta relativa al manual
     * @param {string} title - Título del manual para la ventana
     */
    openManual(manualPath, title = 'Manual de Usuario') {
        if (!manualPath) {
            console.error('ManualService: Ruta del manual no especificada');
            this.showError('Manual no disponible');
            return;
        }

        const fullPath = this.getFullPath(manualPath);
        
        // Verificar si el manual existe antes de abrir
        this.checkManualExists(fullPath)
            .then(exists => {
                if (exists) {
                    this.openWindow(fullPath, title);
                } else {
                    this.showError('Manual no encontrado');
                }
            })
            .catch(() => {
                // Si falla la verificación, intentar abrir de todas formas
                this.openWindow(fullPath, title);
            });
    }

    /**
     * Obtiene el contenido de un manual
     * @param {string} manualPath - Ruta al manual
     * @returns {Promise<string>} Contenido HTML del manual
     */
    async getManualContent(manualPath) {
        const fullPath = this.getFullPath(manualPath);
        
        // Verificar caché
        if (this.cache.has(fullPath)) {
            return this.cache.get(fullPath);
        }

        try {
            const response = await fetch(fullPath);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const content = await response.text();
            
            // Guardar en caché
            this.cache.set(fullPath, content);
            
            return content;
        } catch (error) {
            console.error('Error cargando manual:', error);
            throw new Error('No se pudo cargar el manual');
        }
    }

    /**
     * Verifica si un manual existe
     * @param {string} manualPath - Ruta al manual
     * @returns {Promise<boolean>} True si el manual existe
     */
    async checkManualExists(manualPath) {
        try {
            const fullPath = this.getFullPath(manualPath);
            const response = await fetch(fullPath, { method: 'HEAD' });
            return response.ok;
        } catch (error) {
            console.warn('Error verificando existencia del manual:', error);
            return false;
        }
    }

    /**
     * Abre el manual en una nueva ventana
     * @param {string} fullPath - Ruta completa al manual
     * @param {string} title - Título de la ventana
     */
    openWindow(fullPath, title) {
        const windowFeatures = 'width=1200,height=800,scrollbars=yes,resizable=yes,menubar=yes,toolbar=yes';
        
        const manualWindow = window.open(fullPath, '_blank', windowFeatures);
        
        if (!manualWindow) {
            // Fallback si el popup fue bloqueado
            console.warn('Popup bloqueado, redirigiendo en la misma ventana');
            window.location.href = fullPath;
        } else {
            // Configurar título de la ventana
            manualWindow.document.title = title;
        }
    }

    /**
     * Construye la ruta completa al manual
     * @param {string} manualPath - Ruta relativa
     * @returns {string} Ruta completa
     */
    getFullPath(manualPath) {
        if (manualPath.startsWith('http') || manualPath.startsWith('/')) {
            return manualPath;
        }
        
        return `${this.basePath}${manualPath}`;
    }

    /**
     * Muestra un mensaje de error al usuario
     * @param {string} message - Mensaje de error
     */
    showError(message) {
        // Crear notificación temporal
        const notification = document.createElement('div');
        notification.innerHTML = `
            <div style="
                position: fixed;
                top: 20px;
                right: 20px;
                background: #ef4444;
                color: white;
                padding: 1rem 1.5rem;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 9999;
                font-family: system-ui, -apple-system, sans-serif;
                font-size: 14px;
                max-width: 300px;
                animation: slideIn 0.3s ease-out;
            ">
                <strong>⚠️ Error:</strong> ${message}
            </div>
        `;

        document.body.appendChild(notification);

        // Remover después de 4 segundos
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 4000);

        // Agregar estilos de animación si no existen
        if (!document.querySelector('#manual-notification-styles')) {
            const style = document.createElement('style');
            style.id = 'manual-notification-styles';
            style.textContent = `
                @keyframes slideIn {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }

    /**
     * Limpia la caché de manuales
     */
    clearCache() {
        this.cache.clear();
    }

    /**
     * Obtiene estadísticas de la caché
     * @returns {Object} Estadísticas de caché
     */
    getCacheStats() {
        return {
            size: this.cache.size,
            keys: Array.from(this.cache.keys())
        };
    }
}

// Crear instancia singleton
const manualService = new ManualService();

export default manualService;