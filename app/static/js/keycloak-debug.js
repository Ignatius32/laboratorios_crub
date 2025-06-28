/**
 * Keycloak Authentication Debug Module
 * Provides comprehensive browser console debugging for authentication flows
 */

class KeycloakDebugger {
    constructor() {
        this.isDebugEnabled = false;
        this.debugPrefix = '[KEYCLOAK-DEBUG]';
        this.init();
    }

    init() {
        // Check if debugging is enabled via meta tag or global variable
        const debugMeta = document.querySelector('meta[name="keycloak-debug"]');
        this.isDebugEnabled = debugMeta ? debugMeta.content === 'true' : false;
        
        if (this.isDebugEnabled) {
            console.log(`${this.debugPrefix} Debug mode enabled`);
            this.startDebugging();
        }
    }

    log(message, data = null) {
        if (!this.isDebugEnabled) return;
        
        if (data) {
            console.log(`${this.debugPrefix} ${message}`, data);
        } else {
            console.log(`${this.debugPrefix} ${message}`);
        }
    }

    error(message, error = null) {
        if (!this.isDebugEnabled) return;
        
        if (error) {
            console.error(`${this.debugPrefix} ${message}`, error);
        } else {
            console.error(`${this.debugPrefix} ${message}`);
        }
    }

    warn(message, data = null) {
        if (!this.isDebugEnabled) return;
        
        if (data) {
            console.warn(`${this.debugPrefix} ${message}`, data);
        } else {
            console.warn(`${this.debugPrefix} ${message}`);
        }
    }

    startDebugging() {
        this.log('Starting Keycloak authentication debugging...');
        
        // Debug current page info
        this.debugPageInfo();
        
        // Debug URL parameters
        this.debugUrlParameters();
        
        // Debug session storage
        this.debugSessionStorage();
        
        // Debug local storage
        this.debugLocalStorage();
        
        // Debug cookies
        this.debugCookies();
        
        // Monitor network requests
        this.monitorNetworkRequests();
        
        // Monitor form submissions
        this.monitorFormSubmissions();
        
        // Monitor Keycloak button clicks
        this.monitorKeycloakButtons();
        
        // Monitor page navigation
        this.monitorPageNavigation();
    }

    debugPageInfo() {
        this.log('Page Information:', {
            url: window.location.href,
            pathname: window.location.pathname,
            search: window.location.search,
            hash: window.location.hash,
            origin: window.location.origin,
            host: window.location.host,
            hostname: window.location.hostname,
            port: window.location.port,
            protocol: window.location.protocol,
            userAgent: navigator.userAgent,
            timestamp: new Date().toISOString()
        });
    }

    debugUrlParameters() {
        const urlParams = new URLSearchParams(window.location.search);
        const params = {};
        
        for (const [key, value] of urlParams) {
            params[key] = value;
        }
        
        this.log('URL Parameters:', params);
        
        // Check for specific Keycloak parameters
        const keycloakParams = ['code', 'state', 'error', 'error_description', 'session_state', 'iss'];
        const foundKeycloakParams = {};
        
        keycloakParams.forEach(param => {
            if (urlParams.has(param)) {
                foundKeycloakParams[param] = urlParams.get(param);
            }
        });
        
        if (Object.keys(foundKeycloakParams).length > 0) {
            this.log('Keycloak Callback Parameters:', foundKeycloakParams);
        }
        
        // Check for error parameters
        if (urlParams.has('error')) {
            this.error('Authentication Error in URL:', {
                error: urlParams.get('error'),
                error_description: urlParams.get('error_description')
            });
        }
    }

    debugSessionStorage() {
        try {
            const sessionData = {};
            for (let i = 0; i < sessionStorage.length; i++) {
                const key = sessionStorage.key(i);
                const value = sessionStorage.getItem(key);
                
                // Try to parse JSON values
                try {
                    sessionData[key] = JSON.parse(value);
                } catch (e) {
                    sessionData[key] = value;
                }
            }
            
            this.log('Session Storage:', sessionData);
        } catch (error) {
            this.error('Failed to read session storage:', error);
        }
    }

