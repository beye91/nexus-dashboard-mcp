// Cluster types
export interface Cluster {
  id?: number;
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
  clusters: { id: number; name: string }[];
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

// ==================== LDAP Types ====================

export interface LDAPConfig {
  id: number;
  name: string;
  is_enabled: boolean;
  is_primary: boolean;
  server_url: string;
  base_dn: string;
  bind_dn?: string;
  use_ssl: boolean;
  use_starttls: boolean;
  verify_ssl: boolean;
  has_ca_certificate: boolean;
  user_search_base?: string;
  user_search_filter: string;
  username_attribute: string;
  email_attribute: string;
  display_name_attribute: string;
  member_of_attribute: string;
  group_search_base?: string;
  group_search_filter: string;
  group_name_attribute: string;
  group_member_attribute: string;
  sync_interval_minutes: number;
  auto_create_users: boolean;
  auto_sync_groups: boolean;
  default_role_id?: number;
  last_sync_at?: string;
  last_sync_status?: 'success' | 'partial' | 'failed';
  last_sync_message?: string;
  last_sync_users_created: number;
  last_sync_users_updated: number;
  created_at: string;
  updated_at: string;
}

export interface LDAPConfigCreate {
  name: string;
  server_url: string;
  base_dn: string;
  bind_dn?: string;
  bind_password?: string;
  use_ssl?: boolean;
  use_starttls?: boolean;
  verify_ssl?: boolean;
  user_search_base?: string;
  user_search_filter?: string;
  username_attribute?: string;
  email_attribute?: string;
  display_name_attribute?: string;
  member_of_attribute?: string;
  group_search_base?: string;
  group_search_filter?: string;
  group_name_attribute?: string;
  group_member_attribute?: string;
  sync_interval_minutes?: number;
  auto_create_users?: boolean;
  auto_sync_groups?: boolean;
  default_role_id?: number;
}

export interface LDAPGroup {
  dn: string;
  name: string;
  description?: string;
}

export interface LDAPRoleMapping {
  id: number;
  ldap_config_id: number;
  ldap_group_dn: string;
  ldap_group_name: string;
  role_id: number;
  role_name?: string;
  created_at: string;
}

export interface LDAPClusterMapping {
  id: number;
  ldap_config_id: number;
  ldap_group_dn: string;
  ldap_group_name: string;
  cluster_id: number;
  cluster_name?: string;
  created_at: string;
}

export interface LDAPTestResult {
  success: boolean;
  error?: string;
  error_type?: string;
  server_info?: {
    vendor: string;
    version: string;
    naming_contexts: string[];
  };
  users_found?: number;
  message?: string;
}

export interface LDAPSyncResult {
  success: boolean;
  created?: number;
  updated?: number;
  errors?: string[];
  total_errors?: number;
  error?: string;
}

export interface AssignClustersRequest {
  cluster_ids: number[];
}

// ==================== API Guidance Types ====================

export interface APIGuidance {
  id: number;
  api_name: string;
  display_name: string;
  description: string | null;
  when_to_use: string | null;
  when_not_to_use: string | null;
  examples: any[];
  priority: number;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface CategoryGuidance {
  id: number;
  api_name: string;
  category_name: string;
  display_name: string | null;
  description: string | null;
  when_to_use: string | null;
  related_categories: string[];
  priority: number;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface WorkflowStep {
  id: number;
  workflow_id: number;
  step_order: number;
  operation_name: string;
  description: string | null;
  expected_output: string | null;
  optional: boolean;
  fallback_operation: string | null;
  created_at: string | null;
}

export interface Workflow {
  id: number;
  name: string;
  display_name: string;
  description: string | null;
  problem_statement: string | null;
  use_case_tags: string[];
  is_active: boolean;
  priority: number;
  steps_count: number;
  steps?: WorkflowStep[];
  created_at: string | null;
  updated_at: string | null;
}

export interface ToolDescriptionOverride {
  id: number;
  operation_name: string;
  enhanced_description: string | null;
  usage_hint: string | null;
  related_tools: string[];
  common_parameters: any[];
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface SystemPromptSection {
  id: number;
  section_name: string;
  section_order: number;
  title: string | null;
  content: string;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

// ==================== Resource Group Types (Tool Consolidation) ====================

export interface ResourceGroupOperation {
  id: number;
  group_id: number;
  operation_id: string;
  api_name: string;
  created_at: string;
}

export interface ResourceGroup {
  id: number;
  group_key: string;
  display_name: string | null;
  description: string | null;
  is_enabled: boolean;
  is_custom: boolean;
  sort_order: number;
  operations_count: number;
  operations: ResourceGroupOperation[];
  created_at: string;
  updated_at: string;
}

export interface ResourceGroupCreate {
  group_key: string;
  display_name?: string;
  description?: string;
  is_enabled?: boolean;
  sort_order?: number;
}

export interface ResourceGroupUpdate {
  display_name?: string;
  description?: string;
  is_enabled?: boolean;
  sort_order?: number;
}

export interface ResourceGroupStats {
  total_groups: number;
  enabled_groups: number;
  custom_groups: number;
  auto_generated_groups: number;
  mapped_operations: number;
  total_operations: number;
  unmapped_operations: number;
}

export interface UnmappedOperationsResponse {
  total: number;
  operations: {
    operation_id: string;
    api_name: string;
    http_method: string;
    path: string;
    description: string | null;
  }[];
}
