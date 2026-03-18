-- Migration 009: Seed built-in troubleshooting workflows and use cases
-- Version: 009
-- Date: 2026-03-18
-- Description: Seeds 10 practical workflows with steps and 8 use cases for guided troubleshooting

-- ============================================================================
-- WORKFLOWS
-- ============================================================================

INSERT INTO workflows (name, display_name, description, problem_statement, use_case_tags, is_active, priority)
VALUES
    (
        'endpoint_unreachable',
        'Endpoint Unreachable',
        'Diagnose why a VM or host cannot be reached from the network. Walks through endpoint lookup, history, anomaly detection, interface checks, and path tracing.',
        'A VM or endpoint is not reachable from the network.',
        '["troubleshooting", "connectivity", "endpoint"]',
        TRUE, 100
    ),
    (
        'duplicate_ip_detection',
        'Duplicate IP Address Detection',
        'Identify and resolve duplicate IP address conflicts causing connectivity issues. Locates conflicting endpoints and provides resolution guidance.',
        'Two or more hosts share the same IP address causing connectivity issues.',
        '["troubleshooting", "ip", "duplicate", "endpoint"]',
        TRUE, 95
    ),
    (
        'fabric_health_assessment',
        'Fabric Health Assessment',
        'Proactive health check across the entire fabric. Reviews health scores, anomalies, advisories, and switch status for early issue detection.',
        'General fabric health check, proactive monitoring.',
        '["monitoring", "health", "proactive"]',
        TRUE, 90
    ),
    (
        'interface_troubleshooting',
        'Interface Troubleshooting',
        'Diagnose interface issues including link down, flapping, errors, and congestion. Checks counters, statistics, and related anomalies.',
        'Interface is down, flapping, or showing errors.',
        '["troubleshooting", "interface", "errors"]',
        TRUE, 85
    ),
    (
        'bgp_routing_investigation',
        'BGP/Routing Problem Investigation',
        'Investigate routing problems including missing routes, BGP neighbor failures, and unexpected routing behavior. Checks neighbors, tables, and route churn.',
        'Routes missing, BGP neighbor down, unexpected routing behavior.',
        '["troubleshooting", "routing", "bgp", "l3"]',
        TRUE, 80
    ),
    (
        'flow_path_analysis',
        'Flow Path Analysis',
        'Trace and analyze the traffic path between two endpoints. Creates troubleshoot jobs, visualizes topology, and checks flow statistics.',
        'Traffic between two endpoints is broken or taking wrong path.',
        '["troubleshooting", "flow", "path", "connectivity"]',
        TRUE, 75
    ),
    (
        'configuration_compliance_check',
        'Configuration Compliance Check',
        'Verify fabric configuration matches intended state. Reviews compliance summaries, violations, pending changes, and config drift.',
        'Verify fabric configuration matches intended state.',
        '["compliance", "configuration", "drift"]',
        TRUE, 70
    ),
    (
        'advisory_alert_triage',
        'Advisory & Alert Triage',
        'Prioritize and resolve multiple advisories and alerts. Reviews severity, trends, recommendations, and software upgrade options.',
        'Multiple advisories/alerts to prioritize and resolve.',
        '["operations", "advisories", "alerts"]',
        TRUE, 65
    ),
    (
        'node_switch_health',
        'Node/Switch Health Investigation',
        'Investigate an unhealthy or unresponsive switch. Checks health overview, configuration, anomalies, infrastructure status, and cluster health.',
        'A switch or node appears unhealthy or unresponsive.',
        '["troubleshooting", "switch", "node", "health"]',
        TRUE, 60
    ),
    (
        'multicast_troubleshooting',
        'Multicast Troubleshooting',
        'Diagnose multicast delivery issues including IGMP and PIM problems. Checks routes, sources, receivers, group membership, and neighbor adjacency.',
        'Multicast traffic not reaching receivers, IGMP issues.',
        '["troubleshooting", "multicast", "igmp", "pim"]',
        TRUE, 55
    )
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- WORKFLOW STEPS
-- ============================================================================

-- Helper: get workflow IDs by name for FK references
-- We use subqueries to keep this idempotent

