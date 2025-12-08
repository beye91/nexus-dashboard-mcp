# Deployment Guide

## Prerequisites

### Required

- Docker 20.10+ and Docker Compose 2.0+
- Access to a Nexus Dashboard cluster
- 2GB RAM minimum (4GB recommended)
- 10GB disk space

### Optional

- Python 3.11+ (for local development)
- Node.js 18+ (for remote MCP access via mcp-remote)
- PostgreSQL client tools (for database management)

## Architecture Overview

```
+----------------------------------------------------------+
|                    External Clients                       |
|              (Browser, Claude Desktop)                    |
+----------------------------------------------------------+
                    |                    |
               [HTTPS]              [HTTPS]
                    |                    |
            Port 7443            Port 8444
                    |                    |
+------------------+    +--------------------------+
|    Web UI        |    |        Web API           |
|    Next.js       |--->|        FastAPI           |
|    (HTTPS)       |    |  [REST API] [MCP SSE]    |
+------------------+    +--------------------------+
        |                           |
        +----------+----------------+
                   |
           [Docker Volume]
           /app/certs/
           - server.crt
           - server.key
                   |
    +--------------+---------------+
    |              |               |
+--------+  +------------+  +--------------+
|Postgres|  | MCP Server |  |Nexus Dashboard|
| 15432  |  |  (stdio)   |  |   Clusters    |
+--------+  +------------+  +--------------+
```

## Quick Deployment

### Step 1: Clone Repository

```bash
git clone https://github.com/beye91/nexus-dashboard-mcp.git
cd nexus-dashboard-mcp
```

### Step 2: Configure Environment

Create a `.env` file with your server's IP address:

```bash
# Minimal configuration
echo "CERT_SERVER_IP=YOUR_SERVER_IP" > .env
```

For production, include additional settings:

```env
# Required: Your server's IP address (included in SSL certificate)
CERT_SERVER_IP=192.168.1.213

# Optional: Security keys (auto-generated if not provided)
ENCRYPTION_KEY=your-fernet-key
SESSION_SECRET_KEY=your-session-secret

# Optional: Certificate configuration
CERT_DAYS=365
CERT_CN=nexus-dashboard

# Optional: Logging
LOG_LEVEL=INFO
```

**Generate Encryption Key:**
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Step 3: Start Services

```bash
docker compose up -d --build
```

This command will:
1. Generate self-signed SSL certificates (first startup only)
2. Initialize PostgreSQL database with schema
3. Start all services with host networking

### Step 4: Verify Deployment

```bash
# Check container status
docker compose ps

# View logs
docker compose logs -f

# Test API health
curl -k https://localhost:8444/api/health
```

### Step 5: Initial Setup

1. Open browser to `https://YOUR_SERVER_IP:7443`
2. Accept the self-signed certificate warning
3. Create the initial admin user:
   - Username: `admin`
   - Email: `admin@example.com`
   - Password: `Admin123!` (or your preferred password)
4. Add your first Nexus Dashboard cluster

## Port Reference

| Service | Port | Protocol | Description | Configurable |
|---------|------|----------|-------------|--------------|
| Web UI | 7443 | HTTPS | Management interface | `WEB_UI_PORT` |
| Web UI Internal | 7100 | HTTP | Internal Next.js server (localhost only) | `WEB_UI_INTERNAL_PORT` |
| Web API | 8444 | HTTPS | REST API and MCP SSE | `WEB_API_PORT` |
| Internal HTTP | 8001 | HTTP | Web UI to API proxy | `INTERNAL_HTTP_PORT` |
| PostgreSQL | 15432 | TCP | Database | via docker-compose |

> **Note:** Services use Docker host networking mode to enable access to external networks (Nexus Dashboard clusters).

### Port Configuration

The internal Next.js port (default: 7100) can be configured to avoid conflicts with other services (e.g., Grafana which commonly uses port 3000). Set the following environment variables in your `.env` file:

```env
# External HTTPS port for Web UI (default: 7443)
WEB_UI_PORT=7443

# Internal Next.js port - localhost only (default: 7100)
# Change this if you have conflicts with other services
WEB_UI_INTERNAL_PORT=7100
```

## SSL/TLS Configuration

### Certificate Generation

Certificates are automatically generated on first startup:

- **Location:** Docker volume `nexus-mcp-certs`
- **Validity:** 365 days (configurable via `CERT_DAYS`)
- **SANs Included:**
  - `localhost`
  - `127.0.0.1`
  - Your server IP (`CERT_SERVER_IP`)

### Regenerating Certificates

```bash
# Remove existing certificates
docker volume rm nexus-mcp-certs

# Restart services (new certificates will be generated)
docker compose up -d
```

### Using Custom Certificates

To use your own certificates:

1. Create a certificates directory:
   ```bash
   mkdir -p certs
   cp your-certificate.crt certs/server.crt
   cp your-private-key.key certs/server.key
   chmod 600 certs/server.key
   ```

2. Update `docker-compose.yml` to mount your certificates:
   ```yaml
   volumes:
     - ./certs:/app/certs:ro
   ```

## Environment Variables Reference

