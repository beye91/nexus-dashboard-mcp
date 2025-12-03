"""Database initialization service for default data."""

import json
import logging
from pathlib import Path

from sqlalchemy import select, delete

from src.config.database import get_db
from src.models.security import SecurityConfig
from src.models.api_endpoint import APIEndpoint

logger = logging.getLogger(__name__)


async def initialize_security_config():
    """Initialize default security configuration if none exists.

    This ensures that the security_config table has at least one row
    so the MCP server can read edit_mode settings from the database.
    """
    db = get_db()

    async with db.session() as session:
        # Check if any security config exists
        result = await session.execute(
            select(SecurityConfig).limit(1)
        )
        existing_config = result.scalar_one_or_none()

        if existing_config:
            logger.info("Security configuration already exists in database")
            logger.info(f"Edit mode: {existing_config.edit_mode_enabled}")
            return existing_config

        # Create default security configuration
        default_config = SecurityConfig(
            edit_mode_enabled=False,  # Start with read-only mode for safety
            audit_logging=True,       # Enable audit logging by default
            allowed_operations=[]     # No specific operation restrictions
        )

        session.add(default_config)
        await session.commit()
        await session.refresh(default_config)

        logger.info("Created default security configuration:")
        logger.info(f"  - Edit mode: {default_config.edit_mode_enabled}")
        logger.info(f"  - Audit logging: {default_config.audit_logging}")
        logger.info("  - Update via Web UI or database to enable write operations")

        return default_config


async def sync_api_endpoints():
    """Sync API endpoints from OpenAPI specification files to database.

    This loads all operations from the OpenAPI spec files and populates
    the api_endpoints table for use in RBAC operations selection.
    """
    db = get_db()

    # Define API spec files and their names
    api_specs = {
        "manage": "nexus_dashboard_manage.json",
        "analyze": "analyze.json",
        "infra": "infra.json",
        "onemanage": "one_mange.json",
    }

    specs_dir = Path("openapi_specs")
    if not specs_dir.exists():
        logger.warning(f"OpenAPI specs directory not found: {specs_dir}")
        return

    total_loaded = 0

    async with db.session() as session:
        for api_name, spec_file in api_specs.items():
            spec_path = specs_dir / spec_file

            if not spec_path.exists():
                logger.warning(f"OpenAPI spec file not found: {spec_path}")
                continue

            try:
                with open(spec_path, "r") as f:
                    spec = json.load(f)

                paths = spec.get("paths", {})
                operations_added = 0

                for path, path_item in paths.items():
                    for method in ["get", "post", "put", "delete", "patch"]:
                        if method in path_item:
                            operation = path_item[method]
                            operation_id = operation.get("operationId", f"{api_name}_{method}_{path.replace('/', '_')}")
                            summary = operation.get("summary", "")
                            description = operation.get("description", summary)

                            # Check if endpoint already exists
                            existing = await session.execute(
                                select(APIEndpoint).where(
                                    APIEndpoint.api_name == api_name,
                                    APIEndpoint.operation_id == operation_id
                                )
                            )
                            if existing.scalar_one_or_none():
                                continue  # Skip existing endpoints

                            # Determine if operation requires edit mode
                            requires_edit = method.upper() in ["POST", "PUT", "DELETE", "PATCH"]

                            endpoint = APIEndpoint(
                                api_name=api_name,
                                operation_id=operation_id,
                                http_method=method.upper(),
                                path=path,
                                enabled=True,
                                requires_edit_mode=requires_edit,
                                description=description[:500] if description else None,
                            )
                            session.add(endpoint)
                            operations_added += 1

                await session.commit()
                logger.info(f"Loaded {operations_added} operations from {api_name} API")
                total_loaded += operations_added

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAPI spec {spec_file}: {e}")
            except Exception as e:
                logger.error(f"Error loading OpenAPI spec {spec_file}: {e}")

    logger.info(f"Total API endpoints synced to database: {total_loaded}")


async def initialize_database_defaults():
    """Initialize all default database records.

    This function is called during database initialization to ensure
    required default data exists.
    """
    logger.info("Initializing database default values...")

    # Initialize security configuration
    await initialize_security_config()

    # Sync API endpoints from OpenAPI specs
    await sync_api_endpoints()

    logger.info("Database initialization completed")
