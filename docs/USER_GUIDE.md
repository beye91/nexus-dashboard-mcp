# Nexus Dashboard MCP Server - User Guide

## Table of Contents
1. [Overview](#overview)
2. [What is This Tool?](#what-is-this-tool)
3. [Key Features](#key-features)
4. [Getting Started](#getting-started)
5. [Web UI Guide](#web-ui-guide)
6. [System Health Monitoring](#system-health-monitoring)
7. [Security & Access Control](#security--access-control)
8. [Audit Logging](#audit-logging)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The **Nexus Dashboard MCP Server** is a Model Context Protocol (MCP) server that provides programmatic access to Cisco Nexus Dashboard APIs through Claude AI. It includes a comprehensive web-based management interface for configuration, monitoring, and auditing.

### What Does It Do?

This tool acts as a bridge between Claude AI and your Cisco Nexus Dashboard infrastructure, enabling:

- **AI-Powered Network Operations**: Use natural language to query and manage your network fabric
- **Centralized Management**: Single interface to manage multiple Nexus Dashboard clusters
- **Audit & Compliance**: Complete audit trail of all operations with client IP tracking
- **Security Controls**: Granular permission management and read-only mode
- **Health Monitoring**: Real-time status of all services and components

---

## What is This Tool?

### Architecture

```
┌─────────────┐
│   Claude    │  ← Natural language queries
│     AI      │
└──────┬──────┘
       │
       │ MCP Protocol
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
       │ Nexus Dashboard APIs
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

### Components

1. **MCP Server** (Port: stdio)
   - Implements Model Context Protocol
   - Loads 638 operations from Nexus Dashboard OpenAPI specs
   - Executes API calls to Nexus Dashboard clusters
   - Logs all operations to audit database

2. **Web API** (Port: 8002)
   - FastAPI REST API for web UI
   - Manages clusters, security, audit logs
   - Provides health monitoring endpoints

3. **Web UI** (Port: 7001)
   - Next.js React application
   - User-friendly interface for all features
   - Real-time health monitoring
   - Audit log viewer with export

4. **PostgreSQL Database** (Port: 15432)
   - Stores cluster configurations
   - Audit log persistence
   - Security settings
   - Encrypted credential storage

---

## Key Features

### 1. Multi-Cluster Management
- Connect to multiple Nexus Dashboard instances
- Encrypted credential storage (Fernet encryption)
- SSL verification options
- Test connectivity before saving

### 2. Security & Access Control
- **Edit Mode Toggle**: Enable/disable write operations globally
- **Operation Whitelist**: Specify which operations are allowed
- **Audit Logging**: Track every API call with full details
- **Client IP Tracking**: Identify source of all requests

### 3. Comprehensive Audit Trail
- Every operation logged with:
  - Timestamp
  - Cluster name and endpoint
  - HTTP method and path
  - Request/response bodies
  - Status codes and errors
  - **Client IP address** (identifies who made the request)
- CSV export for compliance reporting
- Filtering by cluster, method, status, date range

### 4. Real-Time Health Monitoring
- Overall system status (healthy/degraded/unhealthy)
- Service-level monitoring:
  - PostgreSQL database connectivity
  - Cluster configuration status
  - MCP server activity (operations in last 24h)
- Response time metrics
- Auto-refresh every 30 seconds

### 5. 638 Operations Available
Supports all Nexus Dashboard DCNM APIs including:
- **Manage API**: Fabrics, switches, VLANs, VRFs, networks, interfaces
- **Analyze API**: Telemetry, insights, anomalies, compliance
- **Infra API**: System health, licensing, user management
- **OneManage API**: Device inventory, topology

---

## Getting Started

### Prerequisites
- Docker and Docker Compose installed
- Cisco Nexus Dashboard cluster(s) accessible
- Admin credentials for Nexus Dashboard

### Quick Start

1. **Start the services**:
   ```bash
   docker-compose up -d
   ```

2. **Access the Web UI**:
   ```
   http://localhost:7001
   ```

3. **Add your first cluster**:
   - Navigate to **Clusters** page
   - Click "Add New Cluster"
   - Fill in details:
     - Name: `production` (friendly name)
     - URL: `https://nexus-dashboard.example.com` (your Nexus Dashboard IP)
     - Username: `admin`
     - Password: (your password)
     - SSL Verification: OFF (if using self-signed certs)
   - Click "Test Connection"
   - If successful, click "Create Cluster"

4. **Configure Security**:
   - Navigate to **Security** page
   - Toggle **Edit Mode** if you want to allow write operations
   - Add specific operations to **Allowed Operations** list (optional)
   - Click "Save Configuration"

5. **Use with Claude**:
   - Claude AI can now query your Nexus Dashboard
   - Example: "Show me all fabrics in my production cluster"
   - MCP Server will execute the API call and return results

---

## Web UI Guide

### Dashboard (Home Page)
- Quick overview of system status
- Recent activity summary
- Links to main features

### Clusters Page
**Purpose**: Manage Nexus Dashboard cluster connections

**Features**:
- View all configured clusters
- Add new clusters with test connectivity
- Edit existing cluster details
- Delete clusters
- Status indicators (active/inactive/error)

**Workflow**:
1. Click "Add New Cluster"
2. Enter cluster details
3. Test connection
4. Save cluster
5. Credentials are encrypted automatically

### Security Page
**Purpose**: Control what operations are allowed

**Edit Mode**:
- **OFF** (default): All operations are read-only
- **ON**: Write operations are allowed

**Allowed Operations**:
- Empty list = All operations allowed (when edit mode ON)
- Populated list = Only listed operations allowed
- Example operations:
  - `manage_createVlan`
  - `manage_deleteNetwork`
  - `analyze_getInsights`

**Workflow**:
1. Enable/disable edit mode using toggle
2. Add specific operations to whitelist
3. Click "Save Configuration"
4. Changes take effect within 30 seconds in MCP server

### Audit Logs Page
**Purpose**: View complete history of all API operations

**Table Columns**:
- **Timestamp**: When the operation occurred
- **Cluster**: Which cluster was accessed
- **Cluster Endpoint**: IP address/URL of the cluster
- **Client IP**: IP address of the client that made the request (identifies source)
- **Method**: HTTP method (GET, POST, PUT, DELETE, PATCH)
- **Endpoint**: API path that was called
- **Operation**: Operation ID from OpenAPI spec
- **Status**: HTTP status code (color-coded)
- **Error**: Error message if operation failed

**Filters**:
- Cluster Name
- HTTP Method
- Status Code
- Date Range (start/end)

**Features**:
- Pagination (50 items per page)
- Export to CSV
- Real-time updates

**Use Cases**:
- **Security Audits**: Track who did what and when
- **Troubleshooting**: Find failed operations and error messages
- **Compliance**: Export CSV reports for auditors
- **Bad Behavior Detection**: Filter by Client IP to identify problematic sources

### Health Page
**Purpose**: Monitor system health in real-time

**Overall Status**:
- **Healthy**: All services operational
- **Degraded**: Some services have warnings
- **Unhealthy**: Critical services down

**Service Cards**:
1. **PostgreSQL**
   - Status: healthy/unhealthy
   - Response time in milliseconds
   - Message: Connection status

2. **Cluster Configuration**
   - Status: healthy/degraded/unhealthy
   - Message: Number of clusters configured
   - Degra ded if no clusters

3. **MCP Server**
   - Status: healthy/degraded/unhealthy
   - Message: Operations count in last 24h
   - Degraded if no recent activity

**System Statistics**:
- Total Operations (all-time)
- Clusters Configured
- Audit Logs Count
- Security Mode (Edit Mode ON/Read-Only)

**Features**:
- Auto-refresh every 30 seconds (toggle on/off)
- Manual refresh button
- Last update timestamp

---

## System Health Monitoring

### How to Access
Navigate to: **http://localhost:7001/health**

Or click **Health** in the navigation bar

### What It Monitors

#### 1. PostgreSQL Database
- **Check**: Can we connect and execute queries?
- **Response Time**: How fast is the database?
- **Status**:
  - Healthy: Connection successful
  - Unhealthy: Cannot connect

#### 2. Cluster Configuration
- **Check**: Are clusters configured?
- **Status**:
  - Healthy: 1+ clusters configured
  - Degraded: No clusters configured
  - Unhealthy: Cannot query database

#### 3. MCP Server Activity
- **Check**: Are operations being executed?
- **Metric**: Count of operations in last 24 hours
- **Status**:
  - Healthy: Operations logged recently
  - Degraded: No recent operations
  - Unhealthy: Cannot check audit logs

### Interpreting Status

**Overall Status Logic**:
- **Healthy**: All services are healthy
- **Degraded**: At least one service degraded, none unhealthy
- **Unhealthy**: At least one service unhealthy

**Response Times**:
- < 100ms: Excellent
- 100-500ms: Good
- 500-1000ms: Acceptable
- \> 1000ms: Investigate (may indicate network issues)

---

## Security & Access Control

### Edit Mode

**Purpose**: Global write protection

**When to Enable**:
- During planned maintenance
- For configuration changes
- When allowing AI-assisted modifications

**When to Disable**:
- During production operations (safe mode)
- When only monitoring is needed
- To prevent accidental changes

**How It Works**:
1. Web UI sends edit mode state to Web API
2. Web API updates database
3. MCP Server polls database every 30 seconds
4. MCP Server blocks write operations when edit mode OFF

### Allowed Operations

**Purpose**: Fine-grained permission control

**Empty List** (default):
- When edit mode ON: All operations allowed
- When edit mode OFF: All operations blocked

**With Operations Listed**:
- Only listed operations are allowed
- All other operations are blocked
- Works independently of edit mode

**Example Scenarios**:

**Scenario 1: Read-Only Mode**
```
Edit Mode: OFF
Allowed Operations: []
Result: All operations blocked (read-only)
```

**Scenario 2: Full Access**
```
Edit Mode: ON
Allowed Operations: []
Result: All operations allowed
```

**Scenario 3: Limited Write Access**
```
Edit Mode: ON
Allowed Operations: [manage_createVlan, manage_deleteVlan]
Result: Only VLAN operations allowed
```

**Scenario 4: Specific Read Access**
```
Edit Mode: OFF
Allowed Operations: [analyze_getInsights]
Result: Only insights analysis allowed
```

---

## Audit Logging

### What Gets Logged?

**Every MCP operation** creates an audit log entry with:

| Field | Description | Example |
|-------|-------------|---------|
| Timestamp | When operation occurred | `2025-11-23 12:25:45` |
| Cluster ID | Database ID of cluster | `1` |
| Cluster Name | Friendly name | `production` |
| Cluster Endpoint | IP/URL of cluster | `https://nexus-dashboard.example.com` |
| Client IP | Source IP of request | `10.0.1.50` |
| User ID | (Future: username) | `null` |
| Operation ID | OpenAPI operation | `manage_createVlan` |
| HTTP Method | Request method | `POST` |
| Path | API endpoint path | `/api/dcnm/vlans` |
| Request Body | JSON payload | `{"vlanId": "100"}` |
| Response Status | HTTP status code | `201` |
| Response Body | API response | `{"success": true}` |
| Error Message | If failed | `Connection timeout` |

### Using Audit Logs

#### Security Audits
**Goal**: Track who did what

**Steps**:
1. Navigate to Audit Logs page
2. Filter by date range
3. Look at **Client IP** column to identify sources
4. Filter by specific IP if investigating bad behavior
5. Export to CSV for reporting

**Example**:
```
Find all operations from IP 10.0.1.50:
1. Note the Client IP: 10.0.1.50
2. Filter by date range
3. Review operations, methods, status codes
4. Check for unauthorized write operations
5. Export CSV for security team
```

#### Troubleshooting Failed Operations
**Goal**: Find why an operation failed

**Steps**:
1. Filter by **Status Code** >= 400
2. Look for specific **Operation ID**
3. Check **Error Message** column
4. Review **Request Body** to see what was sent
5. Check **Response Body** for API error details

#### Compliance Reporting
**Goal**: Generate audit reports

**Steps**:
1. Set date range (e.g., last month)
2. Apply any necessary filters
3. Click "Export to CSV"
4. CSV includes all columns:
   - ID, Cluster Name, Cluster URL
   - User ID, Operation ID
   - HTTP Method, Path
   - Response Status, Error Message
   - **Client IP** (identifies request source)
   - Timestamp

### Client IP Tracking

**Purpose**: Identify the source of API requests

**What It Shows**:
- IP address of the client that made the request
- Helps identify:
  - Which team members performed operations
  - Unauthorized access attempts
  - Patterns of bad behavior
  - Source of errors or misconfigurations

**Use Cases**:

**1. Security Investigation**
```
Scenario: Unauthorized VLAN deletion
1. Filter audit logs for deleteVlan operations
2. Check Client IP column
3. Identify IP: 10.0.2.99 (not from known subnet)
4. Block IP at firewall
5. Export logs as evidence
```

**2. Troubleshooting**
```
Scenario: Repeated failed logins
1. Filter by status 401 (Unauthorized)
2. Check Client IP to see if same source
3. If same IP, possible credential issue
4. If multiple IPs, possible auth server problem
```

**3. Usage Analytics**
```
Scenario: Track department API usage
1. Group audit logs by Client IP
2. Map IPs to departments:
   - 10.0.1.x = Network Team
   - 10.0.2.x = NOC
   - 10.0.3.x = Dev Team
3. Count operations per department
4. Identify heavy users
```

---

## Troubleshooting

### Services Not Starting

**Check Docker status**:
```bash
docker-compose ps
```

**Check logs**:
```bash
docker-compose logs postgres
docker-compose logs web-api
docker-compose logs web-ui
```

**Common Issues**:
- Port conflicts: Change ports in `docker-compose.yml`
- Out of memory: Increase Docker memory limit
- Database not ready: Web-api waits for healthy status

### Web UI Not Loading

**Verify containers are running**:
```bash
docker-compose ps
```

**Check web-ui logs**:
```bash
docker-compose logs web-ui
```

**Try rebuilding**:
```bash
docker-compose build web-ui
docker-compose up -d web-ui
```

### Cluster Connection Failed

**Test from command line**:
```bash
curl -k -u admin:password https://nexus-dashboard.example.com/apidocs/
```

**Common Issues**:
- Wrong URL: Verify IP and port
- SSL certificate: Disable SSL verification
- Firewall: Check network connectivity
- Credentials: Verify username/password

### Health Page Shows Degraded/Unhealthy

**Check service status**:
- **PostgreSQL**: Database connection issue
- **Cluster Configuration**: No clusters configured
- **MCP Server**: No recent operations

**Solutions**:
1. PostgreSQL unhealthy:
   ```bash
   docker-compose restart postgres
   docker-compose logs postgres
   ```

2. No clusters configured:
   - Go to Clusters page
   - Add at least one cluster

3. MCP Server degraded:
   - Make a test query through Claude
   - Check if MCP server is running:
     ```bash
     docker-compose ps mcp-server
     ```

### Audit Logs Missing Client IP

**Reason**: Client IP tracking was added recently. Existing logs don't have this field.

**Solution**:
- New operations will have client IP
- Old logs will show "-" in Client IP column
- Client IP is captured starting from November 23, 2025

---

## Ports Reference

| Service | Port | Purpose |
|---------|------|---------|
| Web UI | 7001 | Next.js web interface |
| Web API | 8002 | FastAPI REST API |
| PostgreSQL | 15432 | Database |
| MCP Server | stdio | Model Context Protocol (no port) |

---

## Environment Variables

### Required
- `ENCRYPTION_KEY`: Fernet encryption key for credentials
- `DB_PASSWORD`: PostgreSQL password

### Optional
- `NEXT_PUBLIC_API_URL`: Web UI API endpoint (default: http://localhost:8002)

---

## Database Schema

### Tables

**clusters**:
- Stores Nexus Dashboard cluster configurations
- Credentials encrypted with Fernet

**security_config**:
- Edit mode setting
- Allowed operations list
- Audit logging toggle

**audit_log**:
- Complete operation history
- Includes cluster info, client IP, request/response

**api_endpoints**:
- Registry of available operations from OpenAPI specs

---

## Support & Documentation

### File Locations
- **Main README**: `/README.md`
- **Quick Start**: `/docs/QUICKSTART.md`
- **How It Works**: `/docs/HOW_IT_WORKS.md`
- **Integration Summary**: `/docs/COMPLETE_INTEGRATION_SUMMARY.md`
- **This Guide**: `/docs/USER_GUIDE.md`

### Getting Help
- Check health page for service status
- Review audit logs for error messages
- Check Docker logs: `docker-compose logs [service]`
- Verify cluster connectivity with test function

---

## Best Practices

### Security
1. Keep edit mode OFF when not needed
2. Use allowed operations for fine-grained control
3. Review audit logs regularly
4. Monitor client IPs for unauthorized access
5. Rotate credentials periodically

### Performance
1. Monitor database response times in health page
2. Clean old audit logs if database grows large
3. Limit date ranges in audit log filters
4. Use pagination for large result sets

### Operations
1. Test cluster connectivity before saving
2. Use meaningful cluster names
3. Export audit logs monthly for compliance
4. Check health page before making changes
5. Keep backups of PostgreSQL data volume

---

**Last Updated**: November 23, 2025
**Version**: 1.0.0
