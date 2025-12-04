"""Role management service for RBAC."""

import logging
from typing import List, Optional, Dict, Any

from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from src.config.database import get_db
from src.models.role import Role, RoleOperation
from src.models.api_endpoint import APIEndpoint

logger = logging.getLogger(__name__)


class RoleService:
    """Service for role and operations management."""

    def __init__(self):
        """Initialize role service."""
        self.db = get_db()

    # ==================== Role CRUD ====================

    async def create_role(
        self,
        name: str,
        description: Optional[str] = None,
        edit_mode_enabled: bool = False,
        operations: Optional[List[str]] = None,
    ) -> Role:
        """Create a new role.

        Args:
            name: Unique role name
            description: Role description
            edit_mode_enabled: Whether role has edit mode access
            operations: List of allowed operation names

        Returns:
            Created Role instance

        Raises:
            ValueError: If role name already exists
        """
        async with self.db.session() as session:
            # Check if role exists
            result = await session.execute(
                select(Role).where(Role.name == name)
            )
            if result.scalar_one_or_none():
                raise ValueError(f"Role '{name}' already exists")

            # Create role
            role = Role(
                name=name,
                description=description,
                edit_mode_enabled=edit_mode_enabled,
                is_system_role=False,
            )
            session.add(role)
            await session.flush()  # Get role ID

            # Add operations if provided
            if operations:
                for op_name in operations:
                    role_op = RoleOperation(role_id=role.id, operation_name=op_name)
                    session.add(role_op)

            await session.commit()
            await session.refresh(role)

            logger.info(f"Created role: {name}")
            return role

    async def get_role(self, role_id: int) -> Optional[Role]:
        """Get role by ID with operations loaded.

        Args:
            role_id: Role ID

        Returns:
            Role instance or None if not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(Role)
                .options(selectinload(Role.operations))
                .where(Role.id == role_id)
            )
            return result.scalar_one_or_none()

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name with operations loaded.

        Args:
            name: Role name

        Returns:
            Role instance or None if not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(Role)
                .options(selectinload(Role.operations))
                .where(Role.name == name)
            )
            return result.scalar_one_or_none()

    async def list_roles(self, include_system: bool = True) -> List[Role]:
        """List all roles.

        Args:
            include_system: Whether to include system roles

        Returns:
            List of Role instances
        """
        async with self.db.session() as session:
            query = select(Role).options(selectinload(Role.operations))
            if not include_system:
                query = query.where(Role.is_system_role == False)
            query = query.order_by(Role.name)

            result = await session.execute(query)
            return list(result.scalars().all())

    async def update_role(
        self,
        role_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        edit_mode_enabled: Optional[bool] = None,
    ) -> Optional[Role]:
        """Update role properties.

        Args:
            role_id: Role ID to update
            name: New name (if provided)
            description: New description (if provided)
            edit_mode_enabled: New edit mode status (if provided)

        Returns:
            Updated Role instance or None if not found

        Raises:
            ValueError: If new name conflicts with existing role
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(Role).where(Role.id == role_id)
            )
            role = result.scalar_one_or_none()
            if not role:
                return None

            if name is not None and name != role.name:
                # Check name uniqueness
                existing = await session.execute(
                    select(Role).where(Role.name == name)
                )
                if existing.scalar_one_or_none():
                    raise ValueError(f"Role '{name}' already exists")
                role.name = name

            if description is not None:
                role.description = description
            if edit_mode_enabled is not None:
                role.edit_mode_enabled = edit_mode_enabled

            await session.commit()
            await session.refresh(role)

            logger.info(f"Updated role: {role.name}")
            return role

    async def delete_role(self, role_id: int) -> bool:
        """Delete a role.

        Args:
            role_id: Role ID to delete

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If trying to delete a system role
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(Role).where(Role.id == role_id)
            )
            role = result.scalar_one_or_none()
            if not role:
                return False

            if role.is_system_role:
                raise ValueError(f"Cannot delete system role '{role.name}'")

            await session.delete(role)
            await session.commit()

            logger.info(f"Deleted role: {role.name}")
            return True

    # ==================== Operations Management ====================

    async def set_role_operations(
        self, role_id: int, operation_names: List[str]
    ) -> Optional[Role]:
        """Set the allowed operations for a role (replaces existing).

        Args:
            role_id: Role ID
            operation_names: List of operation names to allow

        Returns:
            Updated Role instance or None if role not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(Role).where(Role.id == role_id)
            )
            role = result.scalar_one_or_none()
            if not role:
                return None

            # Remove existing operations
            await session.execute(
                delete(RoleOperation).where(RoleOperation.role_id == role_id)
            )

            # Add new operations
            for op_name in operation_names:
                role_op = RoleOperation(role_id=role_id, operation_name=op_name)
                session.add(role_op)

            await session.commit()

            logger.info(f"Updated operations for role {role.name}: {len(operation_names)} operations")
            return await self.get_role(role_id)

    async def add_role_operations(
        self, role_id: int, operation_names: List[str]
    ) -> Optional[Role]:
        """Add operations to a role (without removing existing).

        Args:
            role_id: Role ID
            operation_names: List of operation names to add

        Returns:
            Updated Role instance or None if role not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(Role).where(Role.id == role_id)
            )
            role = result.scalar_one_or_none()
            if not role:
                return None

            # Get existing operations
            existing_ops = {op.operation_name for op in role.operations}

            # Add only new operations
            for op_name in operation_names:
                if op_name not in existing_ops:
                    role_op = RoleOperation(role_id=role_id, operation_name=op_name)
                    session.add(role_op)

            await session.commit()

            return await self.get_role(role_id)

    async def remove_role_operations(
        self, role_id: int, operation_names: List[str]
    ) -> Optional[Role]:
        """Remove operations from a role.

        Args:
            role_id: Role ID
            operation_names: List of operation names to remove

        Returns:
            Updated Role instance or None if role not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(Role).where(Role.id == role_id)
            )
            if not result.scalar_one_or_none():
                return None

            await session.execute(
                delete(RoleOperation).where(
                    RoleOperation.role_id == role_id,
                    RoleOperation.operation_name.in_(operation_names)
                )
            )
            await session.commit()

            return await self.get_role(role_id)

    # ==================== Available Operations ====================

    async def get_all_available_operations(
        self,
        search: Optional[str] = None,
        api_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get all available operations from API endpoints.

        Args:
            search: Search term to filter by name/description
            api_name: Filter by API name (manage, analyze, infra, etc.)
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            Dictionary with total count and operations list
        """
        async with self.db.session() as session:
            query = select(APIEndpoint)

            # Apply filters
            if api_name:
                query = query.where(APIEndpoint.api_name == api_name)
            if search:
                search_term = f"%{search.lower()}%"
                query = query.where(
                    APIEndpoint.operation_id.ilike(search_term) |
                    APIEndpoint.method.ilike(search_term)
                )

            # Count total
            count_result = await session.execute(query)
            total = len(list(count_result.scalars().all()))

            # Get paginated results
            query = query.order_by(APIEndpoint.api_name, APIEndpoint.operation_id)
            query = query.offset(offset).limit(limit)

            result = await session.execute(query)
            endpoints = list(result.scalars().all())

            operations = []
            for ep in endpoints:
                operations.append({
                    "name": ep.operation_id,
                    "method": ep.method,
                    "path": ep.path,
                    "api_name": ep.api_name,
                    "description": ep.description or f"{ep.method} {ep.path}",
                })

            return {
                "total": total,
                "operations": operations,
            }

    async def get_operations_by_api(self) -> Dict[str, List[Dict[str, str]]]:
        """Get all operations grouped by API name.

        Returns:
            Dictionary with API names as keys and operation lists as values
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(APIEndpoint).order_by(APIEndpoint.api_name, APIEndpoint.operation_id)
            )
            endpoints = list(result.scalars().all())

            grouped: Dict[str, List[Dict[str, str]]] = {}
            for ep in endpoints:
                if ep.api_name not in grouped:
                    grouped[ep.api_name] = []
                grouped[ep.api_name].append({
                    "name": ep.operation_id,
                    "method": ep.http_method,
                    "path": ep.path,
                    "description": ep.description or f"{ep.http_method} {ep.path}",
                })

            return grouped

    async def get_api_names(self) -> List[str]:
        """Get list of unique API names.

        Returns:
            List of API name strings
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(APIEndpoint.api_name).distinct().order_by(APIEndpoint.api_name)
            )
            return [row[0] for row in result.all() if row[0]]

    async def count_operations(self) -> int:
        """Get total count of available operations.

        Returns:
            Operation count
        """
        async with self.db.session() as session:
            result = await session.execute(select(APIEndpoint))
            return len(list(result.scalars().all()))
