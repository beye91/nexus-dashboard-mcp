# Nexus Dashboard MCP Server - Quick Start Guide

Get up and running in 5 minutes!

## What You Get

A complete Nexus Dashboard management system with:
- **MCP Server**: 638 operations across 4 APIs (Manage, Analyze, Infra, OneManage)
- **Web API**: FastAPI REST backend with HTTPS
- **Web UI**: Next.js/React dashboard with authentication
- **PostgreSQL**: Database with encrypted credentials and audit logging
- **HTTPS**: Self-signed certificates auto-generated

## Quick Start

### Step 1: Clone and Configure

```bash
git clone https://github.com/beye91/nexus-dashboard-mcp.git
cd nexus-dashboard-mcp

# Configure your server's IP address
echo "CERT_SERVER_IP=YOUR_SERVER_IP" > .env
```

Replace `YOUR_SERVER_IP` with your server's IP address (e.g., `192.168.1.213`).

### Step 2: Start Services

```bash
docker compose up -d --build
```

Wait for all services to start (about 1-2 minutes on first run).

### Step 3: Access Web UI

1. Open browser: `https://YOUR_SERVER_IP:7443`
2. Accept the self-signed certificate warning
3. Create admin account:
   - Username: `admin`
   - Email: `admin@example.com`
   - Password: `Admin123!`

### Step 4: Add Your Cluster

1. Navigate to **Clusters** page
2. Click **Add New Cluster**
3. Enter details:
   - Name: `my-nexus-cluster`
   - URL: `https://nexus-dashboard.example.com`
   - Username: `admin`
   - Password: Your password
   - SSL Verification: Off (for self-signed certs)
4. Click **Test Connection** to verify
5. Click **Create Cluster**

### Step 5: Configure Claude Desktop

Add to your Claude Desktop config:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

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

Restart Claude Desktop and try: "List all fabrics in my Nexus Dashboard"

## Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Web UI | `https://YOUR_SERVER_IP:7443` | Management dashboard |
| Web API | `https://YOUR_SERVER_IP:8444` | REST API |
| API Docs | `https://YOUR_SERVER_IP:8444/docs` | Swagger documentation |
| MCP SSE | `https://YOUR_SERVER_IP:8444/mcp/sse` | Claude Desktop endpoint |

## Common Commands

```bash
# Check status
docker compose ps

# View logs
docker compose logs -f

# Restart services
docker compose restart

# Stop everything
docker compose down

# Clean restart (keeps data)
docker compose down && docker compose up -d

# Full reset (WARNING: deletes all data!)
docker compose down -v
docker volume rm nexus-mcp-certs
docker compose up -d --build
```

## Troubleshooting

### Can't access Web UI
```bash
# Check containers are running
docker compose ps

# Check for errors
docker compose logs web-ui
docker compose logs web-api
```

### Certificate issues
```bash
# Regenerate certificates
docker volume rm nexus-mcp-certs
docker compose up -d
```

### Database issues
```bash
# Connect to database
docker compose exec postgres psql -U mcp_user -d nexus_mcp

# Check tables
\dt
```

## Next Steps

1. **Add more clusters**: Configure additional Nexus Dashboard instances
2. **Set up users**: Add team members with role-based access
3. **Enable edit mode**: Allow write operations when needed
4. **Review audit logs**: Monitor all API operations
5. **Read the docs**: Check `docs/` folder for detailed guides

## Documentation

- [Deployment Guide](docs/DEPLOYMENT.md) - Production setup
- [Claude Desktop Setup](docs/CLAUDE_DESKTOP_SETUP.md) - MCP integration
- [Multi-User RBAC](docs/MULTI_USER_RBAC.md) - User management
- [API Guidance](docs/API_GUIDANCE_SYSTEM.md) - Customizing API behavior

---

**Ready to use!**
