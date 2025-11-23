# Architecture Documentation

## Overview

The Nexus Dashboard MCP Server is built with a modular, layered architecture designed for security, maintainability, and extensibility.

## Core Components

### 1. MCP Server Core (`src/core/`)

**Purpose**: Handles MCP protocol communication and tool registration

**Key Files**:
- `mcp_server.py`: Main MCP server implementation
- `api_loader.py`: OpenAPI specification loader and validator

**Responsibilities**:
- Load and validate OpenAPI specifications
- Generate MCP tools from API operations
- Handle tool execution requests
- Manage stdio communication

### 2. Middleware Layer (`src/middleware/`)

**Purpose**: Cross-cutting concerns for all API operations

#### Authentication Middleware (`auth.py`)
- Manages Nexus Dashboard authentication
- Handles session/cookie management
- Executes authenticated API requests
- Automatic token refresh on expiration

#### Security Middleware (`security.py`)
- Enforces read-only vs edit mode
- Blocks write operations when edit mode disabled
- Validates operation permissions
- Provides security status reporting

#### Audit Logger (`logging.py`)
- Logs all operations to PostgreSQL
- Tracks request/response data
- Records successes and failures
- Provides audit query capabilities

### 3. Services Layer (`src/services/`)

**Purpose**: Business logic and external integrations

#### Credential Manager (`credential_manager.py`)
- Secure credential storage with Fernet encryption
- CRUD operations for cluster credentials
- Credential retrieval and decryption

#### Nexus API Client (`nexus_api.py`)
- HTTP client for Nexus Dashboard
- Authentication handling
- Retry logic and error handling
- Connection pooling

### 4. Data Layer (`src/models/`)

**Purpose**: Database models using SQLAlchemy ORM

**Models**:
- `Cluster`: Nexus Dashboard cluster credentials
- `SecurityConfig`: Global security settings
- `APIEndpoint`: Registry of available API operations
- `AuditLog`: Audit trail of all operations

### 5. Configuration (`src/config/`)

**Purpose**: Application configuration and database setup

**Components**:
- `settings.py`: Pydantic settings from environment
- `database.py`: SQLAlchemy async engine setup
- `schema.sql`: PostgreSQL schema definition

## Data Flow

### Read Operation (GET)

```
1. User Query → Claude Desktop
2. Claude Desktop → MCP Server (tool call)
3. MCP Server → Security Middleware (check: always allowed)
4. MCP Server → Auth Middleware (authenticate if needed)
5. Auth Middleware → Nexus Dashboard API
6. Nexus Dashboard → Response
7. MCP Server → Audit Logger (log success)
8. MCP Server → Claude Desktop (return data)
```

### Write Operation (POST/PUT/DELETE)

```
1. User Query → Claude Desktop
2. Claude Desktop → MCP Server (tool call)
3. MCP Server → Security Middleware (check edit mode)
   ├─ If disabled → PermissionError → User
   └─ If enabled → Continue
4. MCP Server → Auth Middleware
5. Auth Middleware → Nexus Dashboard API
6. Nexus Dashboard → Response
7. MCP Server → Audit Logger (log with request body)
8. MCP Server → Claude Desktop (return result)
```

## Security Architecture

### Defense in Depth

1. **Network Layer**: Docker network isolation
2. **Application Layer**: Read-only mode enforcement
3. **Data Layer**: Encrypted credentials at rest
4. **Audit Layer**: Complete operation logging

### Authentication Flow

```
┌─────────────┐
│ MCP Server  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Auth Middleware │
└──────┬──────────┘
       │
       ▼
┌─────────────────────┐
│ Credential Manager  │
│ (decrypt password)  │
└──────┬──────────────┘
       │
       ▼
┌──────────────────────┐
│ Nexus API Client     │
│ POST /login          │
│ (Basic Auth)         │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Nexus Dashboard      │
│ Returns cookies      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Cache session        │
│ Use for all requests │
└──────────────────────┘
```

### Encryption

**Credentials Encryption**:
- Algorithm: Fernet (symmetric encryption)
- Key: Environment variable `ENCRYPTION_KEY`
- Scope: Passwords in `clusters` table

**In Transit**:
- HTTPS for Nexus Dashboard communication
- Option to disable SSL verification for dev/test

## Database Schema

### Entity Relationship Diagram

