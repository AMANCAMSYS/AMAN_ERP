// Simple event emitter for toast notifications
// This allows non-React code (like api.js) to trigger toasts

class ToastEventEmitter {
    constructor() {
        this.listeners = [];
    }

    subscribe(callback) {
        this.listeners.push(callback);
        return () => {
            this.listeners = this.listeners.filter(l => l !== callback);
        };
    }

    emit(message, type = 'info') {
        this.listeners.forEach(callback => callback(message, type));
    }
}

export const toastEmitter = new ToastEventEmitter();
