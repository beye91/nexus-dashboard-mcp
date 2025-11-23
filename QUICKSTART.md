# Nexus Dashboard MCP Server - Quick Start Guide

**Complete System Ready**: MCP Server + Web API + Web UI

## What You Have

A complete Nexus Dashboard management system with:
- 🤖 **MCP Server**: 638 operations across 4 APIs (Manage, Analyze, Infra, OneManage)
- 🌐 **Web API**: FastAPI REST backend with full CRUD operations
- 💻 **Web UI**: Next.js/React dashboard for cluster management, security, and audit logs
- 🐘 **PostgreSQL**: Database with encrypted credentials and audit logging

## Option 1: Start Everything (Recommended)

Run the complete stack with Docker Compose:

```bash
cd /Users/cbeye/AI/nexus_dashboard_mcp

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

**Access Points**:
- Web UI: http://localhost:7001
- Web API: http://localhost:8002
- API Docs: http://localhost:8002/docs
- PostgreSQL: localhost:15432
- MCP Server: stdio (use with Claude Desktop)

**Services Running**:
1. `postgres` - Database (port 15432)
2. `mcp-server` - MCP Server (stdio)
3. `web-api` - FastAPI Backend (port 8002)
4. `web-ui` - Next.js Frontend (port 7001)

## Option 2: Development Mode

For active development with hot reload:

```bash
# Terminal 1: Start database
docker-compose up postgres

# Terminal 2: Start web API
docker-compose up web-api

# Terminal 3: Start web UI (hot reload)
cd web-ui
npm run dev
```

**Access**:
- Web UI: http://localhost:7001 (hot reload enabled)
- Web API: http://localhost:8002 (auto-reload on code changes)

## Option 3: MCP Server Only

If you only want the MCP server for Claude Desktop:

```bash
# Start database and MCP server
docker-compose up postgres mcp-server
```

**Configure Claude Desktop** (`~/.config/claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "nexus-dashboard": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "nexus-mcp-server",
        "python",
        "src/main.py"
      ]
    }
  }
}
```

## First Time Setup

### 1. Configure Environment

Edit `.env` file:

```env
# Database
DB_PASSWORD=NexusMCP2025!

# Nexus Dashboard (your cluster)
NEXUS_CLUSTER_URL=https://nexus-dashboard.example.com
NEXUS_USERNAME=admin
NEXUS_PASSWORD=YourPassword
NEXUS_VERIFY_SSL=false

# Security
EDIT_MODE_ENABLED=false
ENCRYPTION_KEY=<generate-with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">

# Optional
LOG_LEVEL=INFO
```

### 2. Generate Encryption Key

```bash
# Generate a new Fernet key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env file
echo "ENCRYPTION_KEY=<your-generated-key>" >> .env
```

### 3. Initialize Database

Database is automatically initialized on first run. To manually initialize:

```bash
docker-compose up postgres
docker-compose run --rm mcp-server python scripts/init_database.py
```

## Using the Web UI

### Access the Dashboard

1. Open browser: http://localhost:7001
2. You'll see the home dashboard with statistics

### Add a Cluster

1. Navigate to **Clusters** page
2. Click **Add New Cluster**
3. Fill in the form:
   - Name: `Production-DC1`
   - URL: `https://nexus-dashboard.example.com`
   - Username: `admin`
   - Password: `YourPassword`
   - SSL Verification: Off
4. Click **Create Cluster**

### Configure Security

1. Navigate to **Security** page
2. Toggle **Edit Mode** (enables POST/PUT/DELETE operations)
3. Add read-only operations (optional)
4. Add blocked operations (optional)
5. Click **Save Changes**

### View Audit Logs

1. Navigate to **Audit Logs** page
2. Use filters to search logs:
   - Cluster name
   - HTTP method
   - Status code
   - Date range
3. Click **Export CSV** to download logs

## Using with Claude Desktop

Once the MCP server is running:

1. Open Claude Desktop
2. Configure MCP server (see Option 3 above)
3. Restart Claude Desktop
4. Try queries like:
   - "List all fabrics"
   - "Show switches in Production-DC1"
   - "What anomalies have been detected?"
   - "What's the cluster health status?"

## Common Commands

### Docker

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f web-ui
docker-compose logs -f web-api
docker-compose logs -f mcp-server

# Restart a service
docker-compose restart web-ui

# Rebuild after code changes
docker-compose build
docker-compose up -d

# Clean up
docker-compose down -v  # WARNING: Deletes database!
```

### Web UI Development

```bash
cd web-ui

# Install dependencies
npm install

# Development mode
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Type check
npm run type-check