-- 1. Endpoint Unreachable
INSERT INTO workflow_steps (workflow_id, step_order, operation_name, description, expected_output, optional)
SELECT w.id, v.step_order, v.operation_name, v.description, v.expected_output, v.optional
FROM workflows w
CROSS JOIN (VALUES
    (1, 'analyze_listEndpointsDetails', 'Find the endpoint by IP or MAC address and confirm it exists in the fabric', 'Endpoint details including leaf, EPG, and interface attachment', FALSE),
    (2, 'analyze_listEndpointsHistory', 'Check if the endpoint recently moved, flapped, or disappeared', 'History of endpoint events with timestamps', FALSE),
    (3, 'analyze_listEndpointsAnomalies', 'Check for active anomalies affecting this endpoint', 'List of anomalies related to the endpoint', FALSE),
    (4, 'analyze_getAnomalyRecommendations', 'Get fix recommendations if an anomaly was found in the previous step', 'Recommended remediation actions', TRUE),
    (5, 'analyze_listFabricInterfaces', 'Check the status of the interface where the endpoint is attached', 'Interface operational status, speed, and errors', FALSE),
    (6, 'analyze_getFlowTopology', 'Trace the connectivity path to the endpoint through the fabric', 'Topology visualization of the path', FALSE),
    (7, 'analyze_getHealthSummary', 'Check overall fabric health for broader issues that may affect connectivity', 'Fabric health score and top-level status', TRUE)
) AS v(step_order, operation_name, description, expected_output, optional)
WHERE w.name = 'endpoint_unreachable'
AND NOT EXISTS (
    SELECT 1 FROM workflow_steps ws WHERE ws.workflow_id = w.id AND ws.step_order = v.step_order
);

-- 2. Duplicate IP Address Detection
INSERT INTO workflow_steps (workflow_id, step_order, operation_name, description, expected_output, optional)
SELECT w.id, v.step_order, v.operation_name, v.description, v.expected_output, v.optional
FROM workflows w
CROSS JOIN (VALUES
    (1, 'analyze_listEndpointsDuplicateIps', 'List all duplicate IP addresses detected in the fabric', 'List of IPs with multiple MAC/endpoint bindings', FALSE),
    (2, 'analyze_listEndpointsDetails', 'Get details of the conflicting endpoints (MAC, leaf, EPG)', 'Full endpoint details for each conflicting entry', FALSE),
    (3, 'analyze_listEndpointsHistory', 'Track when the duplicate entries first appeared', 'Timeline of endpoint learn/move events', FALSE),
    (4, 'analyze_getAnomaliesSummary', 'Check for IP-related anomalies in the system', 'Anomaly counts by category and severity', FALSE),
    (5, 'analyze_getAnomalyRecommendations', 'Get resolution guidance for the duplicate IP anomaly', 'Recommended steps to resolve the conflict', FALSE)
) AS v(step_order, operation_name, description, expected_output, optional)
WHERE w.name = 'duplicate_ip_detection'
AND NOT EXISTS (
    SELECT 1 FROM workflow_steps ws WHERE ws.workflow_id = w.id AND ws.step_order = v.step_order
);

-- 3. Fabric Health Assessment
INSERT INTO workflow_steps (workflow_id, step_order, operation_name, description, expected_output, optional)
SELECT w.id, v.step_order, v.operation_name, v.description, v.expected_output, v.optional
FROM workflows w
CROSS JOIN (VALUES
    (1, 'analyze_getHealthSummary', 'Get overall fabric health score and status', 'Health score breakdown by category', FALSE),
    (2, 'analyze_getAnomaliesSummary', 'Review active anomalies broken down by severity', 'Anomaly counts: critical, major, minor, warning', FALSE),
    (3, 'analyze_getAnomaliesTopNodes', 'Identify nodes with the most anomalies', 'Ranked list of nodes by anomaly count', FALSE),
    (4, 'analyze_getAdvisoriesSummary', 'Review outstanding advisories (PSIRTs, field notices, EOL)', 'Advisory counts by type and severity', FALSE),
    (5, 'analyze_listSwitchesSummary', 'Check switch health overview across the fabric', 'Switch status summary with health indicators', FALSE),
    (6, 'analyze_listFabricsSummary', 'Get per-fabric status for multi-fabric environments', 'Fabric-level health and connectivity status', TRUE)
) AS v(step_order, operation_name, description, expected_output, optional)
WHERE w.name = 'fabric_health_assessment'
AND NOT EXISTS (
    SELECT 1 FROM workflow_steps ws WHERE ws.workflow_id = w.id AND ws.step_order = v.step_order
);

