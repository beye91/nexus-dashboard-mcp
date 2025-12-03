# Multi-User Role-Based Access Control (RBAC)

This document describes the multi-user authentication and authorization system for Nexus Dashboard MCP Server.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Authentication Flow                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐         ┌──────────────────┐                         │
│  │  Claude Desktop  │         │     Web UI       │                         │
│  │  (API Token)     │         │  (Session/Cookie)│                         │
│  └────────┬─────────┘         └────────┬─────────┘                         │
│           │                            │                                    │
│           │ Authorization:             │ session_token                      │
│           │ Bearer <api_token>         │ (HTTP Cookie)                      │
│           │                            │                                    │
│           └────────────┬───────────────┘                                    │
│                        │                                                    │
│                        ▼                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      MCP Server / Web API                            │   │
│  │                                                                      │   │
│  │   ┌──────────────────────────────────────────────────────────┐      │   │
│  │   │                 Token/Session Validation                  │      │   │
│  │   │                                                          │      │   │
│  │   │  API Token → users.api_token → User                      │      │   │
│  │   │  Session   → user_sessions.session_token → User          │      │   │
│  │   └──────────────────────────────────────────────────────────┘      │   │
│  │                              │                                       │   │
│  │                              ▼                                       │   │
│  │   ┌──────────────────────────────────────────────────────────┐      │   │
│  │   │                  Permission Check                         │      │   │
│  │   │                                                          │      │   │
│  │   │  User → user_roles → roles → role_operations → allowed?  │      │   │
│  │   └──────────────────────────────────────────────────────────┘      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Database Schema

```
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│      users       │       │    user_roles    │       │      roles       │
├──────────────────┤       ├──────────────────┤       ├──────────────────┤
│ id (PK)          │◄──┐   │ id (PK)          │   ┌──►│ id (PK)          │
│ username         │   │   │ user_id (FK)     │───┘   │ name             │
│ password_hash    │   └───│ role_id (FK)     │───────│ description      │
│ email            │       │ created_at       │       │ edit_mode_enabled│
│ display_name     │       └──────────────────┘       │ is_system_role   │
│ api_token        │                                  │ created_at       │
│ is_active        │                                  │ updated_at       │
│ is_superuser     │                                  └────────┬─────────┘
│ auth_type        │                                           │
│ last_login       │       ┌──────────────────┐                │
│ created_at       │       │  role_operations │                │
│ updated_at       │       ├──────────────────┤                │
└──────────────────┘       │ id (PK)          │                │
                           │ role_id (FK)     │────────────────┘
┌──────────────────┐       │ operation_name   │
│  user_sessions   │       │ created_at       │
├──────────────────┤       └──────────────────┘
│ id (PK)          │
│ user_id (FK)     │───────► users.id
│ session_token    │
│ expires_at       │
│ created_at       │
└──────────────────┘
```

## Default System Roles

| Role Name        | Edit Mode | Description                                        |
|------------------|-----------|---------------------------------------------------|
| Administrator    | Yes       | Full access to all operations with edit mode      |
| Network Operator | Yes       | Read-write access to network operational tasks    |
| Read-Only User   | No        | View-only access without edit capabilities        |

## Authentication Methods

### 1. Web UI Authentication (Session-based)

```
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password123"
}

Response:
{
  "token": "<session_token>",
  "user": { ... }
}
```

The session token is stored as an HTTP cookie (`session_token`) with HttpOnly flag.

### 2. Claude Desktop Authentication (API Token)

Each user has a unique API token stored in `users.api_token`. Configure Claude Desktop:

```json
{
  "mcpServers": {
    "nexus-dashboard": {
      "command": "npx",
      "args": [
        "mcp-remote@latest",
        "http://<server>:8002/mcp/sse",
        "--allow-http",
        "--transport", "sse-only",
        "--header", "Authorization: Bearer <USER_API_TOKEN>"
      ]
    }
  }
}
```

## API Endpoints

### Authentication

| Method | Endpoint              | Description                      |
|--------|----------------------|----------------------------------|
| POST   | /api/auth/login      | Login and create session         |
| POST   | /api/auth/logout     | Logout and invalidate session    |
| GET    | /api/auth/me         | Get current user info            |
| POST   | /api/auth/setup      | Create first admin user (setup)  |

### Users

| Method | Endpoint                      | Description                    |
|--------|------------------------------|--------------------------------|
| GET    | /api/users                   | List all users                 |
| POST   | /api/users                   | Create new user                |
| GET    | /api/users/{id}              | Get user details               |
| PUT    | /api/users/{id}              | Update user                    |
| DELETE | /api/users/{id}              | Delete user                    |
| PUT    | /api/users/{id}/roles        | Assign roles to user           |
| POST   | /api/users/{id}/regenerate-token | Generate new API token     |

### Roles

| Method | Endpoint                      | Description                    |
|--------|------------------------------|--------------------------------|
| GET    | /api/roles                   | List all roles                 |
| POST   | /api/roles                   | Create new role                |
| GET    | /api/roles/{id}              | Get role details               |
| PUT    | /api/roles/{id}              | Update role                    |
| DELETE | /api/roles/{id}              | Delete role (not system roles) |
| PUT    | /api/roles/{id}/operations   | Set role's allowed operations  |

### Operations

| Method | Endpoint                      | Description                    |
|--------|------------------------------|--------------------------------|
| GET    | /api/operations              | List operations (searchable)   |
| GET    | /api/operations/grouped      | Operations grouped by API      |
| GET    | /api/operations/api-names    | List API names                 |
| GET    | /api/operations/count        | Count total operations         |

## MCP Tool Filtering

When a user connects via Claude Desktop:

1. Token is validated against `users.api_token`
2. User's roles are loaded
3. `tools/list` returns only operations allowed by user's roles
4. `tools/call` checks permission before executing

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Tool Filtering                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  All Tools (638+)                                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ manage_createVlan, manage_updateVlan, manage_deleteVlan, │   │
│  │ analyze_getInsights, infra_deployPolicy, ...             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              │ User: network_operator           │
│                              │ Roles: [Network Operator]        │
│                              │ Allowed: [manage_*, analyze_*]   │
│                              ▼                                  │
│  Filtered Tools                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ manage_createVlan, manage_updateVlan, analyze_getInsights│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Permission Model

### Superuser
- Has access to ALL operations regardless of role assignments
- Can manage users and roles
- Always has edit mode enabled

### Regular User
- Operations determined by assigned roles
- Edit mode enabled if ANY assigned role has `edit_mode_enabled = true`
- Cannot manage other users (only superusers can)

## First-Time Setup

1. Access Web UI at `http://<server>:7001`
2. System detects no users exist (setup mode)
3. Create first admin user (automatically assigned Administrator role)
4. Login with created credentials
5. Create additional users and assign roles as needed

## Security Considerations

- Passwords hashed with bcrypt (12 rounds)
- API tokens are 64-character random hex strings
- Session tokens expire after 24 hours
- HttpOnly cookies prevent XSS token theft
- System roles cannot be deleted
