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
