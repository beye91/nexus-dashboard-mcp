"""API loader for loading OpenAPI specifications and creating MCP tools."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class APILoader:
    """Loader for OpenAPI specifications."""

    def __init__(self, specs_dir: str = "openapi_specs"):
        """Initialize API loader.

        Args:
            specs_dir: Directory containing OpenAPI specification files
        """
        self.specs_dir = Path(specs_dir)
        self.loaded_specs: Dict[str, Dict[str, Any]] = {}

    def load_openapi_spec(self, spec_file: str) -> Optional[Dict[str, Any]]:
        """Load an OpenAPI specification from file.

        Args:
            spec_file: Name of the OpenAPI spec file

        Returns:
            OpenAPI specification as dictionary, or None if load fails
        """
        spec_path = self.specs_dir / spec_file

        if not spec_path.exists():
            logger.error(f"OpenAPI spec file not found: {spec_path}")
            return None

        try:
            with open(spec_path, "r") as f:
                spec = json.load(f)

            logger.info(f"Successfully loaded OpenAPI spec: {spec_file}")
            return spec

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAPI spec {spec_file}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading OpenAPI spec {spec_file}: {e}")
            return None

    def get_api_info(self, spec: Dict[str, Any]) -> Dict[str, str]:
        """Extract API information from OpenAPI spec.

        Args:
            spec: OpenAPI specification dictionary

        Returns:
            Dictionary with API title, version, description
        """
        info = spec.get("info", {})
        return {
            "title": info.get("title", "Unknown API"),
            "version": info.get("version", "0.0.0"),
            "description": info.get("description", ""),
        }

    def count_endpoints(self, spec: Dict[str, Any]) -> Dict[str, int]:
        """Count endpoints by HTTP method in an OpenAPI spec.

        Args:
            spec: OpenAPI specification dictionary

        Returns:
            Dictionary with counts by HTTP method
        """
        counts = {"GET": 0, "POST": 0, "PUT": 0, "DELETE": 0, "PATCH": 0, "total": 0}

        paths = spec.get("paths", {})
        for path, path_item in paths.items():
            for method in ["get", "post", "put", "delete", "patch"]:
                if method in path_item:
                    counts[method.upper()] += 1
                    counts["total"] += 1

        return counts

    def list_operations(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List all operations from an OpenAPI spec.

        Args:
            spec: OpenAPI specification dictionary

        Returns:
            List of operation dictionaries with method, path, operation_id, summary
        """
        operations = []

        paths = spec.get("paths", {})
        for path, path_item in paths.items():
            for method in ["get", "post", "put", "delete", "patch", "head", "options"]:
                if method in path_item:
                    operation = path_item[method]
                    operations.append({
                        "method": method.upper(),
                        "path": path,
                        "operation_id": operation.get("operationId", f"{method}_{path}"),
                        "summary": operation.get("summary", ""),
                        "description": operation.get("description", ""),
                        "tags": operation.get("tags", []),
                        "parameters": operation.get("parameters", []),
                        "requestBody": operation.get("requestBody"),
                    })

        return operations

    def get_base_url(self, spec: Dict[str, Any]) -> Optional[str]:
        """Extract base URL from OpenAPI spec.

        Args:
            spec: OpenAPI specification dictionary

        Returns:
            Base URL string or None if not found
        """
        servers = spec.get("servers", [])
        if servers and len(servers) > 0:
            server_url = servers[0].get("url", "")
            return server_url

        return None

    def validate_spec(self, spec: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate basic OpenAPI spec structure.

        Args:
            spec: OpenAPI specification dictionary

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        # Check required fields
        if "openapi" not in spec:
            errors.append("Missing 'openapi' version field")

        if "info" not in spec:
            errors.append("Missing 'info' section")
        elif "title" not in spec["info"]:
            errors.append("Missing 'info.title' field")

        if "paths" not in spec:
            errors.append("Missing 'paths' section")
        elif not spec["paths"]:
            errors.append("'paths' section is empty")

        is_valid = len(errors) == 0
        return is_valid, errors

    def load_all_specs(self) -> Dict[str, Dict[str, Any]]:
        """Load all OpenAPI specifications from specs directory.

        Returns:
            Dictionary mapping API name to spec dict
        """
        api_files = {
            "manage": "nexus_dashboard_manage.json",
            "analyze": "analyze.json",
            "infra": "infra.json",
            "one_manage": "one_mange.json",
            "orchestrator": "orchestrator.json",
        }

        loaded = {}

        for api_name, spec_file in api_files.items():
            spec = self.load_openapi_spec(spec_file)
            if spec:
                is_valid, errors = self.validate_spec(spec)
                if is_valid:
                    loaded[api_name] = spec
                    logger.info(f"Validated and loaded API: {api_name}")
                else:
                    logger.error(f"Invalid OpenAPI spec for {api_name}: {errors}")
            else:
                logger.warning(f"Skipping API {api_name}: failed to load spec")

        self.loaded_specs = loaded
        return loaded
