# Claude Desktop Integration Guide

## Quick Setup

Your Nexus Dashboard MCP Server has been configured in Claude Desktop!

### ✅ Configuration Added

The MCP server has been added to:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Configuration:**
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

### 🔄 Next Steps

1. **Restart Claude Desktop**
   - Quit Claude Desktop completely (Cmd+Q)
   - Relaunch Claude Desktop

2. **Verify Connection**
   - Look for the MCP server indicator (hammer icon)
   - You should see "nexus-dashboard" in the available servers

3. **Test with a Query**
   Try asking Claude:
   ```
   "List all fabrics in my Nexus Dashboard"

   "Show me recent anomalies from the Nexus Dashboard"

   "Get the status of fabric connections"
   ```

### 🎯 Available Operations

**Read Operations (Always Available):**
- Get fabrics, templates, policies
- List anomalies and advisories
- Query inventory and topology
- View configurations and status

**Write Operations (Requires Edit Mode):**
- Create/update/delete fabrics
- Manage templates and policies
- Configure devices
- Deploy configurations

To enable write operations:
```bash
cd /Users/cbeye/AI/nexus_dashboard_mcp
echo "EDIT_MODE_ENABLED=true" >> .env
docker-compose restart mcp-server
```

### 🐛 Troubleshooting

**Server Not Showing Up:**
1. Check Docker containers are running:
   ```bash
   docker-compose ps
   ```

2. Check server logs:
   ```bash
   docker-compose logs -f mcp-server
   ```

3. Verify Claude Desktop config syntax:
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | jq .
   ```

**Permission Errors:**
- Check edit mode setting in `.env`
- Review audit logs: `docker-compose exec postgres psql -U mcp_user -d nexus_mcp`

**Connection Errors:**
- Verify Nexus Dashboard cluster is accessible: `curl -k https://nexus-dashboard.example.com`
- Check credentials in database

### 📊 Monitoring

**Server Status:**
```bash
# View real-time logs
docker-compose logs -f mcp-server

# Check container health
docker-compose ps

# View audit logs
docker-compose exec postgres psql -U mcp_user -d nexus_mcp -c "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 10;"
```

**Audit Queries:**
```sql
-- Recent operations
SELECT operation_id, http_method, response_status, timestamp
FROM audit_log
ORDER BY timestamp DESC
LIMIT 20;

-- Success rate
SELECT
  COUNT(*) FILTER (WHERE response_status BETWEEN 200 AND 299) as successful,
  COUNT(*) FILTER (WHERE response_status >= 400 OR error_message IS NOT NULL) as failed,
  COUNT(*) as total
FROM audit_log;

-- Operations by type
SELECT http_method, COUNT(*)
FROM audit_log
GROUP BY http_method;
```

### 🔐 Security Notes

**Current Mode:** Read-Only
- GET requests: ✅ Allowed
- POST/PUT/DELETE: ❌ Blocked

**To Enable Write Mode:**
1. Edit `.env`: `EDIT_MODE_ENABLED=true`
2. Restart: `docker-compose restart mcp-server`
3. Verify in logs: Should show "Edit mode: ENABLED"

**Credentials:**
- Stored encrypted in PostgreSQL
- Encryption key in `.env` (not committed to git)
- Never logged in plaintext

### 📚 Example Queries

**Read-Only (Current Mode):**
```
"Show me all fabrics configured in Nexus Dashboard"

"What anomalies have been detected in the last 24 hours?"

"List all devices in the inventory"

"Get the configuration of fabric 'Production-DC1'"

"Show me the topology of fabric 'Test-Fabric'"
```

**Write Mode (After Enabling):**
```
"Create a new fabric named 'Development-Fabric'"

"Update the description of fabric 'Test-Fabric' to 'QA Environment'"

"Deploy the template 'Base-Config' to fabric 'Production-DC1'"

"Delete the fabric 'Old-Test-Fabric'"
```

### 🎓 Tips

1. **Be Specific**: Include fabric names, device IDs when querying
2. **Check Audit**: Review audit_log table to see what operations were performed
3. **Start Read-Only**: Test queries before enabling write mode
4. **Monitor Logs**: Keep `docker-compose logs -f` running during testing

### 🔄 Restarting Services

```bash
# Restart everything
docker-compose restart

# Restart just MCP server
docker-compose restart mcp-server

# View startup logs
docker-compose logs -f mcp-server

# Stop everything
docker-compose down

# Start fresh
docker-compose up -d
```

### 📞 Need Help?

**Check Logs:**
```bash
docker-compose logs mcp-server | grep ERROR
docker-compose logs mcp-server | grep -i "authentication"
```

**Database Access:**
```bash
docker-compose exec postgres psql -U mcp_user -d nexus_mcp
```

**Reset and Retry:**
```bash
docker-compose down
docker-compose up -d
docker-compose logs -f mcp-server
```

---

**Status**: Configured and Ready ✅
**Cluster**: https://nexus-dashboard.example.com
**Mode**: Read-Only (Edit mode available on demand)
**Tools**: 202 Nexus Dashboard operations
