"""API Registry for managing multiple Nexus Dashboard APIs."""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class APIDefinition:
    """Definition of a Nexus Dashboard API."""

    name: str
    display_name: str
    spec_file: str
    base_path: str
    description: str
    enabled: bool = True


class APIRegistry:
    """Registry for managing multiple Nexus Dashboard APIs."""

    # Define all available APIs
    APIS: Dict[str, APIDefinition] = {
        "manage": APIDefinition(
            name="manage",
            display_name="Nexus Dashboard Manage (Fabric Controller)",
            spec_file="nexus_dashboard_manage.json",
            base_path="/api/v1/manage",
            description="Fabric management, switches, networks, VRFs, policies, templates",
            enabled=True
        ),
        "analyze": APIDefinition(
            name="analyze",
            display_name="Nexus Dashboard Insights (Network Analysis)",
            spec_file="analyze.json",
            base_path="/api/v1/analyze",
            description="Network insights, flow analytics, anomalies, compliance, advisories",
            enabled=True
        ),
        "infra": APIDefinition(
            name="infra",
            display_name="Nexus Dashboard Infrastructure",
            spec_file="infra.json",
            base_path="/api/v1/infra",
            description="Cluster management, nodes, services, system health, backups",
            enabled=True
        ),
        "onemanage": APIDefinition(
            name="onemanage",
            display_name="Nexus Dashboard OneManage (Multi-Site)",
            spec_file="one_mange.json",
            base_path="/api/v1/oneManage",
            description="Multi-site orchestration and management",
            enabled=True
        ),
        # Note: orchestrator.json currently has parsing issues
        # "orchestrator": APIDefinition(
        #     name="orchestrator",
        #     display_name="Nexus Dashboard Orchestrator",
        #     spec_file="orchestrator.json",
        #     base_path="/api/v1/orchestrator",
        #     description="Multi-cloud orchestration and automation",
        #     enabled=False
        # ),
    }

    @classmethod
    def get_api(cls, name: str) -> Optional[APIDefinition]:
        """Get API definition by name.

        Args:
            name: API name

        Returns:
            APIDefinition or None if not found
        """
        return cls.APIS.get(name)

    @classmethod
    def get_enabled_apis(cls) -> List[APIDefinition]:
        """Get list of enabled APIs.

        Returns:
            List of enabled APIDefinition objects
        """
        return [api for api in cls.APIS.values() if api.enabled]

    @classmethod
    def get_all_apis(cls) -> List[APIDefinition]:
        """Get list of all APIs.

        Returns:
            List of all APIDefinition objects
        """
        return list(cls.APIS.values())

    @classmethod
    def enable_api(cls, name: str) -> bool:
        """Enable an API.

        Args:
            name: API name

        Returns:
            True if successful, False if API not found
        """
        api = cls.get_api(name)
        if api:
            api.enabled = True
            return True
        return False

    @classmethod
    def disable_api(cls, name: str) -> bool:
        """Disable an API.

        Args:
            name: API name

        Returns:
            True if successful, False if API not found
        """
        api = cls.get_api(name)
        if api:
            api.enabled = False
            return True
        return False

    @classmethod
    def get_base_path_for_api(cls, api_name: str) -> Optional[str]:
        """Get base path for an API.

        Args:
            api_name: API name

        Returns:
            Base path string or None if API not found
        """
        api = cls.get_api(api_name)
        return api.base_path if api else None
