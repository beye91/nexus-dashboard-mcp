# Claude Desktop Integration Guide

## Overview

This guide explains how to connect Claude Desktop to the Nexus Dashboard MCP Server, enabling Claude to interact with your Cisco Nexus Dashboard infrastructure.

## Prerequisites

- Nexus Dashboard MCP Server deployed and running
- Claude Desktop installed
- For remote connections: Node.js 18+ installed locally

## Quick Setup

### Remote Connection (Recommended)

For accessing the MCP server running on a remote host:

**Step 1:** Locate your Claude Desktop configuration file:

| OS | Path |
|----|------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

**Step 2:** Add the MCP server configuration:

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

Replace `YOUR_SERVER_IP` with your server's IP address (e.g., `192.168.1.213`).

**Step 3:** Restart Claude Desktop

- macOS: Cmd+Q to quit, then relaunch
- Windows: Close and reopen the application
- Linux: Close and reopen the application

### Local Connection

For Claude Desktop running on the same machine as Docker:

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

## Handling Self-Signed Certificates

Since the MCP server uses self-signed certificates, you may encounter SSL/TLS errors.

### Option 1: Accept Self-Signed Certificates (Development)

Set the environment variable before running Claude Desktop:

**macOS/Linux:**
```bash
export NODE_TLS_REJECT_UNAUTHORIZED=0
open -a "Claude"
```

**Windows (PowerShell):**
```powershell
$env:NODE_TLS_REJECT_UNAUTHORIZED=0
& "C:\Path\To\Claude.exe"
```

### Option 2: Add Certificate to Trust Store (Production)

1. Download the server certificate:
   ```bash
   openssl s_client -connect YOUR_SERVER_IP:8444 -showcerts </dev/null 2>/dev/null | \
     openssl x509 -outform PEM > nexus-mcp.crt
   ```

2. Add to your system's trust store:
   - **macOS:** Double-click the .crt file and add to Keychain Access
   - **Windows:** Right-click > Install Certificate
   - **Linux:** Copy to `/usr/local/share/ca-certificates/` and run `update-ca-certificates`

## Verifying the Connection

After restarting Claude Desktop:

1. Look for the MCP server indicator (hammer icon) in Claude Desktop
2. You should see "nexus-dashboard" listed as an available server
3. The indicator should show a green status

### Test Query

Try asking Claude:

```
"List all fabrics in my Nexus Dashboard"
```

or

```
"Show me the health status of my clusters"
```

## Available Operations

### Read Operations (Always Available)

- Get fabrics, templates, policies
- List anomalies and advisories
- Query inventory and topology
- View configurations and status
- Get health metrics

### Write Operations (Requires Edit Mode)

Write operations are disabled by default. To enable:

1. Go to Web UI: `https://YOUR_SERVER_IP:7443`
2. Navigate to **Security** page
3. Enable **Edit Mode**
4. Optionally whitelist specific operations

Once enabled, you can:
- Create/update/delete fabrics
- Manage templates and policies
- Configure devices
- Deploy configurations

## Secure Access with API Token

For additional security, you can require an API token:

**Step 1:** Set the token in your deployment's `.env` file:

```env
MCP_API_TOKEN=your-secure-token-here
```

**Step 2:** Restart the services:

```bash
docker compose down
docker compose up -d
```

**Step 3:** Update Claude Desktop configuration:

```json
{
  "mcpServers": {
    "nexus-dashboard": {
      "command": "npx",
      "args": [
        "mcp-remote@latest",
        "https://YOUR_SERVER_IP:8444/mcp/sse",
        "--transport",
        "sse-only",
        "--header",
        "Authorization: Bearer your-secure-token-here"
      ]
    }
  }
}
```

## Troubleshooting

### Server Not Showing Up

1. **Check Docker containers are running:**
   ```bash
   docker compose ps
   ```

2. **Check server logs:**
   ```bash
   docker compose logs -f mcp-server
   ```

3. **Verify Claude Desktop config syntax:**
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python -m json.tool
   ```

4. **Test the SSE endpoint:**
   ```bash
   curl -k https://YOUR_SERVER_IP:8444/mcp/sse
   ```

### Permission Errors

- Check edit mode setting in Web UI
- Verify your user has appropriate role assignments
- Review audit logs: `https://YOUR_SERVER_IP:7443/audit`

### Connection Errors

1. **Test network connectivity:**
   ```bash
   curl -k https://YOUR_SERVER_IP:8444/api/health
   ```

2. **Check firewall rules:**
   - Port 8444 must be accessible

3. **Verify SSL certificate:**
   ```bash
   openssl s_client -connect YOUR_SERVER_IP:8444 -servername YOUR_SERVER_IP
   ```

### SSL/Certificate Errors

If you see "self-signed certificate" or "unable to verify" errors:

1. Use `NODE_TLS_REJECT_UNAUTHORIZED=0` for development
2. Add the certificate to your system trust store for production
3. Or use proper CA-signed certificates

## Monitoring Usage

### View Real-Time Logs

```bash
docker compose logs -f mcp-server
```

### Audit Log Access

All MCP operations are logged. View them at:
- Web UI: `https://YOUR_SERVER_IP:7443/audit`
- Database:
  ```bash
  docker compose exec postgres psql -U mcp_user -d nexus_mcp -c \
    "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 20;"
  ```

## Example Queries

### Read-Only Examples

```
"Show me all fabrics configured in Nexus Dashboard"

"What anomalies have been detected in the last 24 hours?"

"List all devices in the inventory"

"Get the configuration of fabric 'Production-DC1'"

"Show me the topology of fabric 'Test-Fabric'"

"What is the health status of my clusters?"
```

### Write Mode Examples (After Enabling)

```
"Create a new fabric named 'Development-Fabric'"

"Update the description of fabric 'Test-Fabric' to 'QA Environment'"

"Deploy the template 'Base-Config' to fabric 'Production-DC1'"
```

## Best Practices

1. **Start Read-Only:** Test queries before enabling write mode
2. **Use Specific Queries:** Include fabric names and device IDs
3. **Monitor Logs:** Keep `docker compose logs -f` running during testing
4. **Review Audit:** Check audit logs after operations
5. **Limit Access:** Use API tokens in shared environments
