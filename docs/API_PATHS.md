# Nexus Dashboard API Path Reference

## API Base Paths

### Manage API
**Base Path**: `/api/v1/manage`
**Server URL**: `https://{cluster}/api/v1/manage`

**Example Endpoints**:
- List Fabrics: `GET /api/v1/manage/fabrics`
- Get Fabric: `GET /api/v1/manage/fabrics/{fabricId}`
- List Anomalies: `GET /api/v1/manage/anomalyRules/complianceRules`

### Analyze API (Phase 2)
**Base Path**: `/api/v1/analyze`
**Server URL**: `https://{cluster}/api/v1/analyze`

### Infrastructure API (Phase 2)
**Base Path**: `/api/v1/infra`
**Server URL**: `https://{cluster}/api/v1/infra`

### OneManage API (Phase 2)
**Base Path**: `/api/v1/one-manage`
**Server URL**: `https://{cluster}/api/v1/one-manage`

### Orchestrator API (Phase 2)
**Base Path**: TBD
**Server URL**: TBD

## OpenAPI Specification Structure

### How Paths are Defined

In the OpenAPI spec (`nexus_dashboard_manage.json`):

```json
{
  "openapi": "3.0.3",
  "servers": [
    {
      "url": "https://{cluster}/api/v1/manage",
      "variables": {
        "cluster": {
          "default": "example.com"
        }
      }
    }
  ],
  "paths": {
    "/fabrics": {
      "get": {
        "operationId": "listFabrics",
        ...
      }
    }
  }
}
```

**Key Points**:
- The `servers[0].url` contains the full base path: `https://{cluster}/api/v1/manage`
- The `paths` object contains relative paths like `/fabrics`
- Full URL is: `servers[0].url + paths.key` = `https://{cluster}/api/v1/manage/fabrics`

## Implementation in MCP Server

### Path Construction Flow

1. **API Loader** (`src/core/api_loader.py`):
   - Reads OpenAPI spec
   - Extracts paths from `paths` object (e.g., `/fabrics`)
   - Does NOT include the base path from `servers[0].url`

2. **MCP Server** (`src/core/mcp_server.py`):
   - Gets operation with path `/fabrics`
   - Passes it to AuthMiddleware

3. **Auth Middleware** (`src/middleware/auth.py`):
   - **CRITICAL**: Prepends `/api/v1/manage` to the path
   - Code:
     ```python
     if not path.startswith("/api/"):
         path = f"/api/v1/manage{path}"
     ```
   - Final path: `/api/v1/manage/fabrics`

4. **Nexus API Client** (`src/services/nexus_api.py`):
   - Receives full path: `/api/v1/manage/fabrics`
   - Joins with base_url: `https://nexus-dashboard.example.com`
   - Final URL: `https://nexus-dashboard.example.com/api/v1/manage/fabrics`

## Authentication Endpoints

### Login
**Endpoint**: `POST /login`
**Full URL**: `https://{cluster}/login`

**Note**: Login endpoint is NOT under `/api/v1/manage`. It's a top-level endpoint.

**Request Body**:
```json
{
  "username": "admin",
  "password": "password"
}
```

**Response**:
- Sets session cookies
- May return token in response body

## Common Issues and Solutions

### Issue: 404 Not Found

**Symptom**: API returns 404 when calling endpoints

**Possible Causes**:
1. Missing base path (`/api/v1/manage`)
2. Wrong API version
3. Service not running
4. Incorrect cluster URL

**Debugging Steps**:
```bash
# Check what URL is being called
docker-compose logs mcp-server | grep "API request"

# Test endpoint manually
curl -k https://nexus-dashboard.example.com/api/v1/manage/fabrics

# Verify cluster is accessible
curl -k https://nexus-dashboard.example.com
```

### Issue: 401 Unauthorized

**Symptom**: API returns 401

**Possible Causes**:
1. Authentication failed
2. Session expired
3. Invalid credentials

**Solution**: Check authentication in AuthMiddleware

### Issue: Wrong Base Path

**Symptom**: Calls going to wrong API (e.g., Analyze instead of Manage)

**Solution**: Verify the base path logic in `src/middleware/auth.py`

## Testing API Paths

### Manual Testing

```bash
# 1. Get authentication token
curl -k -X POST https://nexus-dashboard.example.com/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Davinci!!02"}' \
  -c cookies.txt

# 2. Test Manage API endpoint
curl -k -X GET https://nexus-dashboard.example.com/api/v1/manage/fabrics \
  -b cookies.txt

# 3. Test with specific fabric
curl -k -X GET https://nexus-dashboard.example.com/api/v1/manage/fabrics/{fabricId} \
  -b cookies.txt
```

### Automated Testing

See `src/services/nexus_api.py` for the `NexusAPIClient` class that handles:
- Authentication with cookies
- Automatic retry on 401
- Session management
- Path construction

## Multi-API Support (Phase 2)

When adding support for multiple APIs, the path construction logic needs to be updated:

### Current (Phase 1 - Manage API Only):
```python
# In src/middleware/auth.py
if not path.startswith("/api/"):
    path = f"/api/v1/manage{path}"
```

### Future (Phase 2 - Multi-API):
```python
# In src/middleware/auth.py
async def execute_request(
    self,
    method: str,
    path: str,
    api_name: str = "manage",  # New parameter
    ...
):
    # Map API names to base paths
    api_base_paths = {
        "manage": "/api/v1/manage",
        "analyze": "/api/v1/analyze",
        "infra": "/api/v1/infra",
        "one-manage": "/api/v1/one-manage",
    }

    if not path.startswith("/api/"):
        base_path = api_base_paths.get(api_name, "/api/v1/manage")
        path = f"{base_path}{path}"
```

## References

- Nexus Dashboard API Documentation: https://developer.cisco.com/docs/nexus-dashboard/
- OpenAPI 3.0 Specification: https://swagger.io/specification/
- Nexus Dashboard Manage API OpenAPI: `openapi_specs/nexus_dashboard_manage.json`

---

**Last Updated**: November 23, 2025
**Status**: Active documentation for Phase 1 implementation