# Lint
npm run lint
```

### Database

```bash
# Connect to PostgreSQL
docker exec -it nexus-mcp-postgres psql -U mcp_user -d nexus_mcp

# Useful SQL queries
SELECT * FROM clusters;
SELECT * FROM security_config;
SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 10;
SELECT COUNT(*) FROM audit_log;
```

## Troubleshooting

### Web UI Won't Start

```bash
# Check if API is running
curl http://localhost:8002/api/health

# Check web-ui logs
docker-compose logs web-ui

# Rebuild and restart
cd web-ui && npm install
docker-compose restart web-ui
```

### API Connection Errors

```bash
# Check API is accessible
curl http://localhost:8002/api/health

# Check CORS configuration
# Should allow http://localhost:7001

# Check environment variables
docker-compose exec web-ui env | grep API_URL
```

### Database Connection Issues

```bash
# Check database is running
docker-compose ps postgres

# Check connection
docker exec -it nexus-mcp-postgres pg_isready -U mcp_user

# View database logs
docker-compose logs postgres
```

### MCP Server Issues

```bash
# Check if database is initialized
docker-compose logs mcp-server | grep "Successfully loaded"

# Should see: "Successfully loaded 4 APIs with 638 total operations"

# Reinitialize database
docker-compose run --rm mcp-server python scripts/init_database.py
```

### Port Already in Use

```bash
# Find what's using port 7001
lsof -i :7001

# Find what's using port 8000
lsof -i :8000

# Kill the process or change ports in docker-compose.yml
```

## File Locations

**Important Files**:
- Configuration: `.env`
- Docker Compose: `docker-compose.yml`
- Web UI: `web-ui/`
- API Backend: `src/api/web_api.py`
- MCP Server: `src/main.py`
- Database Schema: `src/config/schema.sql`
- Documentation: `docs/`

**Logs**:
- Docker logs: `docker-compose logs`
- Application logs: `./logs/`

## API Documentation

Interactive API documentation (Swagger UI):
- URL: http://localhost:8002/docs
- Alternative (ReDoc): http://localhost:8002/redoc

## System Architecture

```
┌─────────────┐
│   Browser   │ ─── http://localhost:7001 ───┐
└─────────────┘                               │
                                              ▼
┌──────────────┐                      ┌─────────────┐
│ Claude       │ ─── stdio ───────────│  MCP Server │
│ Desktop      │                      │  (Python)   │
└──────────────┘                      └──────┬──────┘
                                             │
      ┌──────────────────────────────────────┤
      │                                      │
      ▼                                      ▼
┌─────────────┐                      ┌─────────────┐
│   Web UI    │ ─── HTTP ───────────▶│   Web API   │
│  (Next.js)  │                      │  (FastAPI)  │
└─────────────┘                      └──────┬──────┘
                                            │
                                            ▼
                                     ┌─────────────┐
                                     │ PostgreSQL  │
                                     │  (Database) │
                                     └─────────────┘
```

## Next Steps

1. **Add Your Clusters**: Use the web UI to add your Nexus Dashboard clusters
2. **Configure Security**: Set up edit mode and operation permissions
3. **Try It Out**: Use Claude Desktop to query your infrastructure
4. **Monitor**: Check audit logs to see all operations
5. **Customize**: Modify the web UI or add new API endpoints

## Getting Help

**Documentation**:
- Main README: [README.md](README.md)
- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Web UI Guide: [docs/WEB_UI_GUIDE.md](docs/WEB_UI_GUIDE.md)
- Phase 3 Status: [docs/PHASE3_WEB_UI_COMPLETE.md](docs/PHASE3_WEB_UI_COMPLETE.md)
- Multi-API Status: [docs/MULTI_API_STATUS.md](docs/MULTI_API_STATUS.md)

**Logs**:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web-ui
docker-compose logs -f web-api
docker-compose logs -f mcp-server
```

## Production Deployment

For production deployment:

1. **Update Environment Variables**:
   - Generate strong encryption keys
   - Use production database credentials
   - Set `EDIT_MODE_ENABLED=false`
   - Set `LOG_LEVEL=WARNING`

2. **Enable HTTPS**:
   - Add reverse proxy (nginx/Caddy)
   - Configure SSL certificates
   - Update CORS origins

3. **Add Authentication**:
   - Implement JWT tokens
   - Add user management
   - Configure RBAC

4. **Monitor**:
   - Set up logging aggregation
   - Configure alerts
   - Monitor performance

---

**Status**: All 3 Phases Complete ✅
- Phase 1: MCP Server (202 operations)
- Phase 2: Multi-API Support (638 operations)
- Phase 3: Web Management UI (Complete)

**Ready to use!** 🚀
