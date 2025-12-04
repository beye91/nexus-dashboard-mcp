import axios from 'axios';
import type {
  User,
  Role,
  Cluster,
  LoginRequest,
  LoginResponse,
  AuthMeResponse,
  SetupResponse,
  CreateUserRequest,
  UpdateUserRequest,
  CreateRoleRequest,
  UpdateRoleRequest,
  AssignRolesRequest,
  AssignClustersRequest,
  SetRoleOperationsRequest,
  OperationsListResponse,
  OperationsGrouped,
  ApiNamesResponse,
  RegenerateTokenResponse,
  LDAPConfig,
  LDAPConfigCreate,
  LDAPGroup,
  LDAPRoleMapping,
  LDAPClusterMapping,
  LDAPTestResult,
  LDAPSyncResult,
} from '@/types';

// Use relative URLs - Next.js rewrites will proxy to the backend
// This works for both local and remote deployments
const API_BASE_URL = '';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
  withCredentials: true,  // Include cookies for session auth
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Session token is sent via cookie automatically with withCredentials
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

  // Authentication
  auth: {
    login: (data: LoginRequest) =>
      apiClient.post<LoginResponse>('/api/auth/login', data),
    logout: () =>
      apiClient.post('/api/auth/logout'),
    me: () =>
      apiClient.get<AuthMeResponse>('/api/auth/me'),
    setup: (data: CreateUserRequest) =>
      apiClient.post<SetupResponse>('/api/auth/setup', data),
  },

  // Users
  users: {
    list: (activeOnly?: boolean) =>
      apiClient.get<User[]>('/api/users', { params: { active_only: activeOnly } }),
    get: (id: number) =>
      apiClient.get<User>(`/api/users/${id}`),
    create: (data: CreateUserRequest) =>
      apiClient.post<User>('/api/users', data),
    update: (id: number, data: UpdateUserRequest) =>
      apiClient.put<User>(`/api/users/${id}`, data),
    delete: (id: number) =>
      apiClient.delete(`/api/users/${id}`),
    assignRoles: (id: number, data: AssignRolesRequest) =>
      apiClient.put<User>(`/api/users/${id}/roles`, data),
    assignClusters: (id: number, data: AssignClustersRequest) =>
      apiClient.put<User>(`/api/users/${id}/clusters`, data),
    getClusters: (id: number) =>
      apiClient.get<Cluster[]>(`/api/users/${id}/clusters`),
    regenerateToken: (id: number) =>
      apiClient.post<RegenerateTokenResponse>(`/api/users/${id}/regenerate-token`),
  },

  // Roles
  roles: {
    list: (includeSystem?: boolean) =>
      apiClient.get<Role[]>('/api/roles', { params: { include_system: includeSystem } }),
    get: (id: number) =>
      apiClient.get<Role>(`/api/roles/${id}`),
    create: (data: CreateRoleRequest) =>
      apiClient.post<Role>('/api/roles', data),
    update: (id: number, data: UpdateRoleRequest) =>
      apiClient.put<Role>(`/api/roles/${id}`, data),
    delete: (id: number) =>
      apiClient.delete(`/api/roles/${id}`),
    setOperations: (id: number, data: SetRoleOperationsRequest) =>
      apiClient.put<Role>(`/api/roles/${id}/operations`, data),
  },

  // Operations (for searchable dropdown)
  operations: {
    list: (params?: { search?: string; api_name?: string; limit?: number; offset?: number }) =>
      apiClient.get<OperationsListResponse>('/api/operations', { params }),
    grouped: () =>
      apiClient.get<OperationsGrouped>('/api/operations/grouped'),
    apiNames: () =>
      apiClient.get<ApiNamesResponse>('/api/operations/api-names'),
    count: () =>
      apiClient.get<{ total: number }>('/api/operations/count'),
  },

  // LDAP
  ldap: {
    listConfigs: () =>
      apiClient.get<LDAPConfig[]>('/api/ldap/configs'),
    getConfig: (id: number) =>
      apiClient.get<LDAPConfig>(`/api/ldap/configs/${id}`),
    createConfig: (data: LDAPConfigCreate) =>
      apiClient.post<LDAPConfig>('/api/ldap/configs', data),
    updateConfig: (id: number, data: Partial<LDAPConfigCreate>) =>
      apiClient.put<LDAPConfig>(`/api/ldap/configs/${id}`, data),
    deleteConfig: (id: number) =>
      apiClient.delete(`/api/ldap/configs/${id}`),
    testConnection: (id: number) =>
      apiClient.post<LDAPTestResult>(`/api/ldap/configs/${id}/test`),
    syncUsers: (id: number) =>
      apiClient.post<LDAPSyncResult>(`/api/ldap/configs/${id}/sync`),
    discoverGroups: (id: number) =>
      apiClient.get<LDAPGroup[]>(`/api/ldap/configs/${id}/groups`),

    // Role mappings
    listRoleMappings: (configId: number) =>
      apiClient.get<LDAPRoleMapping[]>(`/api/ldap/configs/${configId}/role-mappings`),
    createRoleMapping: (configId: number, data: { ldap_group_dn: string; ldap_group_name: string; role_id: number }) =>
      apiClient.post<LDAPRoleMapping>(`/api/ldap/configs/${configId}/role-mappings`, data),
    deleteRoleMapping: (configId: number, mappingId: number) =>
      apiClient.delete(`/api/ldap/configs/${configId}/role-mappings/${mappingId}`),

    // Cluster mappings
    listClusterMappings: (configId: number) =>
      apiClient.get<LDAPClusterMapping[]>(`/api/ldap/configs/${configId}/cluster-mappings`),
    createClusterMapping: (configId: number, data: { ldap_group_dn: string; ldap_group_name: string; cluster_id: number }) =>
      apiClient.post<LDAPClusterMapping>(`/api/ldap/configs/${configId}/cluster-mappings`, data),
    deleteClusterMapping: (configId: number, mappingId: number) =>
      apiClient.delete(`/api/ldap/configs/${configId}/cluster-mappings/${mappingId}`),
  },
};