-- 4. Interface Troubleshooting
INSERT INTO workflow_steps (workflow_id, step_order, operation_name, description, expected_output, optional)
SELECT w.id, v.step_order, v.operation_name, v.description, v.expected_output, v.optional
FROM workflows w
CROSS JOIN (VALUES
    (1, 'analyze_listFabricInterfaces', 'Find the interface and check its operational status', 'Interface admin/oper state, speed, type', FALSE),
    (2, 'analyze_listInterfacesDetails', 'Get detailed configuration and error counters for the interface', 'Detailed counters: CRC, input/output errors, resets', FALSE),
    (3, 'analyze_listFabricInterfacesStatistics', 'Check error rates, discard rates, and utilization over time', 'Time-series statistics for errors and throughput', FALSE),
    (4, 'analyze_listCongestionDetails', 'Check for congestion events on the interface or related links', 'Congestion events with timestamps and severity', TRUE),
    (5, 'analyze_getAnomaliesSummary', 'Check for interface-related anomalies in the system', 'Anomalies filtered by interface category', FALSE),
    (6, 'analyze_getAnomalyRecommendations', 'Get fix recommendations for any detected interface anomalies', 'Recommended actions to resolve interface issues', TRUE)
) AS v(step_order, operation_name, description, expected_output, optional)
WHERE w.name = 'interface_troubleshooting'
AND NOT EXISTS (
    SELECT 1 FROM workflow_steps ws WHERE ws.workflow_id = w.id AND ws.step_order = v.step_order
);

-- 5. BGP/Routing Problem Investigation
INSERT INTO workflow_steps (workflow_id, step_order, operation_name, description, expected_output, optional)
SELECT w.id, v.step_order, v.operation_name, v.description, v.expected_output, v.optional
FROM workflows w
CROSS JOIN (VALUES
    (1, 'analyze_listL3NeighborsSummary', 'Check BGP/OSPF neighbor status across the fabric', 'Neighbor state summary: established, idle, active', FALSE),
    (2, 'analyze_listL3NeighborsDetails', 'Get detailed neighbor information including timers and prefixes', 'Per-neighbor details: uptime, prefixes received/sent, state', FALSE),
    (3, 'analyze_listProtocolsDetails', 'Review protocol configuration for BGP/OSPF instances', 'Protocol config: AS numbers, router IDs, address families', FALSE),
    (4, 'analyze_listUrib', 'Check routing table entries for specific prefixes', 'Routing table entries with next-hops and metrics', FALSE),
    (5, 'analyze_getUribChangesCount', 'Check for recent route churn or instability', 'Route change counts over time', FALSE),
    (6, 'analyze_getUribNodeGraph', 'Visualize the routing path for a given prefix', 'Graph representation of route propagation', TRUE),
    (7, 'analyze_getAnomaliesSummary', 'Check for routing-related anomalies', 'Anomalies in routing category', FALSE)
) AS v(step_order, operation_name, description, expected_output, optional)
WHERE w.name = 'bgp_routing_investigation'
AND NOT EXISTS (
    SELECT 1 FROM workflow_steps ws WHERE ws.workflow_id = w.id AND ws.step_order = v.step_order
);

-- 6. Flow Path Analysis
INSERT INTO workflow_steps (workflow_id, step_order, operation_name, description, expected_output, optional)
SELECT w.id, v.step_order, v.operation_name, v.description, v.expected_output, v.optional
FROM workflows w
CROSS JOIN (VALUES
    (1, 'analyze_listEndpointsDetails', 'Verify that both source and destination endpoints exist in the fabric', 'Endpoint details for source and destination', FALSE),
    (2, 'analyze_createTroubleshootJob', 'Create a flow troubleshoot job for the source/destination pair', 'Job ID for the troubleshoot session', FALSE),
    (3, 'analyze_getFlowTroubleshootJob', 'Retrieve the troubleshoot job results and analysis', 'Troubleshoot findings: drops, misconfigurations, contract issues', FALSE),
    (4, 'analyze_getFlowTopology', 'Visualize the actual flow path through the fabric', 'Topology map showing hops, interfaces, and policies', FALSE),
    (5, 'analyze_listFlowDetails', 'Get detailed per-flow statistics and metadata', 'Flow details: protocol, ports, bytes, packets', FALSE),
    (6, 'analyze_listFlowsStatistics', 'Check flow rate, drops, and utilization trends', 'Time-series flow statistics', TRUE)
) AS v(step_order, operation_name, description, expected_output, optional)
WHERE w.name = 'flow_path_analysis'
AND NOT EXISTS (
    SELECT 1 FROM workflow_steps ws WHERE ws.workflow_id = w.id AND ws.step_order = v.step_order
);

