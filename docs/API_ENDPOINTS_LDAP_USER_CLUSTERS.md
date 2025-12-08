# API Endpoints - LDAP Configuration and User Cluster Assignment

This document describes the REST API endpoints for LDAP configuration and user cluster assignment added to the Nexus Dashboard MCP Server.

## Table of Contents

1. [User Cluster Assignment Endpoints](#user-cluster-assignment-endpoints)
2. [LDAP Configuration Endpoints](#ldap-configuration-endpoints)
3. [LDAP Group Mapping Endpoints](#ldap-group-mapping-endpoints)
4. [Request/Response Models](#requestresponse-models)

---

## User Cluster Assignment Endpoints

These endpoints manage which clusters a user can access. Users can manage their own cluster assignments, while superusers can manage any user's assignments.

### Assign Clusters to User

```
PUT /api/users/{user_id}/clusters
```

**Authentication:** Required (user themselves or superuser)

**Request Body:**
```json
{
  "cluster_ids": [1, 2, 3]
}
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "prod-cluster",
    "url": "https://nd1.example.com",
    "created_at": "2025-01-15T10:30:00"
  }
]
```

**Permissions:**
- Users can only assign clusters to their own account
- Superusers can assign clusters to any user

**Notes:**
- Replaces all existing cluster assignments
- Empty array removes all cluster access
- Superusers always have access to all clusters regardless of assignments

---

### Get User's Assigned Clusters

```
GET /api/users/{user_id}/clusters
```

**Authentication:** Required (user themselves or superuser)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "prod-cluster",
    "url": "https://nd1.example.com",
    "created_at": "2025-01-15T10:30:00"
  }
]
```

**Permissions:**
- Users can view their own cluster assignments
- Superusers can view any user's assignments

---

## LDAP Configuration Endpoints

These endpoints manage LDAP server configurations for optional LDAP authentication. All LDAP endpoints require superuser access.

### List LDAP Configurations

```
GET /api/ldap/configs
```

**Authentication:** Superuser required

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "Corporate AD",
    "is_enabled": true,
    "is_primary": true,
    "server_url": "ldaps://ad.example.com:636",
    "base_dn": "dc=example,dc=com",
    "bind_dn": "cn=service,dc=example,dc=com",
    "use_ssl": true,
    "use_starttls": false,
    "verify_ssl": true,
    "has_ca_certificate": false,
    "user_search_base": "ou=users",
    "user_search_filter": "(objectClass=person)",
    "username_attribute": "sAMAccountName",
    "email_attribute": "mail",
    "display_name_attribute": "displayName",
    "member_of_attribute": "memberOf",
    "group_search_base": "ou=groups",
    "group_search_filter": "(objectClass=group)",
    "group_name_attribute": "cn",
    "sync_interval_minutes": 60,
    "auto_create_users": true,
    "auto_sync_groups": true,
    "default_role_id": 2,
    "last_sync_at": "2025-01-15T12:00:00",
    "last_sync_status": "success",
    "last_sync_message": "Created: 5, Updated: 10, Errors: 0",
    "last_sync_users_created": 5,
    "last_sync_users_updated": 10,
    "created_at": "2025-01-10T08:00:00",
    "updated_at": "2025-01-15T12:00:00"
  }
]
```

---

### Create LDAP Configuration

```
POST /api/ldap/configs
```

**Authentication:** Superuser required

**Request Body:**
```json
{
  "name": "Corporate AD",
  "server_url": "ldaps://ad.example.com:636",
  "base_dn": "dc=example,dc=com",
  "bind_dn": "cn=service,dc=example,dc=com",
  "bind_password": "secret",
  "use_ssl": true,
  "use_starttls": false,
  "verify_ssl": true,
  "user_search_base": "ou=users",
  "user_search_filter": "(objectClass=person)",
  "username_attribute": "sAMAccountName",
  "email_attribute": "mail",
  "display_name_attribute": "displayName",
  "member_of_attribute": "memberOf",
  "group_search_base": "ou=groups",
  "group_search_filter": "(objectClass=group)",
  "group_name_attribute": "cn",
  "auto_create_users": true,
  "auto_sync_groups": true,
  "sync_interval_minutes": 60,
  "default_role_id": 2,
  "is_enabled": false,
  "is_primary": false
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "name": "Corporate AD",
  ...
}
```

**Notes:**
- `bind_password` is encrypted before storage and never returned in responses
- Only one configuration can be marked as `is_primary`
- New configurations are disabled by default for safety

---

### Get LDAP Configuration

```
GET /api/ldap/configs/{config_id}
```

**Authentication:** Superuser required

**Response:** `200 OK` (same structure as list)

**Error Responses:**
- `404 Not Found` - Configuration does not exist

---

### Update LDAP Configuration

```
PUT /api/ldap/configs/{config_id}
```

**Authentication:** Superuser required

**Request Body:** (all fields optional)
```json
{
  "is_enabled": true,
  "bind_password": "new_password",
  "auto_create_users": true
}
```

**Response:** `200 OK` (updated configuration)

**Error Responses:**
- `404 Not Found` - Configuration does not exist

**Notes:**
- Only provided fields are updated
- Setting `is_primary: true` will unset other primaries

---

### Delete LDAP Configuration

```
DELETE /api/ldap/configs/{config_id}
```

**Authentication:** Superuser required

**Response:** `204 No Content`

**Error Responses:**
- `404 Not Found` - Configuration does not exist

**Notes:**
- Cascade deletes all associated group mappings
- Users created via this LDAP config remain in database but switch to local auth

---

### Test LDAP Connection

```
POST /api/ldap/configs/{config_id}/test
```

**Authentication:** Superuser required

**Response:** `200 OK`
```json
{
  "success": true,
  "server_info": {
    "vendor": "Microsoft Active Directory",
    "version": "Windows Server 2019",
    "naming_contexts": ["dc=example,dc=com"]
  },
  "users_found": 42,
  "message": "Connection successful. Found 42 users (limited to 100)."
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Bind failed: Invalid credentials",
  "error_type": "BindError"
}
```

**Notes:**
- Tests connection, authentication, and basic search functionality
- Limited to 100 users for performance
- Returns detailed server information for diagnostics

---

### Sync Users from LDAP

```
POST /api/ldap/configs/{config_id}/sync
```

**Authentication:** Superuser required

**Response:** `200 OK`
```json
{
  "success": true,
  "created": 5,
  "updated": 10,
  "errors": [],
  "total_errors": 0
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Connection timeout"
}
```

**Notes:**
- Creates new users with `auth_type: "ldap"`
- Updates existing LDAP users' metadata
- Does not overwrite local users
- Applies group-based role and cluster mappings
- Updates `last_sync_at` and sync status on configuration

---

### Discover LDAP Groups

```
GET /api/ldap/configs/{config_id}/groups
```

**Authentication:** Superuser required

**Response:** `200 OK`
```json
[
  {
    "dn": "cn=Admins,ou=groups,dc=example,dc=com",
    "name": "Admins",
    "description": "Administrator group"
  }
]
```

**Notes:**
- Queries LDAP server for available groups
- Uses `group_search_base` and `group_search_filter` from configuration
- Useful for building role/cluster mappings

---

## LDAP Group Mapping Endpoints

These endpoints map LDAP groups to roles and clusters for automatic access provisioning.

### List Role Mappings

```
GET /api/ldap/configs/{config_id}/role-mappings
```

**Authentication:** Superuser required

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "ldap_config_id": 1,
    "ldap_group_dn": "cn=Admins,ou=groups,dc=example,dc=com",
    "ldap_group_name": "Admins",
    "role_id": 1,
    "role_name": "Administrator",
    "created_at": "2025-01-15T10:00:00"
  }
]
```

---

### Create Role Mapping

```
POST /api/ldap/configs/{config_id}/role-mappings
```

**Authentication:** Superuser required

**Request Body:**
```json
{
  "ldap_group_dn": "cn=Admins,ou=groups,dc=example,dc=com",
  "ldap_group_name": "Admins",
  "role_id": 1
}
```

**Response:** `201 Created`

**Notes:**
- When a user syncs or authenticates, if they are a member of `ldap_group_dn`, they are automatically assigned `role_id`
- Multiple groups can map to the same role
- One group can map to multiple roles

---

### Delete Role Mapping

```
DELETE /api/ldap/configs/{config_id}/role-mappings/{mapping_id}
```

**Authentication:** Superuser required

**Response:** `204 No Content`

**Error Responses:**
- `404 Not Found` - Mapping does not exist

**Notes:**
- Does not remove roles from existing users
- Only affects future syncs/authentications

---

### List Cluster Mappings

```
GET /api/ldap/configs/{config_id}/cluster-mappings
```

**Authentication:** Superuser required

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "ldap_config_id": 1,
    "ldap_group_dn": "cn=ProdAccess,ou=groups,dc=example,dc=com",
    "ldap_group_name": "ProdAccess",
    "cluster_id": 1,
    "cluster_name": "prod-cluster",
    "created_at": "2025-01-15T10:00:00"
  }
]
```

