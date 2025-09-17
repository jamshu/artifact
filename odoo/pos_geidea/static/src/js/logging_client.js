odoo.define('pos_geidea.logging_client', function(require) {
    'use strict';

    const { _t } = require('web.core');

    /**
     * POS Geidea Logging Client
     * Sends console logs and debugging data to local logging server
     */
    class GeideaLoggingClient {
        constructor() {
            // Store original console methods to prevent recursion
            this.originalConsole = {
                log: console.log.bind(console),
                info: console.info.bind(console),
                warn: console.warn.bind(console),
                error: console.error.bind(console)
            };
            
            this.serverUrl = 'http://localhost:8000';
            this.sessionId = this._generateSessionId();
            this.logQueue = [];
            this.batchSize = 10;
            this.flushInterval = 5000; // 5 seconds
            this.isOnline = true;
            
            // Configuration options
            this.captureUnhandledPromises = false; // Disabled by default to prevent recursion issues
            
            // Start background processes
            this._startBatchProcessor();
            this._detectOnlineStatus();
            this._initializeSession();
            
            this.originalConsole.log('🔄 Geidea Logging Client initialized:', this.sessionId);
            // Use _queueLog directly to avoid triggering console override during initialization
            this._queueLog('logging_client', 'INFO', 'Geidea Logging Client initialized', {
                session_id: this.sessionId,
                server_url: this.serverUrl
            });
        }

        /**
         * Generate unique session ID
         */
        _generateSessionId() {
            const timestamp = Date.now();
            const random = Math.random().toString(36).substring(2, 15);
            return `pos_${timestamp}_${random}`;
        }

        /**
         * Get current order info for context
         */
        _getCurrentOrderContext() {
            try {
                if (this.env.pos && this.env.pos) {
                    const order = this.env.pos.get_order();
                    return {
                        order_id: order ? order.uid : null,
                        order_total: order ? (typeof order.get_total_with_tax === 'function' ? order.get_total_with_tax() : null) : null,
                        payment_lines_count: order && order.paymentlines ? order.paymentlines.length : 0
                    };
                }
            } catch (e) {
                // Ignore errors when POS is not available
                return { error: 'Failed to get order context' };
            }
            return {};
        }

        /**
         * Get current user info
         */
        _getCurrentUserContext() {
            try {
                if (this.env.pos && this.env.pos) {
                    return {
                        user_id: this.env.pos.user.id ? window.pos.user.id.toString() : null,
                        user_name: this.env.pos.user.name || 'unknown'
                    };
                }
                if (this.env.session && this.env.session.user_context) {
                    return {
                        user_id: this.env.session.uid ? this.env.session.uid.toString() : null,
                        user_name: this.env.session.user_context.lang || 'unknown'
                    };
                }
            } catch (e) {
                // Ignore errors when session is not available
                return { error: 'Failed to get user context' };
            }
            return {};
        }

        /**
         * Initialize session info
         */
        async _initializeSession() {
            try {
                await this._sendLog({
                    component: 'session',
                    level: 'INFO',
                    message: 'POS session started',
                    data: {
                        ...this._getCurrentUserContext(),
                        browser: {
                            user_agent: navigator.userAgent,
                            language: navigator.language,
                            platform: navigator.platform,
                            cookies_enabled: navigator.cookieEnabled,
                            online: navigator.onLine
                        },
                        screen: {
                            width: screen.width,
                            height: screen.height,
                            color_depth: screen.colorDepth
                        },
                        window: {
                            inner_width: window.innerWidth,
                            inner_height: window.innerHeight,
                            url: window.location.href
                        }
                    }
                });
            } catch (e) {
                if (this.originalConsole) {
                    this.originalConsole.warn('Failed to initialize logging session:', e);
                }
            }
        }

        /**
         * Detect online/offline status
         */
        _detectOnlineStatus() {
            window.addEventListener('online', () => {
                this.isOnline = true;
                if (this.originalConsole) {
                    this.originalConsole.log('🔄 Logging client: Back online, flushing queued logs');
                }
                this._flushQueue();
            });

            window.addEventListener('offline', () => {
                this.isOnline = false;
                if (this.originalConsole) {
                    this.originalConsole.log('🔄 Logging client: Offline, queuing logs');
                }
            });
        }

        /**
         * Start batch processor to send logs periodically
         */
        _startBatchProcessor() {
            setInterval(() => {
                if (this.logQueue.length > 0 && this.isOnline) {
                    this._flushQueue();
                }
            }, this.flushInterval);
        }

        /**
         * Safe JSON serialization to handle circular references
         */
        _safeStringify(obj, maxDepth = 3, currentDepth = 0) {
            try {
                if (currentDepth > maxDepth) {
                    return '[Object too deep]';
                }
                
                if (obj === null || obj === undefined) {
                    return obj;
                }
                
                if (typeof obj === 'string' || typeof obj === 'number' || typeof obj === 'boolean') {
                    return obj;
                }
                
                if (obj instanceof Date) {
                    return obj.toISOString();
                }
                
                if (Array.isArray(obj)) {
                    return obj.slice(0, 10).map(item => this._safeStringify(item, maxDepth, currentDepth + 1));
                }
                
                if (typeof obj === 'object') {
                    const result = {};
                    const keys = Object.keys(obj).slice(0, 20); // Limit number of keys
                    
                    for (const key of keys) {
                        try {
                            // Skip circular references and functions
                            if (typeof obj[key] === 'function') {
                                result[key] = '[Function]';
                            } else if (obj[key] && typeof obj[key] === 'object') {
                                // Check for potential circular references
                                if (key.includes('parent') || key.includes('owner') || 
                                    key.includes('pos') || key.includes('order') || 
                                    key.includes('_') || key.includes('$')) {
                                    result[key] = '[Circular Reference Avoided]';
                                } else {
                                    result[key] = this._safeStringify(obj[key], maxDepth, currentDepth + 1);
                                }
                            } else {
                                result[key] = obj[key];
                            }
                        } catch (e) {
                            result[key] = '[Serialization Error]';
                        }
                    }
                    
                    return result;
                }
                
                return String(obj);
            } catch (error) {
                return '[Serialization Failed]';
            }
        }
        
        /**
         * Safe data sanitization for logging
         */
        _sanitizeData(data) {
            if (!data) {
                return null;
            }
            
            try {
                // Use safe stringify to handle circular references
                return this._safeStringify(data);
            } catch (error) {
                return { error: 'Data serialization failed', type: typeof data };
            }
        }

        /**
         * Create log entry object
         */
        _createLogEntry(component, level, message, data = null) {
            const userContext = this._getCurrentUserContext();
            const orderContext = this._getCurrentOrderContext();
            
            return {
                session_id: this.sessionId,
                order_id: orderContext.order_id,
                user_id: userContext.user_id,
                component: component,
                level: level.toUpperCase(),
                message: message,
                data: this._sanitizeData(data ? { ...data, ...orderContext } : orderContext),
                timestamp: new Date().toISOString(),
                url: window.location.href,
                user_agent: navigator.userAgent
            };
        }

        /**
         * Add log to queue
         */
        _queueLog(component, level, message, data = null) {
            const logEntry = this._createLogEntry(component, level, message, data);
            this.logQueue.push(logEntry);

            // If queue is full or this is an error, flush immediately
            if (this.logQueue.length >= this.batchSize || level.toUpperCase() === 'ERROR') {
                this._flushQueue();
            }
        }

        /**
         * Send log immediately (bypass queue)
         */
        async _sendLog(logData) {
            if (!this.isOnline) {
                this._queueLog(logData.component, logData.level, logData.message, logData.data);
                return;
            }

            try {
                const logEntry = this._createLogEntry(
                    logData.component, 
                    logData.level, 
                    logData.message, 
                    logData.data
                );

                // Use safe JSON stringify to prevent circular reference errors
                const jsonData = this._safeJSONStringify(logEntry);

                const response = await fetch(`${this.serverUrl}/api/logs`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: jsonData
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

            } catch (error) {
                if (this.originalConsole) {
                    this.originalConsole.warn('Failed to send log to server:', error);
                }
                // Store in queue for retry
                this._queueLog(logData.component, logData.level, logData.message, logData.data);
            }
        }

        /**
         * Safe JSON stringify with circular reference handling
         */
        _safeJSONStringify(obj) {
            try {
                // Use a Set to track visited objects and prevent circular references
                const seen = new Set();
                
                return JSON.stringify(obj, function(key, value) {
                    try {
                        // Handle circular references
                        if (typeof value === 'object' && value !== null) {
                            if (seen.has(value)) {
                                return '[Circular Reference]';
                            }
                            seen.add(value);
                        }
                        
                        // Handle functions
                        if (typeof value === 'function') {
                            return '[Function]';
                        }
                        
                        // Handle undefined
                        if (value === undefined) {
                            return '[Undefined]';
                        }
                        
                        // Skip problematic keys that are likely to cause circular references
                        if (typeof key === 'string' && (
                            key.startsWith('_') || 
                            key.startsWith('$') ||
                            key.includes('dispatcher') ||
                            key.includes('callback') ||
                            key.includes('event') ||
                            key.includes('parent') ||
                            key.includes('owner') ||
                            key.includes('pos') ||
                            key.includes('order') ||
                            key.includes('Class') ||
                            key.includes('source') ||
                            key.includes('target') ||
                            key.toLowerCase().includes('circular')
                        )) {
                            return '[Skipped - Potential Circular Reference]';
                        }
                        
                        return value;
                    } catch (e) {
                        return '[Serialization Error]';
                    }
                });
            } catch (error) {
                return JSON.stringify({
                    error: 'JSON serialization failed',
                    message: error.message,
                    originalType: typeof obj
                });
            }
        }

        /**
         * Flush queued logs to server
         */
        async _flushQueue() {
            if (this.logQueue.length === 0 || !this.isOnline) {
                return;
            }

            const logsToSend = this.logQueue.splice(0, this.batchSize);
            
            try {
                // Use safe JSON stringify to prevent circular reference errors
                const jsonData = this._safeJSONStringify(logsToSend);
                
                const response = await fetch(`${this.serverUrl}/api/logs/batch`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: jsonData
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                if (this.originalConsole) {
                    this.originalConsole.log(`🔄 Sent ${logsToSend.length} logs to server`);
                }

            } catch (error) {
                if (this.originalConsole) {
                    this.originalConsole.warn('Failed to flush logs to server:', error);
                }
                // Put logs back in queue for retry
                this.logQueue.unshift(...logsToSend);
            }
        }

        // Public logging methods

        /**
         * Log debug message
         */
        logDebug(component, message, data = null) {
            // Use stored original console methods to prevent recursion
            if (this.originalConsole) {
                this.originalConsole.log(`[DEBUG] ${component}: ${message}`, data);
            }
            this._queueLog(component, 'DEBUG', message, data);
        }

        /**
         * Log info message
         */
        logInfo(component, message, data = null) {
            if (this.originalConsole) {
                this.originalConsole.info(`[INFO] ${component}: ${message}`, data);
            }
            this._queueLog(component, 'INFO', message, data);
        }

        /**
         * Log warning message
         */
        logWarning(component, message, data = null) {
            if (this.originalConsole) {
                this.originalConsole.warn(`[WARNING] ${component}: ${message}`, data);
            }
            this._queueLog(component, 'WARNING', message, data);
        }

        /**
         * Log error message
         */
        logError(component, message, data = null) {
            try {
                if (this.originalConsole && this.originalConsole.error) {
                    // Safely format the message
                    const safeMessage = message || 'Unknown error';
                    const safeComponent = component || 'unknown';
                    
                    // Only pass data if it's safe to log
                    if (data && typeof data === 'object') {
                        this.originalConsole.error(`[ERROR] ${safeComponent}: ${safeMessage}`, data);
                    } else {
                        this.originalConsole.error(`[ERROR] ${safeComponent}: ${safeMessage}`);
                    }
                }
            } catch (consoleError) {
                // If console logging fails, try basic console.error as last resort
                try {
                    console.error(`[ERROR] Logging failed: ${message}`);
                } catch (e) {
                    // Complete console failure - silently fail
                }
            }
            
            // Always try to queue the log
            try {
                this._queueLog(component, 'ERROR', message, data);
            } catch (queueError) {
                // If queue fails, at least we tried console logging above
            }
        }

        /**
         * Log payment event with detailed data
         */
        logPayment(action, status, data = {}) {
            const message = `Payment ${action}: ${status}`;
            const paymentData = {
                action: action,
                status: status,
                ...data
            };
            
            this.logInfo('payment', message, paymentData);
        }

        /**
         * Log terminal interaction
         */
        logTerminal(event, message, data = {}) {
            const terminalData = {
                event: event,
                ...data
            };
            
            this.logInfo('terminal', `Terminal ${event}: ${message}`, terminalData);
        }

        /**
         * Log navigation restriction
         */
        logRestriction(action, blocked, reason, data = {}) {
            const restrictionData = {
                action: action,
                blocked: blocked,
                reason: reason,
                ...data
            };
            
            const level = blocked ? 'WARNING' : 'INFO';
            const message = blocked ? `Blocked ${action}: ${reason}` : `Allowed ${action}`;
            
            this._queueLog('restriction', level, message, restrictionData);
        }

        /**
         * Log JavaScript errors
         */
        logJSError(error, context = {}) {
            try {
                // Safely extract error properties
                const errorName = (error && error.name) ? error.name : 'UnknownError';
                const errorMessage = (error && error.message) ? error.message : 'No error message';
                const errorStack = (error && error.stack) ? error.stack : 'No stack trace';
                
                const errorData = {
                    error_name: errorName,
                    error_message: errorMessage,
                    error_stack: errorStack,
                    context: context || {}
                };
                
                // Use safe message
                const logMessage = `JS Error: ${errorMessage}`;
                
                this.logError('javascript', logMessage, errorData);
            } catch (loggingError) {
                // If logging the JS error fails, try basic fallback
                try {
                    if (this.originalConsole && this.originalConsole.error) {
                        this.originalConsole.error('Failed to log JavaScript error:', error, loggingError);
                    }
                } catch (fallbackError) {
                    // Complete failure - silent
                }
            }
        }

        /**
         * Force flush all queued logs
         */
        async flush() {
            await this._flushQueue();
        }

        /**
         * Get current session info
         */
        getSessionInfo() {
            return {
                session_id: this.sessionId,
                queue_length: this.logQueue.length,
                is_online: this.isOnline,
                server_url: this.serverUrl,
                capture_unhandled_promises: this.captureUnhandledPromises
            };
        }
        
        /**
         * Enable/disable unhandled promise rejection monitoring
         */
        setPromiseMonitoring(enabled) {
            this.captureUnhandledPromises = enabled;
            if (this.originalConsole) {
                this.originalConsole.log(`🔄 Promise rejection monitoring ${enabled ? 'enabled' : 'disabled'}`);
            }
        }
    }

    // Store original console methods for overrides
    const originalConsoleLog = console.log;
    const originalConsoleInfo = console.info;
    const originalConsoleWarn = console.warn;
    const originalConsoleError = console.error;

    // Create global instance
    const loggingClient = new GeideaLoggingClient();

    // Track recursion to prevent infinite loops
    let isLoggingInProgress = false;
    
    // Override console methods with recursion prevention
    console.log = function(...args) {
        originalConsoleLog.apply(console, args);
        
        // Prevent recursion and only log Geidea-related console messages
        if (!isLoggingInProgress) {
            try {
                const message = args.join(' ');
                if (message.toLowerCase().includes('geidea')) {
                    isLoggingInProgress = true;
                    loggingClient.logDebug('console', message, { args: args });
                }
            } catch (e) {
                // Silently ignore logging errors to prevent recursion
            } finally {
                isLoggingInProgress = false;
            }
        }
    };

    console.info = function(...args) {
        originalConsoleInfo.apply(console, args);
        
        if (!isLoggingInProgress) {
            try {
                const message = args.join(' ');
                if (message.toLowerCase().includes('geidea')) {
                    isLoggingInProgress = true;
                    loggingClient.logInfo('console', message, { args: args });
                }
            } catch (e) {
                // Silently ignore logging errors
            } finally {
                isLoggingInProgress = false;
            }
        }
    };

    console.warn = function(...args) {
        originalConsoleWarn.apply(console, args);
        
        if (!isLoggingInProgress) {
            try {
                const message = args.join(' ');
                if (message.toLowerCase().includes('geidea')) {
                    isLoggingInProgress = true;
                    loggingClient.logWarning('console', message, { args: args });
                }
            } catch (e) {
                // Silently ignore logging errors
            } finally {
                isLoggingInProgress = false;
            }
        }
    };

    console.error = function(...args) {
        originalConsoleError.apply(console, args);
        
        if (!isLoggingInProgress) {
            try {
                const message = args.join(' ');
                if (message.toLowerCase().includes('geidea')) {
                    isLoggingInProgress = true;
                    loggingClient.logError('console', message, { args: args });
                }
            } catch (e) {
                // Silently ignore logging errors
            } finally {
                isLoggingInProgress = false;
            }
        }
    };

    // Capture unhandled errors
    window.addEventListener('error', (event) => {
        try {
            const error = event.error || new Error(event.message || 'Unknown error');
            loggingClient.logJSError(error, {
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
        } catch (e) {
            // Fallback: use original console to log if logging client fails
            originalConsoleError('Failed to log JS error:', e);
        }
    });

    // Conditionally capture unhandled promise rejections (disabled by default)
    if (loggingClient.captureUnhandledPromises) {
        window.addEventListener('unhandledrejection', (event) => {
            try {
                // Safely convert reason to Error object
                let error;
                if (event.reason instanceof Error) {
                    error = event.reason;
                } else if (typeof event.reason === 'string') {
                    error = new Error(event.reason);
                } else if (event.reason && event.reason.toString) {
                    error = new Error(event.reason.toString());
                } else {
                    error = new Error('Unknown promise rejection');
                }
                
                loggingClient.logJSError(error, {
                    type: 'unhandled_promise_rejection',
                    original_reason: event.reason
                });
            } catch (e) {
                // Fallback: use original console to log if logging client fails
                originalConsoleError('Failed to log promise rejection:', e, event.reason);
            }
        });
        originalConsoleLog('🔄 Unhandled promise rejection monitoring enabled');
    } else {
        originalConsoleLog('🔄 Unhandled promise rejection monitoring disabled (to prevent issues)');
    }

    // Expose to global scope
    window.geideaLogger = loggingClient;

    // Use original console method for this final log
    originalConsoleLog('🔄 Geidea Logging Client loaded and monitoring console');

    return loggingClient;
});