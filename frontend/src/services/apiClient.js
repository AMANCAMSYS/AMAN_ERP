/**
 * Shared Axios instance with interceptors.
 * All service files import `api` from here.
 */
import axios from 'axios'
import { toastEmitter } from '../utils/toastEmitter'
import { requestManager } from '../utils/requestManager'

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || '/api',
    headers: {
        'Content-Type': 'application/json'
    }
})

// Add auth token + AbortController to requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    // Auto-attach AbortController unless request already has a signal or opts out
    if (!config.signal && !config.skipAbort) {
        const controller = requestManager.createController()
        config.signal = controller.signal
        config._abortController = controller
    }
    return config
})

// Handle API responses — clean up AbortControllers + auto token refresh
api.interceptors.response.use(
    (response) => {
        // Clean up tracked controller on success
        if (response.config._abortController) {
            requestManager.removeController(response.config._abortController)
        }
        return response
    },
    async (error) => {
        // Clean up tracked controller on error
        if (error.config?._abortController) {
            requestManager.removeController(error.config._abortController)
        }
        // Silently ignore aborted/canceled requests (page navigation)
        if (axios.isCancel(error) || error.code === 'ERR_CANCELED') {
            return Promise.reject(error)
        }
        // Option to skip global toast for specific requests
        const skipToast = error.config?.skipGlobalToast;
        const originalRequest = error.config;

        // --- 429 Rate Limit: Retry with backoff ---
        if (error.response?.status === 429 && !originalRequest._retryCount) {
            originalRequest._retryCount = 1;
            const retryAfter = parseInt(error.response.headers['retry-after'], 10);
            const delay = (retryAfter && retryAfter > 0) ? retryAfter * 1000 : 2000;
            await new Promise(resolve => setTimeout(resolve, delay));
            return api(originalRequest);
        }

        // --- Auto Token Refresh ---
        if (error.response?.status === 401 && !originalRequest._isRetry) {
            originalRequest._isRetry = true;
            const currentRefreshToken = localStorage.getItem('refresh_token');

            if (currentRefreshToken) {
                try {
                    // Attempt to refresh access token using long-lived refresh token
                    const refreshRes = await axios.post(
                        `${api.defaults.baseURL}/auth/refresh`,
                        { refresh_token: currentRefreshToken }
                    );

                    const newToken = refreshRes.data?.access_token;
                    const newRefreshToken = refreshRes.data?.refresh_token;
                    if (newToken) {
                        localStorage.setItem('token', newToken);
                        if (newRefreshToken) {
                            localStorage.setItem('refresh_token', newRefreshToken);
                        }
                        originalRequest.headers.Authorization = `Bearer ${newToken}`;
                        return api(originalRequest); // retry original request
                    }
                } catch (refreshError) {
                    // Refresh failed — session truly expired
                }
            }

            // If we reach here, refresh failed or no token exists
            localStorage.removeItem('token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            localStorage.removeItem('company_id');
            window.location.href = '/login';
            return Promise.reject(error);
        }

        if (!skipToast && error.response) {
            const status = error.response.status;
            const detail = error.response.data?.detail;
            const lang = localStorage.getItem('i18nextLng') || 'ar';

            let message = '';
            let type = 'error';

            if (status === 403) {
                message = lang === 'ar'
                    ? 'ليس لديك صلاحية للقيام بهذا الإجراء'
                    : 'You do not have permission to perform this action';
                type = 'warning';
            } else if (status >= 400 && status < 500) {
                if (typeof detail === 'string') {
                    message = detail;
                } else if (Array.isArray(detail)) {
                    message = detail.map(d => d.msg).join(', ');
                } else {
                    message = lang === 'ar'
                        ? 'يرجى مراجعة البيانات المدخلة'
                        : 'Please check your input';
                }
            } else if (status >= 500) {
                message = lang === 'ar'
                    ? 'حدث خطأ في النظام، يرجى المحاولة لاحقاً'
                    : 'A system error occurred, please try again later';
            }

            if (message) {
                toastEmitter.emit(message, type);
            }
        }
        return Promise.reject(error);
    }
);

/**
 * Remove null/undefined/empty-string params before sending.
 */
export const cleanParams = (params) => {
    if (!params) return params;
    const cleaned = {};
    for (const [key, value] of Object.entries(params)) {
        if (value !== '' && value !== null && value !== undefined) {
            cleaned[key] = value;
        }
    }
    return cleaned;
};

export { api }
export default api