-- 7. Configuration Compliance Check
INSERT INTO workflow_steps (workflow_id, step_order, operation_name, description, expected_output, optional)
SELECT w.id, v.step_order, v.operation_name, v.description, v.expected_output, v.optional
FROM workflows w
CROSS JOIN (VALUES
    (1, 'analyze_listConformanceSummaries', 'Get overall configuration compliance summary', 'Compliance score and violation counts by category', FALSE),
    (2, 'analyze_listConformanceDetails', 'List specific compliance violations and deviations', 'Detailed violations: object, expected vs actual config', FALSE),
    (3, 'manage_getFabricConfigurationPreview', 'Preview any pending configuration changes', 'Pending changes that have not been deployed yet', TRUE),
    (4, 'manage_getSwitchConfigurationDiff', 'Check per-switch config drift between intended and running', 'Config diff per switch showing drift', FALSE),
    (5, 'analyze_getAnomaliesSummary', 'Check for configuration-related anomalies', 'Config anomalies: misconfigurations, policy violations', FALSE)
) AS v(step_order, operation_name, description, expected_output, optional)
WHERE w.name = 'configuration_compliance_check'
AND NOT EXISTS (
    SELECT 1 FROM workflow_steps ws WHERE ws.workflow_id = w.id AND ws.step_order = v.step_order
);

-- 8. Advisory & Alert Triage
INSERT INTO workflow_steps (workflow_id, step_order, operation_name, description, expected_output, optional)
SELECT w.id, v.step_order, v.operation_name, v.description, v.expected_output, v.optional
FROM workflows w
CROSS JOIN (VALUES
    (1, 'analyze_getAdvisoriesSummary', 'Get overview of all advisories by severity and type', 'Advisory counts: PSIRT, field notice, EOL by severity', FALSE),
    (2, 'analyze_getAdvisoriesDetails', 'List individual advisories with full details', 'Advisory details: ID, title, affected versions, severity', FALSE),
    (3, 'analyze_getAdvisoryRecommendations', 'Get fix recommendations for the highest-priority advisory', 'Recommended actions: patches, upgrades, workarounds', FALSE),
    (4, 'analyze_getAlertsTrend', 'Check if alerts are increasing or decreasing over time', 'Alert trend data showing direction and velocity', FALSE),
    (5, 'analyze_getSoftwareRecommendations', 'Check if software upgrades would resolve outstanding issues', 'Recommended software versions and resolved defects', TRUE),
    (6, 'analyze_updateAlertsStatus', 'Acknowledge or dismiss resolved alerts to clean up the queue', 'Updated alert status confirmation', TRUE)
) AS v(step_order, operation_name, description, expected_output, optional)
WHERE w.name = 'advisory_alert_triage'
AND NOT EXISTS (
    SELECT 1 FROM workflow_steps ws WHERE ws.workflow_id = w.id AND ws.step_order = v.step_order
);

-- 9. Node/Switch Health Investigation
INSERT INTO workflow_steps (workflow_id, step_order, operation_name, description, expected_output, optional)
SELECT w.id, v.step_order, v.operation_name, v.description, v.expected_output, v.optional
FROM workflows w
CROSS JOIN (VALUES
    (1, 'analyze_listSwitchesSummary', 'Get switch health overview and identify the unhealthy node', 'Switch list with health scores and status', FALSE),
    (2, 'analyze_listSwitchesConfig', 'Check the switch configuration for misconfigurations', 'Switch configuration details and settings', FALSE),
    (3, 'analyze_getAnomaliesTopNodes', 'See how many anomalies are attributed to this node', 'Anomaly count and ranking for the node', FALSE),
    (4, 'analyze_getAnomalyDetails', 'Get specifics on the anomalies affecting the node', 'Individual anomaly details: type, severity, description', FALSE),
    (5, 'infra_listNodes', 'Check infrastructure-level node status and properties', 'Node properties: model, serial, firmware, uptime', FALSE),
    (6, 'infra_getClusterHealtStatus', 'Check overall cluster health to assess systemic impact', 'Cluster health status and service availability', TRUE),
    (7, 'analyze_getAnomalyRecommendations', 'Get fix recommendations for the node anomalies', 'Recommended remediation steps for the node', FALSE)
) AS v(step_order, operation_name, description, expected_output, optional)
WHERE w.name = 'node_switch_health'
AND NOT EXISTS (
    SELECT 1 FROM workflow_steps ws WHERE ws.workflow_id = w.id AND ws.step_order = v.step_order
);

