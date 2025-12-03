import axios from 'axios';

// Use relative URLs - Next.js rewrites will proxy to the backend
// This works for both local and remote deployments
const API_BASE_URL = '';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add any auth tokens here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle errors globally
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// API endpoints
export const api = {
  // Clusters
  clusters: {
    list: () => apiClient.get('/api/clusters'),
    get: (name: string) => apiClient.get(`/api/clusters/${name}`),
    create: (data: any) => apiClient.post('/api/clusters', data),
    update: (name: string, data: any) => apiClient.put(`/api/clusters/${name}`, data),
    delete: (name: string) => apiClient.delete(`/api/clusters/${name}`),
    test: (data: any) => apiClient.post('/api/clusters/test', data),
  },

  // Security
  security: {
    getConfig: () => apiClient.get('/api/security/config'),
    updateConfig: (data: any) => apiClient.put('/api/security/config', data),
    getEditMode: () => apiClient.get('/api/security/edit-mode'),
    setEditMode: (enabled: boolean) => apiClient.put('/api/security/edit-mode', { enabled }),
  },

  // Audit Logs
  audit: {
    list: (params?: any) => apiClient.get('/api/audit', { params }),
    export: (params?: any) => apiClient.get('/api/audit/export', { params, responseType: 'blob' }),
    stats: () => apiClient.get('/api/audit/stats'),
  },

  // APIs
  apis: {
    list: () => apiClient.get('/api/apis'),
    get: (name: string) => apiClient.get(`/api/apis/${name}`),
    toggle: (name: string, enabled: boolean) => apiClient.put(`/api/apis/${name}/toggle`, { enabled }),
    health: () => apiClient.get('/api/apis/health'),
  },

  // System
  system: {
    health: () => apiClient.get('/api/health'),
    stats: () => apiClient.get('/api/stats'),
  },

  // Shortcuts
  health: {
    get: () => apiClient.get('/api/health'),
  },
  stats: {
    get: () => apiClient.get('/api/stats'),
  },
};
