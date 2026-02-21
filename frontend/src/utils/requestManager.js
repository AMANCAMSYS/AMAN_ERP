/**
 * RequestManager — tracks active API requests and aborts them on page navigation.
 * Works with the axios interceptors in api.js to automatically attach AbortControllers.
 */
class RequestManager {
    constructor() {
        /** @type {Set<AbortController>} */
        this.controllers = new Set()
    }

    /** Create & track a new AbortController */
    createController() {
        const controller = new AbortController()
        this.controllers.add(controller)
        return controller
    }

    /** Remove a controller after its request completes */
    removeController(controller) {
        this.controllers.delete(controller)
    }

    /** Abort all pending requests (called on route change) */
    abortAll() {
        for (const controller of this.controllers) {
            controller.abort()
        }
        this.controllers.clear()
    }

    /** Number of in-flight requests */
    get pendingCount() {
        return this.controllers.size
    }
}

export const requestManager = new RequestManager()