```
┌──────────────┐
│   clusters   │
│──────────────│
│ id (PK)      │◄────┐
│ name (UK)    │     │
│ url          │     │
│ username     │     │
│ password_enc │     │
│ verify_ssl   │     │
│ is_active    │     │
└──────────────┘     │
                     │
                     │ cluster_id (FK)
                     │
┌──────────────┐     │
│  audit_log   │     │
│──────────────│     │
│ id (PK)      │     │
│ cluster_id   │─────┘
│ operation_id │
│ http_method  │
│ path         │
│ request_body │
│ response_*   │
│ error_msg    │
│ timestamp    │
└──────────────┘

┌──────────────────┐
│ security_config  │
│──────────────────│
│ id (PK)          │
│ edit_mode_enabled│
│ allowed_ops[]    │
│ audit_logging    │
└──────────────────┘

┌──────────────────┐
│  api_endpoints   │
│──────────────────│
│ id (PK)          │
│ api_name         │
│ operation_id (UK)│
│ http_method      │
│ path             │
│ enabled          │
│ requires_edit    │
└──────────────────┘
```

## Tool Generation

### From OpenAPI to MCP Tool

```python
# OpenAPI Operation
{
  "get": {
    "operationId": "getFabrics",
    "summary": "Get list of fabrics",
    "parameters": [
      {"name": "limit", "in": "query", "schema": {"type": "integer"}}
    ],
    "responses": {
      "200": {"description": "Success"}
    }
  }
}

# Generated MCP Tool
Tool(
  name="manage_getFabrics",
  description="GET /api/v1/fabrics - Get list of fabrics",
  inputSchema={
    "type": "object",
    "properties": {
      "limit": {"type": "integer", "description": "Query parameter"}
    }
  },
  fn=async_execute_function
)
```

## Extension Points

### Adding New APIs

1. Place OpenAPI spec in `openapi_specs/`
2. Update `api_loader.py` to include new spec
3. Create load method in `mcp_server.py`:
   ```python
   async def load_new_api(self):
       spec = self.api_loader.load_openapi_spec("new_api.json")
       await self._create_tools_from_spec("new_api", spec)
   ```
4. Call from `run()` method

### Custom Middleware

Implement middleware interface:
```python
class CustomMiddleware:
    async def before_request(self, method, path, params, body):
        # Pre-processing
        pass

    async def after_request(self, response):
        # Post-processing
        pass
```

## Performance Considerations

### Database Connection Pooling

- Async connection pool (max 10, overflow 20)
- Pre-ping to detect stale connections
- Automatic reconnection on failure

### HTTP Client

- Connection reuse via httpx AsyncClient
- Configurable timeout (default 30s)
- Retry logic (max 3 attempts)

### Caching (Future)

Planned for Phase 4:
- Redis for response caching
- Token caching with TTL
- Cluster configuration caching

## Scalability

### Current (Phase 1)

- Single MCP server instance
- Single PostgreSQL instance
- Suitable for: Development, small teams

### Future (Phase 4+)

- Multiple MCP server instances (horizontal scaling)
- PostgreSQL replication
- Redis cluster for caching
- Load balancer for API requests
- Suitable for: Enterprise, large teams

## Error Handling

### Error Propagation

```
API Error
  ↓
Auth/Service Layer (log, wrap)
  ↓
Middleware (audit log)
  ↓
MCP Server (format for MCP protocol)
  ↓
Claude Desktop (user-friendly message)
```

### Error Categories

1. **Authentication Errors**: 401, credential issues
2. **Permission Errors**: Edit mode required
3. **Validation Errors**: Invalid parameters
4. **API Errors**: Nexus Dashboard errors (4xx, 5xx)
5. **System Errors**: Database, network failures

Each category has specific handling and user messaging.

## Logging Strategy

### Log Levels

- **DEBUG**: Detailed trace for development
- **INFO**: Normal operations, successful requests
- **WARNING**: Degraded state, retries
- **ERROR**: Failures that don't stop execution
- **CRITICAL**: Fatal errors requiring intervention

### Log Destinations

1. **stderr**: Real-time application logs
2. **PostgreSQL**: Audit trail (via audit_log table)
3. **Future**: External log aggregation (ELK, Splunk)

## Testing Strategy

### Unit Tests (`tests/unit/`)

- Individual functions and classes
- Mocked dependencies
- Fast execution

### Integration Tests (`tests/integration/`)

- Multi-component workflows
- Real database (test DB)
- Mocked Nexus Dashboard API

### E2E Tests (Future)

- Full stack testing
- Real Nexus Dashboard (sandbox/dev)
- User workflow validation
