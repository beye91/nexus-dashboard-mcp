"""Authentication middleware for Nexus Dashboard API requests."""

import logging
from typing import Any, Callable, Dict, Optional

from src.core.api_registry import APIRegistry
from src.services.credential_manager import CredentialManager
from src.services.nexus_api import NexusAPIClient

logger = logging.getLogger(__name__)


class AuthMiddleware:
    """Middleware for handling authentication to Nexus Dashboard."""

    def __init__(self, cluster_name: str = "default"):
        """Initialize authentication middleware.

        Args:
            cluster_name: Name of the cluster to authenticate with
        """
        self.cluster_name = cluster_name
        self.credential_manager = CredentialManager()
        self.api_client: Optional[NexusAPIClient] = None

    async def get_api_client(self) -> NexusAPIClient:
        """Get or create authenticated API client.

        Returns:
            Authenticated NexusAPIClient instance

        Raises:
            RuntimeError: If credentials not found or authentication fails
        """
        if self.api_client is not None:
            return self.api_client

        # Retrieve credentials from database
        credentials = None
        if self.cluster_name == "default":
            # If using default, try to get the first active cluster
            credentials = await self.credential_manager.get_first_active_cluster_credentials()
            if credentials:
                self.cluster_name = credentials["name"]
                logger.info(f"Using first active cluster: {self.cluster_name}")
        else:
            credentials = await self.credential_manager.get_credentials(self.cluster_name)

        if not credentials:
            raise RuntimeError(
                f"No credentials found for cluster '{self.cluster_name}'. "
                f"Please configure a cluster in the web UI first."
            )

        # Create and authenticate API client
        self.api_client = NexusAPIClient(
            base_url=credentials["url"],
            username=credentials["username"],
            password=credentials["password"],
            verify_ssl=credentials["verify_ssl"],
        )

        # Authenticate
        authenticated = await self.api_client.authenticate()
        if not authenticated:
            raise RuntimeError(
                f"Failed to authenticate with cluster '{self.cluster_name}'"
            )

        logger.info(f"Successfully authenticated with cluster '{self.cluster_name}'")
        return self.api_client

    async def execute_request(
        self,
        method: str,
        path: str,
        api_name: str = "manage",
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute authenticated API request.

        Args:
            method: HTTP method
            path: API endpoint path (will be prefixed with appropriate API base path)
            api_name: Name of the API (manage, analyze, infra, onemanage)
            params: Query parameters
            json_data: JSON request body

        Returns:
            Response data as dictionary

        Raises:
            RuntimeError: If request fails
        """
        client = await self.get_api_client()

        # Prepend the API base path if not already present
        if not path.startswith("/api/"):
            base_path = APIRegistry.get_base_path_for_api(api_name)
            if base_path:
                path = f"{base_path}{path}"
            else:
                # Fallback to manage API
                path = f"/api/v1/manage{path}"

        try:
            response = await client.request(
                method=method,
                path=path,
                params=params,
                json_data=json_data,
            )

            # Return JSON response
            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()

            # Return text for non-JSON responses
            return {"data": response.text, "status_code": response.status_code}

        except Exception as e:
            logger.error(f"API request failed: {method} {path} - {e}")
            raise RuntimeError(f"API request failed: {e}")

    async def close(self):
        """Close API client connection."""
        if self.api_client:
            await self.api_client.close()
            self.api_client = None

    def __call__(self, func: Callable) -> Callable:
        """Decorator for adding authentication to functions.

        Args:
            func: Function to wrap with authentication

        Returns:
            Wrapped function with authentication
        """
        async def wrapper(*args, **kwargs):
            try:
                # Ensure we're authenticated before calling function
                await self.get_api_client()
                return await func(*args, **kwargs)
            finally:
                # Clean up if needed
                pass

        return wrapper
