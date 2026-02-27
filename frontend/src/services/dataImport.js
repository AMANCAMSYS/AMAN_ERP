import api from './apiClient'

export const dataImportAPI = {
    // Entity types available for import
    getEntityTypes: () => api.get('/data-import/entity-types'),

    // Download template for an entity type
    getTemplate: (entityType) => api.get(`/data-import/template/${entityType}`, { responseType: 'blob' }),

    // Preview import data before executing
    previewImport: (formData) => api.post('/data-import/preview', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }),

    // Execute import
    executeImport: (data) => api.post('/data-import/execute', data),

    // Import history
    getHistory: (params) => api.get('/data-import/history', { params }),

    // Export data
    exportData: (entityType, params) => api.get(`/data-import/export/${entityType}`, {
        params,
        responseType: 'blob'
    }),
}
