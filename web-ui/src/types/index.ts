// Cluster types
export interface Cluster {
  name: string;
  url: string;
  username: string;
  verify_ssl: boolean;
  status: 'active' | 'inactive' | 'error';
  created_at: string;
  updated_at: string;
}

export interface CreateClusterRequest {
  name: string;
  url: string;
  username: string;
  password: string;
  verify_ssl: boolean;
}

// Security types
export interface SecurityConfig {
  edit_mode_enabled: boolean;
  allowed_operations: string[];
  audit_logging?: boolean;
}

// Audit log types
export interface AuditLog {
  id: number;
  cluster_id?: number;
  cluster_name?: string;
  cluster_url?: string;
  user_id?: string;
  operation_id?: string;
  http_method: string;
  path?: string;
  request_body?: any;
  response_status?: number;
  response_body?: any;
  error_message?: string;
  timestamp: string;
  client_ip?: string;
}

export interface AuditStats {
  total: number;
  successful: number;
  failed: number;
  by_method: Record<string, number>;
  by_status: Record<string, number>;
}

// API types
export interface APIDefinition {
  name: string;
  display_name: string;
  base_path: string;
  description: string;
  enabled: boolean;
  operations_count?: number;
}

export interface APIHealth {
  name: string;
  status: 'healthy' | 'unhealthy' | 'unknown';
  last_check: string;
  response_time_ms?: number;
}

// System types
export interface ServiceStatus {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  message?: string;
  response_time_ms?: number;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  database: boolean;
  uptime_seconds: number;
  services: ServiceStatus[];
  timestamp: string;
}

export interface SystemStats {
  total_operations: number;
  clusters_configured: number;
  audit_logs_count: number;
  edit_mode_enabled: boolean;
}

// ==================== User & Authentication Types ====================

export interface User {
  id: number;
  username: string;
  email?: string;
  display_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  auth_type: 'local' | 'ldap';
  last_login?: string;
  created_at: string;
  updated_at: string;
  roles: Role[];
  has_edit_mode: boolean;
  api_token?: string;  // Only returned for current user
}

export interface CreateUserRequest {
  username: string;
  password: string;
  email?: string;
  display_name?: string;
  is_superuser?: boolean;
  role_ids?: number[];
}

export interface UpdateUserRequest {
  email?: string;
  display_name?: string;
  is_active?: boolean;
  is_superuser?: boolean;
  password?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: User;
}

export interface AuthMeResponse {
  authenticated: boolean;
  setup_required: boolean;
  message?: string;
  user?: User;
}

export interface SetupResponse {
  message: string;
  token: string;
  user: User;
}

// ==================== Role Types ====================

export interface Role {
  id: number;
  name: string;
  description?: string;
  edit_mode_enabled: boolean;
  is_system_role: boolean;
  operations_count: number;
  operations?: string[];
  created_at: string;
  updated_at: string;
}

export interface CreateRoleRequest {
  name: string;
  description?: string;
  edit_mode_enabled?: boolean;
  operations?: string[];
}

export interface UpdateRoleRequest {
  name?: string;
  description?: string;
  edit_mode_enabled?: boolean;
}

// ==================== Operation Types (for searchable dropdown) ====================

export interface Operation {
  name: string;
  method: string;
  path: string;
  api_name: string;
  description: string;
}

export interface OperationsListResponse {
  total: number;
  operations: Operation[];
}

export interface OperationsGrouped {
  [apiName: string]: Operation[];
}

export interface ApiNamesResponse {
  api_names: string[];
}

// ==================== Helper Types ====================

export interface AssignRolesRequest {
  role_ids: number[];
}

export interface SetRoleOperationsRequest {
  operations: string[];
}

export interface RegenerateTokenResponse {
  api_token: string;
}
