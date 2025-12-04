# Securing MCP Servers: A Practical Guide to Enterprise-Grade AI Tool Security

## The Hidden Risk in AI Tooling

Model Context Protocol (MCP) is changing how AI assistants interact with enterprise systems. Claude, GPT, and other LLMs can now execute real operations against production infrastructure through MCP servers. This is powerful, but it comes with a question most teams aren't asking:

**Who's guarding the AI's access to your network?**

When an MCP server connects to Cisco Nexus Dashboard, it gains access to fabric management, device configurations, VLAN provisioning, and network topology. One poorly secured MCP endpoint could become an attack vector for your entire data center infrastructure.

This guide documents the security architecture we built for the Nexus Dashboard MCP Server, a reference implementation for securing AI-to-infrastructure communication.

---

## Why MCP Security Matters

### The Attack Surface

Traditional API security focuses on human users with predictable behavior. MCP servers face different threats:

```
+------------------+     +------------------+     +-------------------+
|   Claude/GPT     |---->|   MCP Server     |---->|  Nexus Dashboard  |
|   (AI Agent)     |     |   (Bridge)       |     |  (Infrastructure) |
+------------------+     +------------------+     +-------------------+
        |                        |                         |
   Prompt Injection?      Credential Theft?         Fabric Changes?
   Unauthorized Ops?      Session Hijacking?        Config Drift?
```

**Key risks:**
- AI agents can be manipulated through prompt injection to execute unintended operations
- MCP endpoints exposed over HTTP leak credentials and session tokens
- Write operations without explicit approval can modify production configs
- No audit trail means no forensic capability after incidents
- Shared credentials across users violate least-privilege principles

### The Compliance Gap

Most organizations have SOC2, ISO 27001, or PCI-DSS requirements. An unsecured MCP server creates gaps in:

- **Access Control**: Who approved this AI operation?
- **Audit Logging**: What did the AI change and when?
- **Encryption in Transit**: Is the AI's communication encrypted?
- **Credential Management**: Are API credentials stored securely?

---

## Security Architecture Overview

Our implementation addresses these gaps with a defense-in-depth approach:

```
+----------------------------------------------------------+
|                    External Clients                       |
|              (Browser, Claude Desktop)                    |
+----------------------------------------------------------+
                    |                    |
               [HTTPS/TLS]          [HTTPS/TLS]
            (Self-signed or CA)   (Self-signed or CA)
                    |                    |
            Port 7443            Port 8444
                    |                    |
+-------------------+    +---------------------------+
|     Web UI        |    |         Web API           |
|   (Next.js)       |--->|        (FastAPI)          |
|                   |    |                           |
|  - Login/Session  |    |  - JWT Authentication    |
|  - RBAC Dashboard |    |  - Operation Whitelist   |
|  - Audit Viewer   |    |  - Request Validation    |
+-------------------+    |  - MCP SSE Endpoint      |
                         +---------------------------+
                                     |
              +----------------------+----------------------+
              |                      |                      |
     +--------+--------+    +--------+--------+    +--------+--------+
     |   PostgreSQL    |    |   MCP Server    |    | Nexus Dashboard |
     |                 |    |                 |    |    Clusters     |
     | - Encrypted     |    | - Read-Only     |    |                 |
     |   Credentials   |    |   by Default    |    | - Per-Cluster   |
     | - Audit Logs    |    | - Tool Registry |    |   Credentials   |
     | - User/Roles    |    | - 638 Operations|    | - SSL Optional  |
     +-----------------+    +-----------------+    +-----------------+
```

---

## Implementation: Seven Layers of Security

### 1. Transport Security (HTTPS Everywhere)

**The Problem:** HTTP transmits credentials and session tokens in plaintext. Anyone on the network path can intercept them.

**Our Solution:** Self-signed certificates auto-generated on first startup.

```bash
# Certificate generation script (scripts/generate-certs.sh)
openssl req -x509 -newkey rsa:4096 -nodes \
    -out "$CERT_DIR/server.crt" \
    -keyout "$CERT_DIR/server.key" \
    -days "$CERT_DAYS" \
    -subj "/CN=${CERT_CN}/O=${CERT_ORG}/C=US" \
    -addext "subjectAltName=${SAN_LIST}"
```

**Key features:**
- 4096-bit RSA keys (strong encryption)
- Configurable SANs for IP and hostname flexibility
- Persistent via Docker volume (survives restarts)
- Regeneration on demand for key rotation

```yaml
# docker-compose.yml excerpt
services:
  cert-init:
    image: alpine:latest
    command: sh /scripts/generate-certs.sh
    volumes:
      - certs:/app/certs
    environment:
      - CERT_SERVER_IP=${CERT_SERVER_IP:-192.168.1.213}
```

**Result:** All communication encrypted. Certificate includes server IP for browser trust.

---

### 2. Read-Only by Default (Edit Mode Protection)

