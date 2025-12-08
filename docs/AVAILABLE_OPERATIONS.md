# Available Operations - Nexus Dashboard Manage API

**Total Operations**: 202
**Status**: All operations available as MCP tools

## Operation Summary by HTTP Method

| Method | Count | Access |
|--------|-------|--------|
| GET    | 85    | ✅ Always Available (Read-Only) |
| POST   | 78    | 🔒 Requires Edit Mode |
| PUT    | 20    | 🔒 Requires Edit Mode |
| DELETE | 19    | 🔒 Requires Edit Mode |

## Key Operation Categories

### Fabrics (Core Operations)
**Total**: 5 operations

| Operation | Method | Path | Description |
|-----------|--------|------|-------------|
| `manage_listFabrics` | GET | `/fabrics` | Retrieve all fabrics |
| `manage_createFabric` | POST | `/fabrics` | Create new fabric |
| `manage_getFabricDetails` | GET | `/fabrics/{fabricName}` | Get fabric details |
| `manage_updatefabricDetails` | PUT | `/fabrics/{fabricName}` | Update fabric |
| `manage_deleteFabric` | DELETE | `/fabrics/{fabricName}` | Delete fabric |

### Switches (Primary Device Operations)
**Total**: 14 operations

| Operation | Method | Path | Description |
|-----------|--------|------|-------------|
| `manage_listFabricSwitches` | GET | `/fabrics/{fabricName}/switches` | List all switches in fabric |
| `manage_createFabricSwitches` | POST | `/fabrics/{fabricName}/switches` | Add switches to fabric |
| `manage_getFabricSwitchesSummary` | GET | `/fabrics/{fabricName}/switches/summary` | Get switches summary |
| `manage_getFabricSwitch` | GET | `/fabrics/{fabricName}/switches/{switchId}` | Get switch details |
| `manage_deleteFabricSwitch` | DELETE | `/fabrics/{fabricName}/switches/{switchId}` | Remove switch |
| `manage_getSwitchInterfacesOverview` | GET | `/fabrics/{fabricName}/switches/{switchId}/interfacesOverview` | Get interfaces overview |
| `manage_getSwitchConfigurationDiff` | GET | `/fabrics/{fabricName}/switches/{switchId}/diff` | Get config differences |
| `manage_executeRediscoverSwitches` | POST | `/fabrics/{fabricName}/switchActions/rediscover` | Rediscover switches |
| `manage_executeReloadSwitches` | POST | `/fabrics/{fabricName}/switchActions/reload` | Reload switches |
| `manage_deleteFabricSwitches` | POST | `/fabrics/{fabricName}/switchActions/remove` | Remove multiple switches |
| `manage_executeChangeCredentialSwitches` | POST | `/fabrics/{fabricName}/switchActions/changeDiscoveryCredential` | Change switch credentials |
| `manage_executeChangeSwitchIpCollection` | POST | `/fabrics/{fabricName}/switchActions/changeIpCollection` | Change IP collection |
| `manage_executeMoveNeighborSwitch` | POST | `/fabrics/{fabricName}/switchActions/moveNeighbor` | Move neighbor switch |
| `manage_executeSwitchConfigurationPreview` | POST | `/fabrics/{fabricName}/switchActions/preview` | Preview config changes |

### Interfaces
**Total**: 11 operations

| Operation | Method | Path | Description |
|-----------|--------|------|-------------|
| `manage_listInterfaces` | GET | `/fabrics/{fabricName}/interfaces` | List all interfaces |
| `manage_createInterfaces` | POST | `/fabrics/{fabricName}/interfaces` | Create interfaces |
| `manage_getInterfacesSummary` | GET | `/fabrics/{fabricName}/interfaces/summary` | Get interfaces summary |
| `manage_getInterface` | GET | `/fabrics/{fabricName}/interfaces/{interfaceId}` | Get interface details |
| `manage_replaceInterface` | PUT | `/fabrics/{fabricName}/interfaces/{interfaceId}` | Update interface |
| `manage_deleteInterface` | DELETE | `/fabrics/{fabricName}/interfaces/{interfaceId}` | Delete interface |

### Networks
**Total**: 8 operations

