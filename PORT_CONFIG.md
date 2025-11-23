# Port Configuration

## Current Port Assignments

| Service | Port | Protocol | Access |
|---------|------|----------|--------|
| **PostgreSQL** | 15432 | TCP | localhost:15432 |
| **MCP Server** | stdio | stdio | Claude Desktop |
| **Web API** | 8002 | HTTP | http://localhost:8002 |
| **Web UI** | 7001 | HTTP | http://localhost:7001 |

## Port Selection Process

Port 7001 was selected after checking availability:

```bash
Port 7000: IN USE
Port 7001: AVAILABLE ✓ (selected)
Port 7002: AVAILABLE
Port 7003: AVAILABLE
Port 7004: AVAILABLE
Port 7005: AVAILABLE
```

**Rationale**:
- Avoided 3000-3999 range (user has many services in this range)
- Port 3000: Conflicted with another application
- Port 3001: Conflicted with Grafana
- Selected 7001 from verified available ports in 7000 range

## Access URLs

### Web UI
- **URL**: http://localhost:7001
- **Docker**: Maps 7001 → 3000 (container internal)
- **Development**: `npm run dev` uses PORT=7001 from .env.local

### Web API
- **URL**: http://localhost:8002
- **Swagger Docs**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc
- **CORS**: Allows http://localhost:7001

### Database
- **URL**: postgresql://mcp_user:password@localhost:15432/nexus_mcp
- **Docker**: Maps 15432 → 5432 (container internal)

## How to Change Ports

If you need to change ports in the future:

### 1. Check Port Availability

```bash
# Check if a port is available
lsof -i :7001

# Check range of ports
for port in 7000 7001 7002; do
  echo -n "Port $port: "
  lsof -i :$port > /dev/null 2>&1 && echo "IN USE" || echo "AVAILABLE"
done
```

### 2. Update Configuration Files

**docker-compose.yml**:
```yaml
web-ui:
  ports:
    - "7001:3000"  # Change 7001 to your desired port
```

**src/api/web_api.py**:
```python
allow_origins=["http://localhost:7001", "http://127.0.0.1:7001"]
                             # ^^^^                      ^^^^
```

**web-ui/.env.local**:
```env
PORT=7001  # Change to your desired port
```

### 3. Update Documentation

Update these files:
- `QUICKSTART.md`
- `docs/PHASE3_WEB_UI_COMPLETE.md`
- `PORT_CONFIG.md` (this file)

### 4. Restart Services

```bash
# Rebuild and restart
docker-compose down
docker-compose build web-ui
docker-compose up -d

# Or for development
cd web-ui
npm run dev
```

## Common Port Conflicts

### Port Already in Use Error

If you see:
```
Error: bind EADDRINUSE :::7001
```

**Solution 1**: Find what's using the port
```bash
lsof -i :7001
# Kill the process if safe
kill -9 <PID>
```

**Solution 2**: Change to a different port (see above)

### CORS Errors in Browser

If you see:
```
Access to fetch at 'http://localhost:8002/api/...' from origin 'http://localhost:XXXX' has been blocked by CORS policy
```

**Solution**: Update CORS origins in `src/api/web_api.py`:
```python
allow_origins=["http://localhost:YOUR_NEW_PORT"]
```

## Docker Port Mapping

Understanding Docker port mapping:

```yaml
ports:
  - "7001:3000"
    # ↑    ↑
    # |    └── Container internal port (don't change)
    # └─────── Host port (change this)
```

- **Host Port** (7001): What you access from your browser
- **Container Port** (3000): Internal Next.js port (don't change)

## Environment Variables

### Web UI (.env.local)
```env
# API endpoint (backend)
NEXT_PUBLIC_API_URL=http://localhost:8002

# Development server port
PORT=7001
```

### Web API (via docker-compose)
```env
# Database connection
DATABASE_URL=postgresql://mcp_user:password@postgres:5432/nexus_mcp

# Encryption key
ENCRYPTION_KEY=<your-fernet-key>
```

## Service Communication

### Browser → Web UI → Web API

```
Browser (http://localhost:7001)
    ↓
Next.js Web UI (port 7001)
    ↓ HTTP requests to NEXT_PUBLIC_API_URL
FastAPI Web API (port 8000)
    ↓ SQL queries
PostgreSQL (port 15432)
```

### Claude Desktop → MCP Server

```
Claude Desktop
    ↓ stdio
MCP Server (Python)
    ↓ SQL queries
PostgreSQL (port 15432)
```

## Port Security Notes

### Firewall Configuration

For production deployment, consider:

```bash
# Only allow localhost access (default)
# Already configured in docker-compose.yml:
ports:
  - "127.0.0.1:7001:3000"  # Only accessible from localhost
  - "127.0.0.1:8000:8000"  # Only accessible from localhost
```

### Public Access

To allow network access (not recommended for development):

```yaml
# Remove 127.0.0.1 prefix
ports:
  - "7001:3000"  # Accessible from network
```

Then update CORS:
```python
allow_origins=["http://YOUR_IP:7001", "http://localhost:7001"]
```

## Troubleshooting

### Issue: Can't access Web UI

**Check**:
1. Service is running: `docker-compose ps`
2. Port is correct: `docker-compose logs web-ui | grep "started"`
3. Firewall allows localhost connections
4. Browser is using http:// not https://

### Issue: API calls fail from Web UI

**Check**:
1. Web API is running: `curl http://localhost:8002/api/health`
2. CORS is configured: Check browser console for CORS errors
3. Environment variable is set: `docker-compose exec web-ui env | grep API_URL`

### Issue: Port changes not taking effect

**Solution**:
```bash
# Stop everything
docker-compose down

# Remove containers
docker-compose rm -f

# Rebuild
docker-compose build

# Start fresh
docker-compose up -d
```

---

**Current Configuration**: Port 7001 (verified available)
**Last Updated**: November 23, 2025
**Status**: Production Ready