**The Problem:** AI agents can execute write operations that modify production infrastructure.

**Our Solution:** Two-tier operation control with explicit edit mode enablement.

```python
# src/core/security_manager.py
class SecurityManager:
    def is_operation_allowed(self, operation_id: str, http_method: str) -> bool:
        # Read operations always allowed
        if http_method.upper() == "GET":
            return True

        # Write operations require edit mode
        if not self.edit_mode_enabled:
            return False

        # Check whitelist for granular control
        if self.whitelisted_operations:
            return operation_id in self.whitelisted_operations

        return True
```

**Web UI control:**
```
+------------------------------------------+
|  Security Settings                       |
+------------------------------------------+
|                                          |
|  Edit Mode: [OFF] [ON]                   |
|                                          |
|  When enabled, write operations are      |
|  allowed through the MCP interface.      |
|                                          |
|  Whitelisted Operations:                 |
|  [ ] fabric-create                       |
|  [ ] fabric-update                       |
|  [x] fabric-deploy (approved)            |
|  [ ] fabric-delete                       |
|                                          |
+------------------------------------------+
```

**Result:** Zero write operations possible until explicitly enabled. Granular whitelisting for approved operations only.

---

### 3. Multi-User Role-Based Access Control (RBAC)

**The Problem:** Single shared credential means no accountability and no least-privilege.

**Our Solution:** User management with role-based permissions.

```
+------------------+     +------------------+     +------------------+
|      Admin       |     |     Operator     |     |      Viewer      |
+------------------+     +------------------+     +------------------+
| - Full access    |     | - Read access    |     | - Read-only      |
| - User mgmt      |     | - Limited writes |     | - View clusters  |
| - Security config|     | - No user mgmt   |     | - View audit     |
| - Cluster mgmt   |     | - Cluster ops    |     | - No changes     |
+------------------+     +------------------+     +------------------+
```

**Database schema:**
```sql
-- Users table with secure password storage
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- bcrypt hashed
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Roles with permission sets
CREATE TABLE roles (
    id UUID PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    permissions JSONB NOT NULL,
    is_system_role BOOLEAN DEFAULT false
);

-- User-role assignments
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id),
    role_id UUID REFERENCES roles(id),
    PRIMARY KEY (user_id, role_id)
);
```

**Result:** Individual user accounts, password policies, role-based access. Audit logs tied to specific users.

---

### 4. Encrypted Credential Storage

**The Problem:** Nexus Dashboard credentials stored in plaintext can be extracted from database dumps.

**Our Solution:** Fernet symmetric encryption for all stored credentials.

```python
# src/core/encryption.py
from cryptography.fernet import Fernet

class CredentialEncryption:
    def __init__(self, key: str):
        self.cipher = Fernet(key.encode())

    def encrypt(self, plaintext: str) -> str:
        return self.cipher.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self.cipher.decrypt(ciphertext.encode()).decode()
```

**Cluster credential storage:**
```python
# When saving a cluster
cluster.password_encrypted = encryption.encrypt(password)
cluster.password = None  # Never store plaintext

# When connecting to cluster
password = encryption.decrypt(cluster.password_encrypted)
```

**Key management:**
```bash
# Generate encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Store in environment (not in code!)
ENCRYPTION_KEY=gAAAAABh...your-key-here...
```

**Result:** Database breach does not expose Nexus Dashboard credentials. Key rotation possible without data loss.

---

### 5. Comprehensive Audit Logging

**The Problem:** No record of what the AI did, when, or who approved it.

**Our Solution:** Every MCP operation logged with full context.

```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),

    -- Who
    user_id UUID REFERENCES users(id),
    username VARCHAR(50),
    client_ip VARCHAR(45),

    -- What
    operation_id VARCHAR(100) NOT NULL,
    operation_name VARCHAR(255),
    http_method VARCHAR(10),

    -- Target
    cluster_id UUID REFERENCES clusters(id),
    cluster_name VARCHAR(100),

    -- Result
    response_status INTEGER,
    error_message TEXT,

    -- Context
    request_params JSONB,
    execution_time_ms INTEGER
);
```

**Audit log viewer in Web UI:**
```
+------------------------------------------------------------------+
| Audit Log                                          [Export CSV]  |
+------------------------------------------------------------------+
| Timestamp           | User    | Operation        | Status | Time |
+------------------------------------------------------------------+
| 2025-12-04 20:15:32 | admin   | fabric-list      | 200    | 45ms |
| 2025-12-04 20:14:18 | admin   | cluster-test     | 200    | 890ms|
| 2025-12-04 20:13:05 | system  | health-check     | 200    | 12ms |
+------------------------------------------------------------------+
```

**Result:** Complete forensic trail. Filter by user, operation, status, or time range. CSV export for compliance reports.

---

### 6. Session Security

**The Problem:** Session tokens without proper expiration or validation enable session hijacking.

**Our Solution:** Secure session management with HttpOnly cookies.