| Operation | Method | Path | Description |
|-----------|--------|------|-------------|
| `manage_listNetworks` | GET | `/fabrics/{fabricName}/networks` | List all networks |
| `manage_createNetworks` | POST | `/fabrics/{fabricName}/networks` | Create networks |
| `manage_getNetworksSummary` | GET | `/fabrics/{fabricName}/networks/summary` | Get networks summary |
| `manage_getNetwork` | GET | `/fabrics/{fabricName}/networks/{networkId}` | Get network details |
| `manage_replaceNetwork` | PUT | `/fabrics/{fabricName}/networks/{networkId}` | Update network |
| `manage_deleteNetwork` | DELETE | `/fabrics/{fabricName}/networks/{networkId}` | Delete network |

### VRFs (Virtual Routing and Forwarding)
**Total**: 8 operations

| Operation | Method | Path | Description |
|-----------|--------|------|-------------|
| `manage_listVrfs` | GET | `/fabrics/{fabricName}/vrfs` | List all VRFs |
| `manage_createVrfs` | POST | `/fabrics/{fabricName}/vrfs` | Create VRFs |
| `manage_getVrfsSummary` | GET | `/fabrics/{fabricName}/vrfs/summary` | Get VRFs summary |
| `manage_getVrf` | GET | `/fabrics/{fabricName}/vrfs/{vrfId}` | Get VRF details |
| `manage_replaceVrf` | PUT | `/fabrics/{fabricName}/vrfs/{vrfId}` | Update VRF |
| `manage_deleteVrf` | DELETE | `/fabrics/{fabricName}/vrfs/{vrfId}` | Delete VRF |

### Anomalies and Compliance
**Total**: 27 operations

| Operation | Method | Path | Description |
|-----------|--------|------|-------------|
| `manage_listComplianceAnomalyRules` | GET | `/anomalyRules/complianceRules` | List compliance rules |
| `manage_createComplianceAnomalyRule` | POST | `/anomalyRules/complianceRules` | Create compliance rule |
| `manage_getComplianceAnomalyRule` | GET | `/anomalyRules/complianceRules/{ruleId}` | Get rule details |
| `manage_listAnomalies` | GET | `/fabrics/{fabricName}/anomalies` | List fabric anomalies |

### Templates
**Total**: 8 operations

| Operation | Method | Path | Description |
|-----------|--------|------|-------------|
| `manage_listTemplates` | GET | `/fabrics/{fabricName}/templates` | List all templates |
| `manage_createTemplates` | POST | `/fabrics/{fabricName}/templates` | Create templates |
| `manage_getTemplate` | GET | `/fabrics/{fabricName}/templates/{templateId}` | Get template details |
| `manage_replaceTemplate` | PUT | `/fabrics/{fabricName}/templates/{templateId}` | Update template |
| `manage_deleteTemplate` | DELETE | `/fabrics/{fabricName}/templates/{templateId}` | Delete template |

### Policies
**Total**: 20+ operations

| Operation | Method | Path | Description |
|-----------|--------|------|-------------|
| `manage_listPolicies` | GET | `/fabrics/{fabricName}/policies` | List all policies |
| `manage_createPolicies` | POST | `/fabrics/{fabricName}/policies` | Create policies |
| `manage_getPolicy` | GET | `/fabrics/{fabricName}/policies/{policyId}` | Get policy details |
| `manage_replacePolicy` | PUT | `/fabrics/{fabricName}/policies/{policyId}` | Update policy |
| `manage_deletePolicy` | DELETE | `/fabrics/{fabricName}/policies/{policyId}` | Delete policy |

### Access Control Lists (ACLs)
**Total**: 7 operations

| Operation | Method | Path | Description |
|-----------|--------|------|-------------|
| `manage_listAccessControlLists` | GET | `/fabrics/{fabricName}/accessControlLists` | List ACLs |
| `manage_createAccessControlLists` | POST | `/fabrics/{fabricName}/accessControlLists` | Create ACLs |
| `manage_getAccessControlListsSummary` | GET | `/fabrics/{fabricName}/accessControlListsSummary` | Get ACL summary |

### Credentials
**Total**: 11 operations

| Operation | Method | Path | Description |
|-----------|--------|------|-------------|
| `manage_listSwitchCredentials` | GET | `/credentials/switches` | List switch credentials |
| `manage_createSwitchCredentials` | POST | `/credentials/switches` | Create switch credentials |
| `manage_getDefaultSwitchCredentials` | GET | `/credentials/defaultSwitchCredentials` | Get default credentials |
| `manage_createDefaultSwitchCredentials` | POST | `/credentials/defaultSwitchCredentials` | Set default credentials |

