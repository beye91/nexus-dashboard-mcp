"""Resource group management service for MCP tool consolidation."""

import logging
from typing import List, Optional, Dict, Any, Set

from sqlalchemy import select, delete, text, func
from sqlalchemy.orm import selectinload

from src.config.database import get_db
from src.models.resource_group import ResourceGroup, ResourceGroupMapping
from src.models.api_endpoint import APIEndpoint
from src.core.resource_grouper import extract_resource_from_path

logger = logging.getLogger(__name__)


class ResourceGroupService:
    """Service for resource group management and tool consolidation."""

    def __init__(self):
        """Initialize resource group service."""
        self.db = get_db()

    # ==================== Group CRUD ====================

    async def create_group(
        self,
        group_key: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        is_enabled: bool = True,
        is_custom: bool = True,
        sort_order: int = 0,
    ) -> ResourceGroup:
        """Create a new resource group.

        Args:
            group_key: Unique group key (e.g., "analyze_fabrics")
            display_name: Human-readable display name
            description: Description for the MCP tool
            is_enabled: Whether the group is enabled
            is_custom: Whether this is a user-created group
            sort_order: Order for UI display

        Returns:
            Created ResourceGroup instance

        Raises:
            ValueError: If group key already exists
        """
        async with self.db.session() as session:
            # Check if group exists
            result = await session.execute(
                select(ResourceGroup).where(ResourceGroup.group_key == group_key)
            )
            if result.scalar_one_or_none():
                raise ValueError(f"Resource group '{group_key}' already exists")

            # Create group
            group = ResourceGroup(
                group_key=group_key,
                display_name=display_name or group_key.replace("_", " ").title(),
                description=description,
                is_enabled=is_enabled,
                is_custom=is_custom,
                sort_order=sort_order,
            )
            session.add(group)
            await session.commit()
            await session.refresh(group)

            logger.info(f"Created resource group: {group_key}")
            return group

    async def get_group(self, group_id: int) -> Optional[ResourceGroup]:
        """Get resource group by ID with mappings loaded.

        Args:
            group_id: Group ID

        Returns:
            ResourceGroup instance or None if not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(ResourceGroup)
                .options(selectinload(ResourceGroup.mappings))
                .where(ResourceGroup.id == group_id)
            )
            return result.scalar_one_or_none()

    async def get_group_by_key(self, group_key: str) -> Optional[ResourceGroup]:
        """Get resource group by key with mappings loaded.

        Args:
            group_key: Group key

        Returns:
            ResourceGroup instance or None if not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(ResourceGroup)
                .options(selectinload(ResourceGroup.mappings))
                .where(ResourceGroup.group_key == group_key)
            )
            return result.scalar_one_or_none()

    async def list_groups(
        self,
        enabled_only: bool = False,
        custom_only: bool = False,
    ) -> List[ResourceGroup]:
        """List all resource groups.

        Args:
            enabled_only: Only return enabled groups
            custom_only: Only return custom (user-created) groups

        Returns:
            List of ResourceGroup instances
        """
        async with self.db.session() as session:
            query = select(ResourceGroup).options(selectinload(ResourceGroup.mappings))

            if enabled_only:
                query = query.where(ResourceGroup.is_enabled == True)
            if custom_only:
                query = query.where(ResourceGroup.is_custom == True)

            query = query.order_by(ResourceGroup.sort_order, ResourceGroup.group_key)

            result = await session.execute(query)
            return list(result.scalars().all())

    async def update_group(
        self,
        group_id: int,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        sort_order: Optional[int] = None,
    ) -> Optional[ResourceGroup]:
        """Update resource group properties.

        Args:
            group_id: Group ID to update
            display_name: New display name (if provided)
            description: New description (if provided)
            is_enabled: New enabled status (if provided)
            sort_order: New sort order (if provided)

        Returns:
            Updated ResourceGroup instance or None if not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(ResourceGroup).where(ResourceGroup.id == group_id)
            )
            group = result.scalar_one_or_none()
            if not group:
                return None

            if display_name is not None:
                group.display_name = display_name
            if description is not None:
                group.description = description
            if is_enabled is not None:
                group.is_enabled = is_enabled
            if sort_order is not None:
                group.sort_order = sort_order

            await session.commit()
            await session.refresh(group)

            logger.info(f"Updated resource group: {group.group_key}")
            return group

    async def delete_group(self, group_id: int) -> bool:
        """Delete a resource group.

        Args:
            group_id: Group ID to delete

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If trying to delete a non-custom group
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(ResourceGroup).where(ResourceGroup.id == group_id)
            )
            group = result.scalar_one_or_none()
            if not group:
                return False

            if not group.is_custom:
                raise ValueError(f"Cannot delete auto-generated group '{group.group_key}'")

            await session.delete(group)
            await session.commit()

            logger.info(f"Deleted resource group: {group.group_key}")
            return True

    # ==================== Operation Mappings ====================

    async def add_operations_to_group(
        self,
        group_id: int,
        operations: List[Dict[str, str]],
    ) -> Optional[ResourceGroup]:
        """Add operations to a resource group.

        Args:
            group_id: Group ID
            operations: List of dicts with 'operation_id' and 'api_name'

        Returns:
            Updated ResourceGroup or None if group not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(ResourceGroup).where(ResourceGroup.id == group_id)
            )
            group = result.scalar_one_or_none()
            if not group:
                return None

            for op in operations:
                # Remove from any existing group first (operation can only be in one group)
                await session.execute(
                    delete(ResourceGroupMapping).where(
                        ResourceGroupMapping.operation_id == op["operation_id"],
                        ResourceGroupMapping.api_name == op["api_name"]
                    )
                )

                # Add to this group
                mapping = ResourceGroupMapping(
                    group_id=group_id,
                    operation_id=op["operation_id"],
                    api_name=op["api_name"],
                )
                session.add(mapping)

            await session.commit()

            logger.info(f"Added {len(operations)} operations to group {group.group_key}")
            return await self.get_group(group_id)

    async def remove_operations_from_group(
        self,
        group_id: int,
        operation_ids: List[str],
    ) -> Optional[ResourceGroup]:
        """Remove operations from a resource group.

        Args:
            group_id: Group ID
            operation_ids: List of operation_ids to remove

        Returns:
            Updated ResourceGroup or None if group not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(ResourceGroup).where(ResourceGroup.id == group_id)
            )
            if not result.scalar_one_or_none():
                return None

            await session.execute(
                delete(ResourceGroupMapping).where(
                    ResourceGroupMapping.group_id == group_id,
                    ResourceGroupMapping.operation_id.in_(operation_ids)
                )
            )

            await session.commit()

            return await self.get_group(group_id)

    async def get_unmapped_operations(
        self,
        api_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get operations that are not mapped to any group.

        Args:
            api_name: Filter by API name

        Returns:
            List of operation dictionaries
        """
        async with self.db.session() as session:
            # Get all mapped operation IDs
            mapped_result = await session.execute(
                select(ResourceGroupMapping.operation_id, ResourceGroupMapping.api_name)
            )
            mapped_ops = {(row[0], row[1]) for row in mapped_result.all()}

            # Get all endpoints
            query = select(APIEndpoint)
            if api_name:
                query = query.where(APIEndpoint.api_name == api_name)

            result = await session.execute(query)
            endpoints = list(result.scalars().all())

            # Filter to unmapped
            unmapped = []
            for ep in endpoints:
                if (ep.operation_id, ep.api_name) not in mapped_ops:
                    unmapped.append({
                        "operation_id": ep.operation_id,
                        "api_name": ep.api_name,
                        "http_method": ep.http_method,
                        "path": ep.path,
                        "description": ep.description,
                    })

            return unmapped

    # ==================== Auto-Generation ====================

    async def generate_default_groups(self, force: bool = False) -> int:
        """Generate default resource groups from API endpoints.

        Groups are created based on the first path segment of each endpoint.
        Format: "{api_name}_{resource}"

        Args:
            force: If True, regenerate even if groups already exist

        Returns:
            Number of groups created
        """
        async with self.db.session() as session:
            # Check if groups already exist
            if not force:
                existing = await session.execute(
                    select(ResourceGroup).limit(1)
                )
                if existing.scalar_one_or_none():
                    logger.info("Resource groups already exist, skipping generation")
                    return 0

            # Get all endpoints grouped by api_name and resource
            result = await session.execute(select(APIEndpoint))
            endpoints = list(result.scalars().all())

            # Group by api_name and resource
            groups_data: Dict[str, Dict[str, Any]] = {}
            for ep in endpoints:
                resource = extract_resource_from_path(ep.path)
                group_key = f"{ep.api_name}_{resource}"

                if group_key not in groups_data:
                    groups_data[group_key] = {
                        "api_name": ep.api_name,
                        "resource": resource,
                        "operations": [],
                        "methods": set(),
                    }

                groups_data[group_key]["operations"].append({
                    "operation_id": ep.operation_id,
                    "api_name": ep.api_name,
                })
                groups_data[group_key]["methods"].add(ep.http_method)

            # Create groups and mappings
            created_count = 0
            for group_key, data in groups_data.items():
                # Check if group exists
                existing = await session.execute(
                    select(ResourceGroup).where(ResourceGroup.group_key == group_key)
                )
                if existing.scalar_one_or_none():
                    continue

                # Build description
                method_summary = ", ".join(sorted(data["methods"]))
                op_count = len(data["operations"])
                description = (
                    f"Operations for {data['resource']} resource ({data['api_name']} API). "
                    f"Contains {op_count} operations ({method_summary})."
                )

                # Create group
                group = ResourceGroup(
                    group_key=group_key,
                    display_name=f"{data['resource'].replace('_', ' ').title()} ({data['api_name']})",
                    description=description,
                    is_enabled=True,
                    is_custom=False,
                    sort_order=0,
                )
                session.add(group)
                await session.flush()  # Get group ID

                # Create mappings
                for op in data["operations"]:
                    mapping = ResourceGroupMapping(
                        group_id=group.id,
                        operation_id=op["operation_id"],
                        api_name=op["api_name"],
                    )
                    session.add(mapping)

                created_count += 1

            await session.commit()

            logger.info(f"Generated {created_count} default resource groups from {len(endpoints)} operations")
            return created_count

    # ==================== Tool Consolidation Helpers ====================

    async def get_enabled_groups_with_operations(self) -> Dict[str, List[str]]:
        """Get enabled groups with their operation IDs.

        Returns:
            Dict mapping group_key to list of operation_ids
        """
        groups = await self.list_groups(enabled_only=True)
        return {
            group.group_key: group.get_operation_ids()
            for group in groups
        }

    async def get_group_for_operation(
        self,
        operation_id: str,
        api_name: str,
    ) -> Optional[str]:
        """Get the group key for a specific operation.

        Args:
            operation_id: Operation ID
            api_name: API name

        Returns:
            Group key or None if operation is not mapped
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(ResourceGroup.group_key)
                .join(ResourceGroupMapping)
                .where(
                    ResourceGroupMapping.operation_id == operation_id,
                    ResourceGroupMapping.api_name == api_name
                )
            )
            row = result.first()
            return row[0] if row else None

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about resource groups.

        Returns:
            Dictionary with stats
        """
        async with self.db.session() as session:
            # Total groups
            groups_result = await session.execute(
                select(func.count(ResourceGroup.id))
            )
            total_groups = groups_result.scalar() or 0

            # Enabled groups
            enabled_result = await session.execute(
                select(func.count(ResourceGroup.id))
                .where(ResourceGroup.is_enabled == True)
            )
            enabled_groups = enabled_result.scalar() or 0

            # Custom groups
            custom_result = await session.execute(
                select(func.count(ResourceGroup.id))
                .where(ResourceGroup.is_custom == True)
            )
            custom_groups = custom_result.scalar() or 0

            # Total mappings
            mappings_result = await session.execute(
                select(func.count(ResourceGroupMapping.id))
            )
            total_mappings = mappings_result.scalar() or 0

            # Total operations
            ops_result = await session.execute(
                select(func.count(APIEndpoint.id))
            )
            total_operations = ops_result.scalar() or 0

            return {
                "total_groups": total_groups,
                "enabled_groups": enabled_groups,
                "custom_groups": custom_groups,
                "auto_generated_groups": total_groups - custom_groups,
                "mapped_operations": total_mappings,
                "total_operations": total_operations,
                "unmapped_operations": total_operations - total_mappings,
            }


# Singleton instance for easy access
_service_instance: Optional[ResourceGroupService] = None


def get_resource_group_service() -> ResourceGroupService:
    """Get the resource group service singleton.

    Returns:
        ResourceGroupService instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = ResourceGroupService()
    return _service_instance