---

### Create Cluster Mapping

```
POST /api/ldap/configs/{config_id}/cluster-mappings
```

**Authentication:** Superuser required

**Request Body:**
```json
{
  "ldap_group_dn": "cn=ProdAccess,ou=groups,dc=example,dc=com",
  "ldap_group_name": "ProdAccess",
  "cluster_id": 1
}
```

**Response:** `201 Created`

**Notes:**
- When a user syncs or authenticates, if they are a member of `ldap_group_dn`, they are automatically assigned access to `cluster_id`
- Cluster assignments are additive (don't remove existing)

---

### Delete Cluster Mapping

```
DELETE /api/ldap/configs/{config_id}/cluster-mappings/{mapping_id}
```

**Authentication:** Superuser required

**Response:** `204 No Content`

**Error Responses:**
- `404 Not Found` - Mapping does not exist

---

## Request/Response Models

### Error Responses

All endpoints may return these standard error responses:

**401 Unauthorized**
```json
{
  "detail": "Not authenticated"
}
```

**403 Forbidden**
```json
{
  "detail": "Superuser privileges required"
}
```

**404 Not Found**
```json
{
  "detail": "Resource not found"
}
```

**400 Bad Request**
```json
{
  "detail": "Validation error message"
}
```

---

## Authentication Flow

### LDAP Authentication Sequence

1. User attempts login via `/api/auth/login`
2. System tries local authentication first
3. If local fails and LDAP is enabled, tries LDAP authentication
4. If LDAP succeeds:
   - Searches for user in LDAP directory
   - Attempts bind with user's credentials
   - Extracts user metadata (email, display name, group memberships)
5. If user doesn't exist locally:
   - Auto-creates user with `auth_type: "ldap"` (if `auto_create_users: true`)
   - Generates random password hash (user can't use local auth)
6. Applies group mappings:
   - Assigns roles based on LDAP group memberships
   - Assigns cluster access based on LDAP group memberships
7. Creates session and returns token

### Permission Model

**User Cluster Assignment:**
- Non-superusers: Can only assign/view their own clusters
- Superusers: Can assign/view any user's clusters, always have access to all clusters

**LDAP Configuration:**
- All LDAP endpoints require superuser access
- This prevents privilege escalation via LDAP configuration

---

## Integration Examples

### Python Example - Assign Clusters

```python
import requests

session = requests.Session()

# Login
response = session.post("http://localhost:8000/api/auth/login", json={
    "username": "admin",
    "password": "Admin123!"
})
token = response.json()["token"]

# Assign clusters to user
response = session.put(
    "http://localhost:8000/api/users/2/clusters",
    json={"cluster_ids": [1, 2, 3]},
    cookies={"nexus_session": token}
)
print(response.json())
```

### Python Example - Configure LDAP

```python
# Create LDAP configuration
response = session.post(
    "http://localhost:8000/api/ldap/configs",
    json={
        "name": "Corporate AD",
        "server_url": "ldaps://ad.example.com:636",
        "base_dn": "dc=example,dc=com",
        "bind_dn": "cn=service,dc=example,dc=com",
        "bind_password": "secret",
        "use_ssl": True,
        "auto_create_users": True,
        "is_enabled": True,
        "is_primary": True
    },
    cookies={"nexus_session": token}
)
config_id = response.json()["id"]

# Test connection
test_result = session.post(
    f"http://localhost:8000/api/ldap/configs/{config_id}/test",
    cookies={"nexus_session": token}
)
print(test_result.json())

# Discover groups
groups = session.get(
    f"http://localhost:8000/api/ldap/configs/{config_id}/groups",
    cookies={"nexus_session": token}
)
print(groups.json())

# Create role mapping
session.post(
    f"http://localhost:8000/api/ldap/configs/{config_id}/role-mappings",
    json={
        "ldap_group_dn": "cn=Admins,ou=groups,dc=example,dc=com",
        "ldap_group_name": "Admins",
        "role_id": 1
    },
    cookies={"nexus_session": token}
)

# Sync users
sync_result = session.post(
    f"http://localhost:8000/api/ldap/configs/{config_id}/sync",
    cookies={"nexus_session": token}
)
print(sync_result.json())
```

### cURL Examples

```bash
# Get user's clusters
curl -X GET http://localhost:8000/api/users/1/clusters \
  -H "Cookie: nexus_session=YOUR_TOKEN"

# Assign clusters
curl -X PUT http://localhost:8000/api/users/1/clusters \
  -H "Content-Type: application/json" \
  -H "Cookie: nexus_session=YOUR_TOKEN" \
  -d '{"cluster_ids": [1,2,3]}'

# List LDAP configs
curl -X GET http://localhost:8000/api/ldap/configs \
  -H "Cookie: nexus_session=YOUR_TOKEN"

# Test LDAP connection
curl -X POST http://localhost:8000/api/ldap/configs/1/test \
  -H "Cookie: nexus_session=YOUR_TOKEN"
```

---

## Architecture Diagram

```
┌──────────────┐
│   Web UI     │
│  (React)     │
└──────┬───────┘
       │ HTTP/Cookie Auth
       │
┌──────▼───────────────────────────────────────────────┐
│              FastAPI Web API                         │
│  ┌────────────────────────────────────────────┐    │
│  │  User Cluster Endpoints                     │    │
│  │  - PUT  /api/users/{id}/clusters            │    │
│  │  - GET  /api/users/{id}/clusters            │    │
│  └────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────┐    │
│  │  LDAP Configuration Endpoints               │    │
│  │  - GET/POST/PUT/DELETE /api/ldap/configs    │    │
│  │  - POST /api/ldap/configs/{id}/test         │    │
│  │  - POST /api/ldap/configs/{id}/sync         │    │
│  │  - GET  /api/ldap/configs/{id}/groups       │    │
│  └────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────┐    │
│  │  LDAP Mapping Endpoints                     │    │
│  │  - GET/POST/DELETE role-mappings            │    │
│  │  - GET/POST/DELETE cluster-mappings         │    │
│  └────────────────────────────────────────────┘    │
└──────────┬───────────────────────────────────────────┘
           │
    ┌──────▼──────┐      ┌──────────────┐
    │ UserService │      │ LDAPService  │
    └──────┬──────┘      └──────┬───────┘
           │                    │
           │   ┌────────────────┘
           │   │
    ┌──────▼───▼─────────────────┐
    │   PostgreSQL Database       │
    │  - users                    │
    │  - user_clusters            │
    │  - ldap_config              │
    │  - ldap_group_role_mappings │
    │  - ldap_group_cluster_mappings │
    └─────────────────────────────┘
           │
           │ (LDAP Authentication)
           │
    ┌──────▼──────┐
    │ LDAP Server │
    │  (AD/OpenLDAP) │
    └─────────────┘
```

---

## Security Considerations

1. **Bind Password Encryption**: LDAP bind passwords are encrypted using Fernet before storage
2. **Superuser Only**: All LDAP configuration requires superuser access
3. **No Password in Responses**: `bind_password` is never returned in API responses
4. **SSL/TLS Support**: Supports LDAPS and STARTTLS for secure LDAP communication
5. **Certificate Validation**: SSL certificate validation can be enabled/disabled per config
6. **Session-Based Auth**: Uses secure HTTP-only cookies for session management
7. **Permission Checks**: User cluster assignments enforce ownership checks

---

## Best Practices

1. **Test Before Enabling**: Always test LDAP connection before enabling a configuration
2. **Use Service Account**: Create a dedicated read-only LDAP service account for binds
3. **Start with Disabled**: Create LDAP configs with `is_enabled: false` initially
4. **Monitor Sync Results**: Check `last_sync_status` and `last_sync_message` after syncs
5. **Group Discovery**: Use the groups endpoint to discover available LDAP groups
6. **Incremental Rollout**: Start with cluster mappings to limit access, then add role mappings
7. **Backup Configurations**: Export LDAP configs before making changes
8. **Keep Local Admin**: Always maintain at least one local superuser account

---

## Troubleshooting

### LDAP Connection Fails

1. Check `server_url` uses correct protocol (ldap:// or ldaps://)
2. Verify `base_dn` matches your LDAP structure
3. Test `bind_dn` and `bind_password` credentials
4. Check firewall allows connection to LDAP port
5. For SSL issues, try setting `verify_ssl: false` temporarily

### Users Not Syncing

1. Verify `user_search_filter` matches your LDAP schema
2. Check `user_search_base` is correct
3. Ensure `auto_create_users: true` is set
4. Review `last_sync_message` for specific errors
5. Test user search manually using LDAP tools

### Group Mappings Not Applied

1. Verify `member_of_attribute` matches your LDAP (memberOf for AD, groupMembership for OpenLDAP)
2. Check LDAP group DNs exactly match in mappings
3. Ensure users are actually members of groups in LDAP
4. Re-sync users after creating mappings
5. Check group mappings are for correct config_id

---

## Version History

- **v1.0.0** (2025-01-15): Initial release with full LDAP and user cluster support
