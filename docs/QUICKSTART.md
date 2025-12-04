# Quick Start Guide

## 5-Minute Setup

### 1. Prerequisites

```bash
# Verify Docker is installed
docker --version
docker compose version
```

### 2. Clone and Configure

```bash
git clone https://github.com/beye91/nexus-dashboard-mcp.git
cd nexus-dashboard-mcp

# Configure your server's IP address (required for SSL certificate)
echo "CERT_SERVER_IP=YOUR_SERVER_IP" > .env
```

Replace `YOUR_SERVER_IP` with your server's IP address (e.g., `192.168.1.213`).

### 3. Start Services

```bash
docker compose up -d --build
```

Wait 1-2 minutes for all services to start. The first startup will:
- Generate self-signed SSL certificates
- Initialize the PostgreSQL database
- Start all services

### 4. Verify Deployment

```bash
# Check container status
docker compose ps

# View logs
docker compose logs -f

# Test API health
curl -k https://localhost:8444/api/health
```

### 5. Initial Setup

1. Open browser: `https://YOUR_SERVER_IP:7443`
2. Accept the self-signed certificate warning
3. Create admin account:
   - Username: `admin`
   - Email: `admin@example.com`
   - Password: `Admin123!`

### 6. Add Your Cluster

1. Navigate to **Clusters** page
2. Click **Add New Cluster**
3. Fill in details:
   - Name: `my-cluster`
   - URL: `https://nexus-dashboard.example.com`
   - Username: `admin`
   - Password: Your password
   - SSL Verification: Off (for self-signed certs)
4. Click **Test Connection**
5. Click **Create Cluster**

## Using with Claude Desktop

### Configuration

Add to your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

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

Replace `YOUR_SERVER_IP` with your server's IP address.

### Restart and Test

1. Restart Claude Desktop
2. Look for MCP icon showing "nexus-dashboard" connected
3. Try: "List all fabrics in my Nexus Dashboard"

## Example Queries

### Read-Only Operations (Always Allowed)

```
"Show me all fabrics in my Nexus Dashboard"

"List recent anomalies detected in the network"

"What's the status of fabric connections?"

"Show inventory of all devices"
```

### Write Operations (Requires Edit Mode)

Enable edit mode in Web UI > Security, then:

```
"Create a new fabric named 'Production-DC1'"

"Update the description of fabric 'Test-Fabric'"

"Delete the fabric 'Old-Test'"
```

## Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Web UI | `https://YOUR_SERVER_IP:7443` | Management dashboard |
| Web API | `https://YOUR_SERVER_IP:8444` | REST API |
| API Docs | `https://YOUR_SERVER_IP:8444/docs` | Swagger UI |
| MCP SSE | `https://YOUR_SERVER_IP:8444/mcp/sse` | Claude endpoint |
| PostgreSQL | `localhost:15432` | Database |

## Troubleshooting

### Container Won't Start

```bash
# Check status
docker compose ps

# View logs
docker compose logs web-api
docker compose logs web-ui

# Restart
docker compose down && docker compose up -d
```

### Certificate Issues

```bash
# Regenerate certificates
docker volume rm nexus-mcp-certs
docker compose up -d
```

### Authentication Failures

```bash
# Test Nexus Dashboard connection manually
curl -k -X POST https://nexus-dashboard.example.com/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"yourpass"}'
```

### Database Issues

```bash
# Connect to database
docker compose exec postgres psql -U mcp_user -d nexus_mcp

# Full reset (WARNING: deletes all data!)
docker compose down -v
docker compose up -d --build
```

## Common Commands

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f

# Restart a service
docker compose restart web-ui

# Rebuild and restart
docker compose up -d --build

# Clean up unused images
docker image prune -f
```

## Security Reminders

- Keep `EDIT_MODE_ENABLED=false` unless actively making changes
- Change default admin password after first login
- Protect your `.env` file (never commit to git)
- Review audit logs regularly in Web UI

## Next Steps

1. **Read documentation**: Check `docs/DEPLOYMENT.md` for production setup
2. **Configure users**: Add team members with roles in Web UI
3. **Explore APIs**: Use Claude to discover available operations
4. **Monitor**: Review audit logs for operation history

## Getting Help

- Issues: https://github.com/beye91/nexus-dashboard-mcp/issues
- Documentation: `docs/` directory
- Troubleshooting: `docs/DEPLOYMENT.md#troubleshooting`

Happy automating!
