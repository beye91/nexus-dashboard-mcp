# Deployment Guide

## Prerequisites

### Required

- Docker 20.10+ and Docker Compose 2.0+
- Access to a Nexus Dashboard cluster
- 2GB RAM minimum (4GB recommended)
- 10GB disk space

### Optional

- Python 3.11+ (for local development)
- PostgreSQL client tools (for database management)

## Deployment Options

### Option 1: Docker Compose (Recommended)

Best for: Quick start, development, small deployments

```bash
# 1. Clone repository
git clone https://github.com/beye91/nexus-dashboard-mcp.git
cd nexus-dashboard-mcp

# 2. Configure environment
cp .env.example .env
nano .env  # Edit with your settings

# 3. Generate encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 4. Update .env with generated key and your credentials
# ENCRYPTION_KEY=<generated-key>
# NEXUS_CLUSTER_URL=https://your-nexus-dashboard.com
# NEXUS_USERNAME=admin
# NEXUS_PASSWORD=your-password

# 5. Start services
docker-compose up -d

# 6. Verify deployment
docker-compose logs -f mcp-server
```

### Option 2: Docker Standalone

Best for: Custom orchestration, Kubernetes preparation

```bash
# 1. Build image
docker build -t nexus-dashboard-mcp:latest .

# 2. Run PostgreSQL
docker run -d \
  --name nexus-mcp-postgres \
  -e POSTGRES_DB=nexus_mcp \
  -e POSTGRES_USER=mcp_user \
  -e POSTGRES_PASSWORD=changeme \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15-alpine

# 3. Initialize database
docker exec -i nexus-mcp-postgres psql -U mcp_user -d nexus_mcp < src/config/schema.sql

# 4. Run MCP server
docker run -d \
  --name nexus-mcp-server \
  --link nexus-mcp-postgres:postgres \
  -e DATABASE_URL=postgresql://mcp_user:changeme@postgres:5432/nexus_mcp \
  -e NEXUS_CLUSTER_URL=https://your-nexus-dashboard.com \
  -e NEXUS_USERNAME=admin \
  -e NEXUS_PASSWORD=your-password \
  -e EDIT_MODE_ENABLED=false \
  -e ENCRYPTION_KEY=your-key \
  -v $(pwd)/openapi_specs:/app/openapi_specs:ro \
  nexus-dashboard-mcp:latest
```

### Option 3: Kubernetes (Future)

Coming in Phase 4.

## Configuration

### Environment Variables

#### Required

```env
# Nexus Dashboard connection
NEXUS_CLUSTER_URL=https://nexus-dashboard.example.com
NEXUS_USERNAME=admin
NEXUS_PASSWORD=YourSecurePassword

# Encryption for credential storage
ENCRYPTION_KEY=<fernet-key>

# Database connection
DATABASE_URL=postgresql://mcp_user:password@postgres:5432/nexus_mcp
```

#### Optional

```env
# Security
EDIT_MODE_ENABLED=false           # Enable write operations
SESSION_SECRET_KEY=random-string   # Session encryption
NEXUS_VERIFY_SSL=false            # SSL verification

# Performance
API_TIMEOUT=30                    # API request timeout (seconds)
API_RETRY_ATTEMPTS=3              # Number of retries

# Logging
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Database
DB_PASSWORD=changeme              # PostgreSQL password
```

### Security Best Practices

1. **Strong Passwords**: Use generated passwords
   ```bash
   openssl rand -base64 32
   ```

2. **Encryption Key**: Generate securely
   ```bash
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

3. **Environment Files**: Never commit .env to git
   ```bash
   echo ".env" >> .gitignore
   ```

4. **Read-Only Mode**: Keep `EDIT_MODE_ENABLED=false` unless needed

5. **SSL Verification**: Set `NEXUS_VERIFY_SSL=true` in production

## Integration with Claude Desktop

### macOS

1. Locate configuration file:
   ```bash
   ~/Library/Application Support/Claude/claude_desktop_config.json
   ```

2. Add MCP server configuration:
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

3. Restart Claude Desktop

### Windows

1. Configuration file location:
   ```
   %APPDATA%\Claude\claude_desktop_config.json
   ```

2. Same configuration as macOS

3. Restart Claude Desktop

### Linux

1. Configuration file location:
   ```
   ~/.config/Claude/claude_desktop_config.json
   ```

2. Same configuration

3. Restart Claude Desktop

## Health Checks

### Container Health

```bash
# Check all containers
docker-compose ps

# Check specific container
docker-compose ps mcp-server

# View detailed health
docker inspect nexus-mcp-server --format='{{.State.Health.Status}}'
```

### Database Health

```bash
# Connect to database
docker-compose exec postgres psql -U mcp_user -d nexus_mcp

# Check tables
\dt

# Check cluster credentials (encrypted)
SELECT name, url, is_active FROM clusters;

# Check recent audit logs
SELECT operation_id, http_method, response_status, timestamp
FROM audit_log
ORDER BY timestamp DESC
LIMIT 10;

