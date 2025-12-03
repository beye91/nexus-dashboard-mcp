# Nexus Dashboard MCP Server

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](docker compose.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](requirements.txt)
[![Next.js](https://img.shields.io/badge/Next.js-16.0-black?logo=next.js&logoColor=white)](web-ui/package.json)

A comprehensive Model Context Protocol (MCP) server for Cisco Nexus Dashboard, enabling AI agents like Claude to interact with Nexus Dashboard APIs for intelligent network automation and management.

## 🌟 Features

### Core Capabilities
- **🔌 Complete API Coverage**: Access to 638+ operations across 5 Nexus Dashboard APIs
  - Manage API (146 endpoints): Fabrics, switches, VLANs, VRFs, networks, interfaces
  - Analyze API: Telemetry, insights, anomalies, compliance
  - Infrastructure API: System health, licensing, user management
  - OneManage API: Device inventory, topology
  - Orchestration API: Workflows and automation

- **🔒 Security First**:
  - Read-only mode by default with explicit edit mode enablement
  - Fernet-encrypted credential storage
  - Complete audit logging with client IP tracking
  - Granular operation whitelisting

- **🎯 Web Management UI**:
  - Next.js-based management interface
  - Real-time system health monitoring
  - Audit log viewer with CSV export
  - Cluster management with connection testing
  - Security configuration dashboard

- **📊 Enterprise Ready**:
  - PostgreSQL database for persistence
  - Docker-based deployment
  - Horizontal scalability
  - Complete audit trail for compliance

## 📸 Screenshots

### Web Management Interface
The web UI provides comprehensive management capabilities for the MCP server:

- **Dashboard**: Real-time system statistics and health overview
- **Cluster Management**: Configure multiple Nexus Dashboard connections
- **Security Settings**: Control edit mode and operation whitelisting
- **Audit Logs**: Complete operation history with filtering and export
- **Health Monitoring**: Service status and performance metrics

## 🚀 Quick Start

### Prerequisites

- **Docker** 20.10+ and Docker Compose 2.0+
- **Access** to a Cisco Nexus Dashboard cluster
- **Python** 3.11+ (for local development)
- **Node.js** 20+ (for web UI development)

### 1. Clone and Start

```bash
git clone https://github.com/beye91/nexus-dashboard-mcp.git
cd nexus-dashboard-mcp
docker compose up -d
```

That's it! The application starts with sensible defaults for development and testing.

```bash
# View logs
docker compose logs -f

# Check status
docker compose ps
```

### 2. Configure Environment (Optional)

For production deployments, create a `.env` file to override defaults:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Nexus Dashboard Configuration (configure via Web UI or here)
NEXUS_CLUSTER_URL=https://nexus-dashboard.example.com
NEXUS_USERNAME=admin
NEXUS_PASSWORD=YourPassword

# Security (generate unique keys for production)
ENCRYPTION_KEY=your-unique-fernet-key
SESSION_SECRET_KEY=your-random-secret-key
```

**Generate Encryption Key for Production:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

The deployment includes:
- **PostgreSQL** (port 15432): Database for credentials and audit logs
- **Web API** (port 8002): FastAPI REST API for management
- **Web UI** (port 7001): Next.js management interface
- **MCP Server** (stdio): Model Context Protocol server for Claude

### 3. Access the Web UI

Open your browser and navigate to:
```
http://localhost:7001
```

**First Steps in Web UI:**
1. Navigate to **Clusters** page
2. Click "Add New Cluster"
3. Enter your Nexus Dashboard details
4. Click "Test Connection" to verify
5. Save the cluster configuration

### 4. Configure Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

#### Local Deployment (same machine as Docker)

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

#### Remote Deployment (MCP server on different host)

For connecting to an MCP server running on a remote host, use the HTTP/SSE transport:

```json
{
  "mcpServers": {
    "nexus-dashboard": {
      "url": "http://YOUR_SERVER_IP:8002/mcp/sse"
    }
  }
}
```

Replace `YOUR_SERVER_IP` with your server's IP address (e.g., `192.168.1.213`).

**Optional: Secure with API Token**

Set the `MCP_API_TOKEN` environment variable in your deployment to require authentication:

```env
MCP_API_TOKEN=your-secure-token-here
```

Then configure Claude Desktop with the token:

```json
{
  "mcpServers": {
    "nexus-dashboard": {
      "url": "http://YOUR_SERVER_IP:8002/mcp/sse",
      "headers": {
        "Authorization": "Bearer your-secure-token-here"
      }
    }
  }
}
```

Restart Claude Desktop, and you'll see the Nexus Dashboard tools available!

## 📖 Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Get up and running in 5 minutes
- **[Architecture Overview](docs/ARCHITECTURE.md)** - System design and components
- **[User Guide](docs/USER_GUIDE.md)** - Comprehensive usage documentation
- **[Web UI Guide](docs/WEB_UI_GUIDE.md)** - Managing the system via web interface
- **[Claude Desktop Setup](docs/CLAUDE_DESKTOP_SETUP.md)** - Detailed Claude integration
- **[API Reference](docs/API_PATHS.md)** - Available API endpoints
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment recommendations
- **[Contributing](CONTRIBUTING.md)** - How to contribute to this project

## 🏗️ Architecture

```
┌─────────────┐
│   Claude    │  ← Natural language queries
│     AI      │
└──────┬──────┘
       │
       │ MCP Protocol (stdio)
       │
┌──────┴──────────────────────────────────┐
│    Nexus Dashboard MCP Server           │
│                                          │
│  ┌────────────┐      ┌────────────┐    │
│  │ MCP Server │◄────►│  Web API   │    │
│  │  (stdio)   │      │ (REST API) │    │
│  └──────┬─────┘      └─────┬──────┘    │
│         │                   │           │
│         │          ┌────────┴────────┐  │
│         │          │   PostgreSQL    │  │
│         │          │    Database     │  │
│         │          └─────────────────┘  │
│         │                               │
│  ┌──────┴──────────┐                   │
│  │   Web UI        │                   │
│  │  (Next.js)      │                   │
│  └─────────────────┘                   │
└─────────────────────────────────────────┘
       │
       │ Nexus Dashboard APIs (HTTPS)
       │
┌──────┴──────────────────────────────────┐
│    Cisco Nexus Dashboard Clusters       │
│                                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │ Cluster │  │ Cluster │  │ Cluster │ │
│  │   #1    │  │   #2    │  │   #3    │ │
│  └─────────┘  └─────────┘  └─────────┘ │
└──────────────────────────────────────────┘
```

## 🛠️ Technology Stack

**Backend:**
- **Python 3.11+** - Core programming language
- **FastMCP** - Model Context Protocol framework
- **FastAPI** - Web API framework
- **SQLAlchemy** - Database ORM
- **PostgreSQL** - Data persistence
- **Cryptography** - Fernet encryption for credentials

**Frontend:**
- **Next.js 16** - React framework with Turbopack
- **React 19** - UI library
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first styling
- **Axios** - HTTP client

**DevOps:**
- **Docker & Docker Compose** - Containerization
- **GitHub Actions** - CI/CD (coming soon)

## 📋 Available Operations

The server provides access to **638 operations** across multiple Nexus Dashboard APIs:

### Manage API (146 operations)
- Fabric management (create, update, delete fabrics)
- Switch management (add, remove, configure switches)
- VLAN management (create, update, delete VLANs)
- VRF management (create, update, delete VRFs)
- Network management (create, update, delete networks)
- Interface management (configure interfaces)
- Policy management (apply policies)

### Analyze API
- Telemetry data retrieval
- Insights and anomalies
- Compliance reporting
- Health scores

### Infrastructure API
- System health monitoring
- License management
- User and role management
- Backup and restore

### OneManage API
- Device inventory
- Topology discovery
- Device management

See [AVAILABLE_OPERATIONS.md](docs/AVAILABLE_OPERATIONS.md) for the complete list.

## 🔐 Security

### Security Features

1. **Read-Only by Default**: All operations are read-only unless explicitly enabled
2. **Edit Mode Control**: Global toggle for write operations
3. **Operation Whitelisting**: Granular control over allowed operations
4. **Encrypted Credentials**: Fernet encryption for all stored passwords
5. **Complete Audit Trail**: Every operation logged with timestamp, user, and details
6. **Client IP Tracking**: Identify source of all API requests

### Security Best Practices

- Keep `EDIT_MODE_ENABLED=false` in production
- Use strong encryption keys (32+ characters)
- Regularly rotate credentials
- Review audit logs for unauthorized activity
- Use SSL/TLS for Nexus Dashboard connections
- Limit network access to the MCP server

### Reporting Security Issues

Please report security vulnerabilities to the maintainers privately. See [SECURITY.md](SECURITY.md) for details.

## 📊 Monitoring & Observability

### Health Monitoring

Access the health dashboard at `http://localhost:7001/health` to monitor:

- **PostgreSQL Database**: Connection status and response time
- **Cluster Connectivity**: Number of configured clusters
- **MCP Server Activity**: Operations processed in last 24h
- **Overall System Health**: Aggregated health status

### Audit Logging

All operations are logged to PostgreSQL with:
- Timestamp
- Cluster name and endpoint
- Client IP address
- HTTP method and path
- Request and response bodies
- Status codes and errors

Export audit logs to CSV for compliance reporting.

## 🧪 Development

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/beye91/nexus-dashboard-mcp.git
cd nexus-dashboard-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install web-ui dependencies
cd web-ui
npm install
cd ..

# Start development environment
docker compose up postgres  # Start database only
python src/main.py  # Run MCP server locally
cd web-ui && npm run dev  # Run web UI in dev mode
```

### Running Tests

```bash
# Python tests
pytest

# Web UI tests
cd web-ui
npm test
```

### Code Style

We use:
- **Black** for Python code formatting
- **Flake8** for Python linting
- **ESLint** for TypeScript/React linting
- **Prettier** for code formatting

## 🗺️ Roadmap

See [ROADMAP.md](docs/ROADMAP.md) for detailed project roadmap.

**Upcoming Features:**
- [ ] GitHub Actions CI/CD pipeline
- [ ] Additional API support (multi-API loading)
- [ ] Advanced filtering in audit logs
- [ ] GraphQL API for web UI
- [ ] Webhooks for event notifications
- [ ] Multi-user authentication
- [ ] Role-based access control (RBAC)
- [ ] Prometheus metrics export

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on:

- Code of Conduct
- Development workflow
- Pull request process
- Coding standards

## 📝 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Anthropic** - For the Claude AI platform and MCP protocol
- **Cisco** - For Nexus Dashboard APIs
- **FastMCP** - For the excellent MCP framework
- **Community Contributors** - Thank you for your contributions!

## 📞 Support

- **Documentation**: [GitHub Wiki](https://github.com/beye91/nexus-dashboard-mcp/wiki)
- **Issues**: [GitHub Issues](https://github.com/beye91/nexus-dashboard-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/beye91/nexus-dashboard-mcp/discussions)

## ⭐ Star History

If you find this project useful, please consider giving it a star!

---

**Made with ❤️ for network automation**