### Core Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CERT_SERVER_IP` | (none) | Your server's IP address for SSL SAN |
| `CERT_DAYS` | `365` | Certificate validity in days |
| `CERT_CN` | `nexus-dashboard` | Certificate common name |
| `ENCRYPTION_KEY` | (auto) | Fernet key for credential encryption |
| `SESSION_SECRET_KEY` | (auto) | Session signing key |

### Port Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `WEB_UI_PORT` | `7443` | External HTTPS port for Web UI |
| `WEB_UI_INTERNAL_PORT` | `7100` | Internal Next.js port (localhost only) |
| `WEB_API_PORT` | `8444` | External HTTPS port for Web API |
| `INTERNAL_HTTP_PORT` | `8001` | Internal HTTP port for API proxy |

### Security

| Variable | Default | Description |
|----------|---------|-------------|
| `EDIT_MODE_ENABLED` | `false` | Enable write operations |
| `MCP_API_TOKEN` | (none) | Optional token for MCP access |
| `NEXUS_VERIFY_SSL` | `false` | Verify Nexus Dashboard SSL |

### Nexus Dashboard (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXUS_CLUSTER_URL` | (none) | Default cluster URL |
| `NEXUS_USERNAME` | `admin` | Default username |
| `NEXUS_PASSWORD` | (none) | Default password |

### Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level |

## Claude Desktop Integration

### Remote Connection (Recommended)

For connecting to the MCP server running on a different host:

```json
{
  "mcpServers": {
    "nexus-dashboard": {
      "command": "npx",
      "args": [
        "mcp-remote@latest",
        "https://YOUR_SERVER_IP:8444/mcp/sse",
        "--transport",
        "sse-only"
      ]
    }
  }
}
```

> **Self-Signed Certificates:** You may need to:
> - Add the certificate to your system's trust store, or
> - Set `NODE_TLS_REJECT_UNAUTHORIZED=0` in your environment

### Local Connection

For Claude Desktop running on the same machine:

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

### Configuration File Locations

| OS | Path |
|----|------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

## Health Monitoring

### Container Health

```bash
# Check all containers
docker compose ps

# View detailed health status
docker inspect nexus-mcp-web-api --format='{{.State.Health.Status}}'
```

### API Health Endpoint

```bash
curl -k https://localhost:8444/api/health
```

Response:
```json
{
  "status": "healthy",
  "database": true,
  "uptime_seconds": 3600,
  "services": [
    {"name": "PostgreSQL", "status": "healthy"},
    {"name": "Cluster Configuration", "status": "healthy"},
    {"name": "MCP Server", "status": "healthy"}
  ]
}
```

### Web UI Health Page

Access `https://YOUR_SERVER_IP:7443/health` for a visual health dashboard.

## Database Management

### Connect to Database

```bash
docker compose exec postgres psql -U mcp_user -d nexus_mcp
```

### Common Queries

```sql
-- List tables
\dt

-- View clusters
SELECT name, url, is_active, status FROM clusters;

-- View recent audit logs
SELECT operation_id, http_method, response_status, timestamp
FROM audit_log
ORDER BY timestamp DESC
LIMIT 10;

-- View users
SELECT id, username, email, is_active FROM users;
```

### Backup

```bash
# Create backup
docker compose exec postgres pg_dump -U mcp_user nexus_mcp > backup-$(date +%Y%m%d).sql

# Restore from backup
docker compose exec -T postgres psql -U mcp_user nexus_mcp < backup-20250101.sql
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs for errors
docker compose logs web-api
docker compose logs web-ui

# Verify port availability
netstat -tlnp | grep -E '7443|8444|15432'
```

### Certificate Errors

```bash
# View certificate details
docker compose exec web-api openssl x509 -in /app/certs/server.crt -text -noout

# Check certificate expiration
docker compose exec web-api openssl x509 -in /app/certs/server.crt -noout -dates
```

### Database Connection Issues

```bash
# Test database connectivity
docker compose exec postgres pg_isready -U mcp_user

# Check database logs
docker compose logs postgres
```

### API Not Responding

```bash
# Check API logs
docker compose logs -f web-api

# Test internal HTTP endpoint
curl http://localhost:8001/api/health
```

## Updating

### Pull Latest Changes

```bash
# Stop services
docker compose down

# Pull updates
git pull origin main

# Rebuild and restart
docker compose up -d --build
```

### Clean Update

```bash
# Stop and remove containers
docker compose down

# Remove old images
docker compose rm -f
docker image prune -f

# Rebuild from scratch
docker compose build --no-cache
docker compose up -d
```

## Production Checklist

- [ ] Set `CERT_SERVER_IP` to your production server IP
- [ ] Generate and configure unique `ENCRYPTION_KEY`
- [ ] Generate and configure unique `SESSION_SECRET_KEY`
- [ ] Configure firewall to allow ports 7443, 8444, 15432
- [ ] Change default admin password after first login
- [ ] Keep `EDIT_MODE_ENABLED=false` unless needed
- [ ] Set up regular database backups
- [ ] Configure log rotation
- [ ] Consider using proper SSL certificates from a CA
- [ ] Review and restrict network access