    debugLocalStorage() {
        try {
            const localData = {};
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                const value = localStorage.getItem(key);
                
                // Try to parse JSON values
                try {
                    localData[key] = JSON.parse(value);
                } catch (e) {
                    localData[key] = value;
                }
            }
            
            this.log('Local Storage:', localData);
        } catch (error) {
            this.error('Failed to read local storage:', error);
        }
    }

    debugCookies() {
        try {
            const cookies = {};
            document.cookie.split(';').forEach(cookie => {
                const [name, value] = cookie.trim().split('=');
                if (name && value) {
                    cookies[name] = decodeURIComponent(value);
                }
            });
            
            this.log('Cookies:', cookies);
        } catch (error) {
            this.error('Failed to read cookies:', error);
        }
    }

    monitorNetworkRequests() {
        // Override fetch to monitor requests
        const originalFetch = window.fetch;
        window.fetch = (...args) => {
            const [url, options] = args;
            
            this.log('Fetch Request:', {
                url: url,
                method: options?.method || 'GET',
                headers: options?.headers,
                body: options?.body,
                timestamp: new Date().toISOString()
            });
            
            return originalFetch(...args)
                .then(response => {
                    this.log('Fetch Response:', {
                        url: url,
                        status: response.status,
                        statusText: response.statusText,
                        headers: Object.fromEntries(response.headers.entries()),
                        timestamp: new Date().toISOString()
                    });
                    return response;
                })
                .catch(error => {
                    this.error('Fetch Error:', {
                        url: url,
                        error: error.message,
                        timestamp: new Date().toISOString()
                    });
                    throw error;
                });
        };

        // Monitor XMLHttpRequest
        const originalXHROpen = XMLHttpRequest.prototype.open;
        const originalXHRSend = XMLHttpRequest.prototype.send;
        
        XMLHttpRequest.prototype.open = function(method, url, ...args) {
            this._debugUrl = url;
            this._debugMethod = method;
            this._debugStartTime = Date.now();
            
            return originalXHROpen.apply(this, [method, url, ...args]);
        };
        
        XMLHttpRequest.prototype.send = function(body) {
            this.addEventListener('loadend', () => {
                window.keycloakDebugger.log('XHR Request Complete:', {
                    url: this._debugUrl,
                    method: this._debugMethod,
                    status: this.status,
                    statusText: this.statusText,
                    responseType: this.responseType,
                    duration: Date.now() - this._debugStartTime,
                    timestamp: new Date().toISOString()
                });
            });
            
            window.keycloakDebugger.log('XHR Request:', {
                url: this._debugUrl,
                method: this._debugMethod,
                body: body,
                timestamp: new Date().toISOString()
            });
            
            return originalXHRSend.apply(this, [body]);
        };
    }

    monitorFormSubmissions() {
        document.addEventListener('submit', (event) => {
            const form = event.target;
            const formData = new FormData(form);
            const data = {};
            
            for (const [key, value] of formData) {
                data[key] = value;
            }
            
            this.log('Form Submission:', {
                action: form.action,
                method: form.method,
                data: data,
                timestamp: new Date().toISOString()
            });
        });
    }

    monitorKeycloakButtons() {
        // Monitor clicks on Keycloak-related buttons and links
        document.addEventListener('click', (event) => {
            const target = event.target;
            const href = target.href || target.closest('a')?.href;
            
            // Check if this is a Keycloak-related link
            if (href && (
                href.includes('keycloak-login') ||
                href.includes('auth/callback') ||
                href.includes('keycloak-logout') ||
                href.includes('logout')
            )) {
                this.log('Keycloak Action Click:', {
                    element: target.tagName,
                    text: target.textContent?.trim(),
                    href: href,
                    className: target.className,
                    id: target.id,
                    timestamp: new Date().toISOString()
                });
            }
        });
    }

    monitorPageNavigation() {
        // Monitor page navigation events
        window.addEventListener('beforeunload', () => {
            this.log('Page Unload:', {
                url: window.location.href,
                timestamp: new Date().toISOString()
            });
        });
        
        window.addEventListener('popstate', (event) => {
            this.log('Popstate Event:', {
                state: event.state,
                url: window.location.href,
                timestamp: new Date().toISOString()
            });
        });
        
        // Monitor hash changes
        window.addEventListener('hashchange', (event) => {
            this.log('Hash Change:', {
                oldURL: event.oldURL,
                newURL: event.newURL,
                timestamp: new Date().toISOString()
            });
        });
    }

    // Helper method to manually log authentication events
    logAuthEvent(eventType, data) {
        this.log(`Auth Event: ${eventType}`, {
            ...data,
            timestamp: new Date().toISOString()
        });
    }

    // Helper method to manually log authentication errors
    logAuthError(errorType, error, context = {}) {
        this.error(`Auth Error: ${errorType}`, {
            error: error.message || error,
            stack: error.stack,
            context: context,
            timestamp: new Date().toISOString()
        });
    }

    // Helper method to export debug data
    exportDebugData() {
        const debugData = {
            timestamp: new Date().toISOString(),
            pageInfo: {
                url: window.location.href,
                userAgent: navigator.userAgent,
                referrer: document.referrer
            },
            urlParams: Object.fromEntries(new URLSearchParams(window.location.search)),
            sessionStorage: Object.fromEntries(
                Object.keys(sessionStorage).map(key => [key, sessionStorage.getItem(key)])
            ),
            localStorage: Object.fromEntries(
                Object.keys(localStorage).map(key => [key, localStorage.getItem(key)])
            ),
            cookies: Object.fromEntries(
                document.cookie.split(';').map(cookie => {
                    const [name, value] = cookie.trim().split('=');
                    return [name, decodeURIComponent(value || '')];
                }).filter(([name]) => name)
            )
        };
        
        console.log(`${this.debugPrefix} Debug Data Export:`, debugData);
        return debugData;
    }
}

// Initialize the debugger when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.keycloakDebugger = new KeycloakDebugger();
});

// Export for manual use
window.KeycloakDebugger = KeycloakDebugger;