# Exit
\q
```

### API Health

```bash
# View server logs
docker-compose logs -f mcp-server

# Look for successful startup messages:
# - "Loaded Manage API: ..."
# - "Registered X tools with MCP server"
# - "Nexus Dashboard MCP Server started"
```

## Monitoring

### Log Aggregation

#### View Real-Time Logs

```bash
# All services
docker-compose logs -f

# MCP server only
docker-compose logs -f mcp-server

# PostgreSQL only
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100 mcp-server
```

#### Export Logs

```bash
# Export to file
docker-compose logs mcp-server > mcp-server.log

# Export with timestamps
docker-compose logs -t mcp-server > mcp-server-timestamped.log
```

### Audit Log Queries

```bash
# Connect to database
docker-compose exec postgres psql -U mcp_user -d nexus_mcp

# View operation statistics
SELECT
  http_method,
  COUNT(*) as count,
  AVG(CASE WHEN response_status BETWEEN 200 AND 299 THEN 1 ELSE 0 END) * 100 as success_rate
FROM audit_log
GROUP BY http_method;

# View recent errors
SELECT timestamp, operation_id, error_message
FROM audit_log
WHERE error_message IS NOT NULL
ORDER BY timestamp DESC
LIMIT 20;

# View operations by date
SELECT
  DATE(timestamp) as date,
  COUNT(*) as operations
FROM audit_log
GROUP BY DATE(timestamp)
ORDER BY date DESC;
```

## Backup and Restore

### Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U mcp_user nexus_mcp > backup-$(date +%Y%m%d).sql

# Verify backup
ls -lh backup-*.sql
```

### Database Restore

```bash
# Stop MCP server
docker-compose stop mcp-server

# Restore from backup
docker-compose exec -T postgres psql -U mcp_user nexus_mcp < backup-20250123.sql

# Restart MCP server
docker-compose start mcp-server
```

### Volume Backup

```bash
# Backup PostgreSQL data volume
docker run --rm \
  -v nexus_dashboard_mcp_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres-data-$(date +%Y%m%d).tar.gz /data

# Verify
ls -lh postgres-data-*.tar.gz
```

## Troubleshooting

### Container Won't Start

```bash
# Check container status
docker-compose ps

# View startup errors
docker-compose logs mcp-server

# Check resource usage
docker stats
```

Common issues:
- **Port conflict**: Change port in docker-compose.yml
- **Memory limit**: Increase Docker memory allocation
- **Permission errors**: Check volume permissions

### Database Connection Errors

```bash
# Test database connectivity
docker-compose exec postgres pg_isready -U mcp_user

# Check connection from MCP server
docker-compose exec mcp-server python -c "
from src.config.database import get_db
import asyncio
async def test():
    db = get_db()
    async with db.session() as session:
        print('Database connection successful')
asyncio.run(test())
"
```

### Authentication Failures

```bash
# View authentication logs
docker-compose logs mcp-server | grep -i auth

# Test credentials manually
curl -k -X POST https://your-nexus-dashboard.com/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"yourpassword"}'
```

Common issues:
- **Invalid credentials**: Verify NEXUS_USERNAME and NEXUS_PASSWORD
- **SSL errors**: Set NEXUS_VERIFY_SSL=false for self-signed certs
- **Network issues**: Check firewall rules

### Performance Issues

```bash
# Check resource usage
docker stats

# View slow operations in audit log
docker-compose exec postgres psql -U mcp_user -d nexus_mcp -c "
SELECT operation_id, http_method, path,
       EXTRACT(EPOCH FROM (timestamp - LAG(timestamp) OVER (ORDER BY timestamp))) as duration
FROM audit_log
ORDER BY timestamp DESC
LIMIT 20;"
```

## Scaling

### Vertical Scaling (Resources)

Update docker-compose.yml:

```yaml
services:
  mcp-server:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### Horizontal Scaling (Future)

Coming in Phase 4:
- Multiple MCP server instances
- Load balancing
- Session sharing via Redis

## Updates and Maintenance

### Updating the MCP Server

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Verify update
docker-compose logs -f mcp-server
```

### Database Migrations

```bash
# Apply new schema changes
docker-compose exec -T postgres psql -U mcp_user nexus_mcp < migrations/v2.sql

# Verify migration
docker-compose exec postgres psql -U mcp_user nexus_mcp -c "\dt"
```

### Cleaning Up

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove images
docker rmi nexus-dashboard-mcp

# Clean up unused Docker resources
docker system prune -a
```

## Production Checklist

- [ ] Strong passwords configured
- [ ] Encryption key generated and stored securely
- [ ] SSL verification enabled (NEXUS_VERIFY_SSL=true)
- [ ] Edit mode disabled by default
- [ ] Backup strategy implemented
- [ ] Monitoring configured
- [ ] Log rotation enabled
- [ ] Resource limits set
- [ ] Security audit completed
- [ ] Documentation reviewed