### Deployment and Configuration
**Total**: 15+ operations

| Operation | Method | Path | Description |
|-----------|--------|------|-------------|
| `manage_executeDeployConfiguration` | POST | `/fabrics/{fabricName}/actions/deployConfiguration` | Deploy configuration |
| `manage_executeSaveAndDeployConfiguration` | POST | `/fabrics/{fabricName}/actions/saveAndDeployConfiguration` | Save and deploy |
| `manage_getFabricDeploymentFreezeMode` | GET | `/fabrics/{fabricName}/deploymentFreeze` | Get deployment freeze status |
| `manage_executeRedeployFabrics` | POST | `/fabricActions/redeploy` | Redeploy fabrics |

### Smart Switches (DPU Operations)
**Total**: 8 operations

| Operation | Method | Path | Description |
|-----------|--------|------|-------------|
| `manage_getSmartSwitchDpus` | GET | `/fabrics/{fabricName}/smartSwitch/{switchId}/dpus` | Get DPUs |
| `manage_getSmartSwitchDpusSummary` | GET | `/fabrics/{fabricName}/smartSwitch/{switchId}/dpus/summary` | Get DPU summary |
| `manage_executeSmartSwitchOnboarding` | POST | `/fabrics/{fabricName}/smartSwitches/actions/updateSecureTenant` | Onboard smart switch |
| `manage_executeSmartSwitchDeboarding` | DELETE | `/fabrics/{fabricName}/smartSwitches/{switchId}/actions/deboard` | Deboard smart switch |

## Usage Examples

### Example 1: List All Switches in a Fabric
```
"Show me all switches in fabric 'Production-DC1'"
```
This uses: `manage_listFabricSwitches` (GET /fabrics/{fabricName}/switches)

### Example 2: Get Switch Details
```
"Get details for switch with ID 'FOC1234X567' in fabric 'Production-DC1'"
```
This uses: `manage_getFabricSwitch` (GET /fabrics/{fabricName}/switches/{switchId})

### Example 3: List Networks
```
"List all networks in fabric 'Production-DC1'"
```
This uses: `manage_listNetworks` (GET /fabrics/{fabricName}/networks)

### Example 4: Get Anomalies
```
"Show me recent anomalies in fabric 'Production-DC1'"
```
This uses: `manage_listAnomalies` (GET /fabrics/{fabricName}/anomalies)

### Example 5: View Templates
```
"List all configuration templates in fabric 'Production-DC1'"
```
This uses: `manage_listTemplates` (GET /fabrics/{fabricName}/templates)

## Tool Name Format

All operations are exposed as MCP tools with the naming format:
- **Format**: `manage_{operation_id}`
- **Example**: `manage_listFabricSwitches`
- **Truncation**: If name exceeds 64 chars, uses just `operation_id`

## Read-Only vs Edit Mode

### Read-Only Mode (Default)
- ✅ All **GET** operations available (85 operations)
- ❌ POST/PUT/DELETE operations blocked
- Returns permission error with edit mode requirement

### Edit Mode (EDIT_MODE_ENABLED=true)
- ✅ All **GET** operations available
- ✅ All **POST** operations available (78 operations)
- ✅ All **PUT** operations available (20 operations)
- ✅ All **DELETE** operations available (19 operations)

## Complete Operation List

To see all 202 operations with full details, use:

```bash
docker exec -i nexus-mcp-server python -c "
import sys
sys.path.insert(0, '/app')
from src.core.api_loader import APILoader

loader = APILoader()
spec = loader.load_openapi_spec('nexus_dashboard_manage.json')
operations = loader.list_operations(spec)

for op in operations:
    print(f'{op[\"method\"]:6s} {op[\"path\"]:60s} {op[\"operation_id\"]}')
"
```

## API Documentation

For detailed information about each operation:
- **OpenAPI Spec**: `openapi_specs/nexus_dashboard_manage.json`
- **Cisco Documentation**: https://developer.cisco.com/docs/nexus-dashboard/

---

**Last Updated**: November 23, 2025
**API Version**: Nexus Dashboard Manage v1.0.130
**Status**: All 202 operations available and tested