```python
# Session configuration
SESSION_CONFIG = {
    "secret_key": os.environ.get("SESSION_SECRET_KEY"),
    "cookie_name": "nexus_mcp_session",
    "max_age": 3600,  # 1 hour
    "httponly": True,  # No JavaScript access
    "secure": True,    # HTTPS only
    "samesite": "lax"  # CSRF protection
}
```

**Login flow:**
```
+--------+     +--------+     +----------+     +--------+
| Browser|---->| Web UI |---->| Web API  |---->|   DB   |
+--------+     +--------+     +----------+     +--------+
    |              |               |               |
    | POST /login  |               |               |
    |------------->|               |               |
    |              | POST /api/    |               |
    |              | auth/login    |               |
    |              |-------------->|               |
    |              |               | Verify        |
    |              |               | bcrypt hash   |
    |              |               |-------------->|
    |              |               |<--------------|
    |              |               |               |
    |              | Set-Cookie:   |               |
    |              | (HttpOnly,    |               |
    |              |  Secure)      |               |
    |              |<--------------|               |
    | Redirect     |               |               |
    |<-------------|               |               |
```

**Result:** Sessions expire after inactivity. Cookies not accessible to JavaScript (XSS protection). HTTPS-only transmission.

---

### 7. Optional API Token Authentication

**The Problem:** In multi-tenant environments, an additional authentication layer is needed for MCP access.

**Our Solution:** Optional bearer token for MCP endpoints.

```python
# Environment configuration
MCP_API_TOKEN=your-secure-token-here

# Token validation middleware
async def verify_mcp_token(request: Request):
    expected_token = os.environ.get("MCP_API_TOKEN")

    if not expected_token:
        return  # Token not required

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid token")

    token = auth_header.split(" ")[1]
    if token != expected_token:
        raise HTTPException(403, "Invalid token")
```

**Claude Desktop configuration with token:**
```json
{
  "mcpServers": {
    "nexus-dashboard": {
      "command": "npx",
      "args": [
        "mcp-remote@latest",
        "https://192.168.1.213:8444/mcp/sse",
        "--transport", "sse-only",
        "--header", "Authorization: Bearer your-secure-token-here"
      ]
    }
  }
}
```

**Result:** Additional authentication layer for shared MCP servers. Token rotation without user password changes.

---

## Security Checklist for Production

Before deploying an MCP server to production:

- [ ] **Generate unique encryption key** (not the default)
  ```bash
  python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```

- [ ] **Generate unique session secret**
  ```bash
  openssl rand -hex 32
  ```

- [ ] **Set server IP for certificate SANs**
  ```bash
  echo "CERT_SERVER_IP=your.server.ip" > .env
  ```

- [ ] **Change default admin password** immediately after first login

- [ ] **Keep edit mode disabled** unless actively making changes

- [ ] **Configure firewall rules**
  - Allow 7443 (Web UI) from trusted networks only
  - Allow 8444 (API/MCP) from Claude Desktop clients only
  - Block 15432 (PostgreSQL) from external access

- [ ] **Set up log rotation** for audit logs

- [ ] **Enable API token** for shared environments

- [ ] **Review audit logs** weekly for anomalies

- [ ] **Plan certificate rotation** before 365-day expiry

---

## The Bigger Picture

Securing an MCP server isn't just about protecting one tool. It's about establishing patterns for AI-to-infrastructure security that will become increasingly important as AI agents gain more autonomy.

The controls we implemented, HTTPS, RBAC, edit mode protection, audit logging, and encrypted credentials, aren't novel. They're established security practices applied to a new context. The challenge is recognizing that AI tooling needs the same rigor we apply to human-facing systems.

As MCP adoption grows, expect to see:
- Industry standards for MCP security configurations
- Compliance frameworks specifically addressing AI agent access
- More sophisticated audit requirements for AI operations

The organizations building secure MCP implementations now will be better positioned for that future.

---

## Resources

- [Nexus Dashboard MCP Server](https://github.com/beye91/nexus-dashboard-mcp) - Full implementation
- [Model Context Protocol Specification](https://modelcontextprotocol.io/) - Official MCP docs
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/) - API security reference
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework) - Security controls reference

---

## Implementation Summary

| Security Layer | Implementation | Purpose |
|---------------|----------------|---------|
| Transport | HTTPS with self-signed certs | Encrypt all communication |
| Operation Control | Edit mode + whitelist | Prevent unauthorized writes |
| Access Control | Multi-user RBAC | Least-privilege access |
| Credential Storage | Fernet encryption | Protect stored secrets |
| Audit | PostgreSQL logging | Forensic trail |
| Session | HttpOnly secure cookies | Prevent session theft |
| API Auth | Optional bearer token | Multi-tenant security |

---

*This document summarizes the security implementation of the Nexus Dashboard MCP Server. For deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md). For quick start, see [QUICKSTART.md](../QUICKSTART.md).*
