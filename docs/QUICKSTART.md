# Quick Start Guide

## 5-Minute Setup

### 1. Prerequisites

```bash
# Verify Docker is installed
docker --version
docker-compose --version
```

### 2. Clone and Configure

```bash
cd nexus_dashboard_mcp

# Copy environment file
cp .env.example .env
```

### 3. Edit Configuration

Edit `.env` file:

```env
# Your Nexus Dashboard details
NEXUS_CLUSTER_URL=https://nexus-dashboard.example.com
NEXUS_USERNAME=admin
NEXUS_PASSWORD=your-password

# Generate encryption key (run this command):
# python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=your-generated-key-here

# Security (set to true to enable write operations)
EDIT_MODE_ENABLED=false

# Database
DB_PASSWORD=change-this-password
```

### 4. Start Server

```bash
# Option A: Using setup script (recommended)
./scripts/setup.sh

# Option B: Manual start
docker-compose up -d
```

### 5. Verify Deployment

```bash
# Check logs
docker-compose logs -f mcp-server

# Look for these messages:
# ✓ "Loaded Manage API: ..."
# ✓ "Registered X tools with MCP server"
# ✓ "Nexus Dashboard MCP Server started"
```

### 6. Test Connection

```bash
# Check database
docker-compose exec postgres psql -U mcp_user -d nexus_mcp -c "SELECT * FROM clusters;"

# Should show your cluster configuration
```

## Using with Claude Desktop

### macOS Configuration

1. Open: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. Add:
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

4. Look for MCP icon/indicator showing "nexus-dashboard" server connected

## Example Queries

### Read-Only Operations (Always Allowed)

```
"Show me all fabrics in my Nexus Dashboard"

"List recent anomalies detected in the network"

"What's the status of fabric connections?"

"Show inventory of all devices"
```

### Write Operations (Requires `EDIT_MODE_ENABLED=true`)

```
"Create a new fabric named 'Production-DC1'"

"Update the description of fabric 'Test-Fabric'"

"Delete the fabric 'Old-Test'"
```

## Troubleshooting

### Container Won't Start

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs mcp-server

# Common fixes:
docker-compose down
docker-compose up -d --build
```

### Authentication Failures

```bash
# Test credentials manually
curl -k -X POST $NEXUS_CLUSTER_URL/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"yourpass"}'

# If using self-signed certs, ensure:
NEXUS_VERIFY_SSL=false
```

### Database Issues

```bash
# Reinitialize database
docker-compose down -v
docker-compose up -d
```

## Next Steps

1. Read full documentation: `docs/README.md`
2. Explore available tools in Claude Desktop
3. Try read-only queries first
4. Enable edit mode when you need write operations
5. Monitor audit logs for operation history

## Getting Help

- Issues: https://github.com/beye91/nexus-dashboard-mcp/issues
- Docs: `docs/` directory
- Troubleshooting: `docs/DEPLOYMENT.md#troubleshooting`

## Security Reminders

- Keep `EDIT_MODE_ENABLED=false` unless actively making changes
- Use strong passwords for database and Nexus Dashboard
- Protect your `.env` file (never commit to git)
- Review audit logs regularly:
  ```bash
  docker-compose exec postgres psql -U mcp_user -d nexus_mcp -c "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 10;"
  ```

## Status Check Commands

```bash
# All services
docker-compose ps

# Server logs
docker-compose logs -f mcp-server

# Database connection
docker-compose exec postgres pg_isready

# Recent operations
docker-compose exec postgres psql -U mcp_user -d nexus_mcp -c \
  "SELECT operation_id, http_method, response_status, timestamp FROM audit_log ORDER BY timestamp DESC LIMIT 5;"

# Statistics
docker-compose exec postgres psql -U mcp_user -d nexus_mcp -c \
  "SELECT http_method, COUNT(*) as count FROM audit_log GROUP BY http_method;"
```

Happy automating! 🚀