-- 10. Multicast Troubleshooting
INSERT INTO workflow_steps (workflow_id, step_order, operation_name, description, expected_output, optional)
SELECT w.id, v.step_order, v.operation_name, v.description, v.expected_output, v.optional
FROM workflows w
CROSS JOIN (VALUES
    (1, 'analyze_listMulticastRoutes', 'List multicast routes to verify group registration', 'Multicast route table: groups, sources, RPF interfaces', FALSE),
    (2, 'analyze_listMulticastRouteSources', 'Check multicast source registration and active sources', 'Registered sources per group with status', FALSE),
    (3, 'analyze_listMulticastRouteReceivers', 'Verify receiver paths and downstream interfaces', 'Receiver list with OIF and join state', FALSE),
    (4, 'analyze_listIgmpMulticastGroups', 'Check IGMP group membership on relevant interfaces', 'IGMP groups: members, last-reporter, expiry timers', FALSE),
    (5, 'analyze_listIgmpInterfaces', 'Verify IGMP interface status and configuration', 'IGMP interface config: version, querier status, timers', FALSE),
    (6, 'analyze_listPimNeighbors', 'Check PIM neighbor adjacency for multicast routing', 'PIM neighbors: address, uptime, expiry, DR priority', FALSE),
    (7, 'analyze_listPimInterfaces', 'Verify PIM interface status and mode configuration', 'PIM interface config: mode (sparse/dense), DR, hello interval', FALSE)
) AS v(step_order, operation_name, description, expected_output, optional)
WHERE w.name = 'multicast_troubleshooting'
AND NOT EXISTS (
    SELECT 1 FROM workflow_steps ws WHERE ws.workflow_id = w.id AND ws.step_order = v.step_order
);

-- ============================================================================
-- USE CASES
-- ============================================================================

INSERT INTO use_cases (name, display_name, description, category, is_active)
VALUES
    (
        'connectivity_troubleshooting',
        'Connectivity Troubleshooting',
        'Diagnose and resolve endpoint connectivity issues including unreachable hosts, broken paths, and flow problems.',
        'troubleshooting',
        TRUE
    ),
    (
        'ip_address_conflict',
        'IP Address Conflict',
        'Detect and resolve duplicate IP address situations where multiple endpoints share the same IP, causing intermittent connectivity.',
        'troubleshooting',
        TRUE
    ),
    (
        'proactive_monitoring',
        'Proactive Monitoring',
        'Regular health checks across fabric and nodes to catch issues before they impact production traffic.',
        'monitoring',
        TRUE
    ),
    (
        'interface_problems',
        'Interface Problems',
        'Troubleshoot interface-level issues including link failures, error counters, flapping, and congestion.',
        'troubleshooting',
        TRUE
    ),
    (
        'routing_issues',
        'Routing Issues',
        'Investigate routing protocol problems including BGP neighbor failures, missing routes, and route instability.',
        'troubleshooting',
        TRUE
    ),
    (
        'compliance_and_drift',
        'Compliance & Drift',
        'Verify that fabric configuration matches the intended state and detect any configuration drift.',
        'compliance',
        TRUE
    ),
    (
        'alert_management',
        'Alert Management',
        'Triage, prioritize, and resolve advisories and alerts across the fabric.',
        'operations',
        TRUE
    ),
    (
        'multicast_issues',
        'Multicast Issues',
        'Diagnose multicast delivery failures including IGMP membership, PIM adjacency, and source/receiver path issues.',
        'troubleshooting',
        TRUE
    )
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- USE CASE <-> WORKFLOW LINKS
-- ============================================================================

INSERT INTO use_case_workflows (use_case_id, workflow_id)
SELECT uc.id, w.id
FROM use_cases uc, workflows w
WHERE (uc.name, w.name) IN (
    ('connectivity_troubleshooting', 'endpoint_unreachable'),
    ('connectivity_troubleshooting', 'flow_path_analysis'),
    ('ip_address_conflict', 'duplicate_ip_detection'),
    ('proactive_monitoring', 'fabric_health_assessment'),
    ('proactive_monitoring', 'node_switch_health'),
    ('interface_problems', 'interface_troubleshooting'),
    ('routing_issues', 'bgp_routing_investigation'),
    ('compliance_and_drift', 'configuration_compliance_check'),
    ('alert_management', 'advisory_alert_triage'),
    ('multicast_issues', 'multicast_troubleshooting')
)
ON CONFLICT (use_case_id, workflow_id) DO NOTHING;
