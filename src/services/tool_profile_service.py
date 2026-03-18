"""Tool profile management service.

Provides CRUD operations for tool profiles and the resolution logic that
determines which tools/operations an authenticated MCP user can access.

Resolution priority:
  1. Tool profile assigned to user (even for superusers)
  2. Superuser with no profile -> all tools
  3. Role-based operations from assigned roles
  4. No profile and no roles -> no tools (empty list)
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select, delete

from src.config.database import get_db
from src.models.tool_profile import ToolProfile, ToolProfileOperation
from src.models.user import User

logger = logging.getLogger(__name__)


class ToolProfileService:
    """Service for tool profile management and tool resolution."""

    def __init__(self):
        """Initialize tool profile service."""
        self.db = get_db()

    # ==================== CRUD ====================

    async def create_profile(
        self,
        name: str,
        description: Optional[str] = None,
        max_tools: int = 100,
        operations: Optional[List[str]] = None,
    ) -> ToolProfile:
        """Create a new tool profile.

        Args:
            name: Unique profile name
            description: Human-readable description
            max_tools: Maximum tools to expose (0 = no limit)
            operations: Initial list of allowed operation names

        Returns:
            Created ToolProfile instance

        Raises:
            ValueError: If profile name already exists
        """
        async with self.db.session() as session:
            # Enforce unique name
            result = await session.execute(
                select(ToolProfile).where(ToolProfile.name == name)
            )
            if result.scalar_one_or_none():
                raise ValueError(f"Tool profile '{name}' already exists")

            profile = ToolProfile(
                name=name,
                description=description,
                max_tools=max_tools,
            )
            session.add(profile)
            await session.flush()  # Materialise the profile ID before adding operations

            if operations:
                for op_name in operations:
                    op = ToolProfileOperation(
                        profile_id=profile.id,
                        operation_name=op_name,
                    )
                    session.add(op)

            await session.commit()
            await session.refresh(profile)

            logger.info(
                f"Created tool profile '{name}' with {len(operations) if operations else 0} operations"
            )
            return profile

    async def get_profile(self, profile_id: int) -> Optional[ToolProfile]:
        """Get a tool profile by ID with its operations loaded.

        Args:
            profile_id: Tool profile primary key

        Returns:
            ToolProfile instance or None if not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(ToolProfile).where(ToolProfile.id == profile_id)
            )
            return result.scalar_one_or_none()

    async def get_profile_by_name(self, name: str) -> Optional[ToolProfile]:
        """Get a tool profile by its unique name.

        Args:
            name: Profile name

        Returns:
            ToolProfile instance or None if not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(ToolProfile).where(ToolProfile.name == name)
            )
            return result.scalar_one_or_none()

    async def list_profiles(self, active_only: bool = False) -> List[ToolProfile]:
        """List all tool profiles.

        Args:
            active_only: When True, only return profiles with is_active=True

        Returns:
            Ordered list of ToolProfile instances
        """
        async with self.db.session() as session:
            query = select(ToolProfile)
            if active_only:
                query = query.where(ToolProfile.is_active == True)
            query = query.order_by(ToolProfile.name)

            result = await session.execute(query)
            return list(result.scalars().all())

    async def update_profile(
        self,
        profile_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        max_tools: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[ToolProfile]:
        """Update tool profile attributes.

        Args:
            profile_id: Profile ID to update
            name: New name (checked for uniqueness)
            description: New description
            max_tools: New max tools limit
            is_active: New active status

        Returns:
            Updated ToolProfile or None if not found

        Raises:
            ValueError: If new name conflicts with an existing profile
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(ToolProfile).where(ToolProfile.id == profile_id)
            )
            profile = result.scalar_one_or_none()
            if not profile:
                return None

            if name is not None and name != profile.name:
                existing = await session.execute(
                    select(ToolProfile).where(ToolProfile.name == name)
                )
                if existing.scalar_one_or_none():
                    raise ValueError(f"Tool profile '{name}' already exists")
                profile.name = name

            if description is not None:
                profile.description = description
            if max_tools is not None:
                profile.max_tools = max_tools
            if is_active is not None:
                profile.is_active = is_active

            await session.commit()
            await session.refresh(profile)

            logger.info(f"Updated tool profile '{profile.name}' (id={profile_id})")
            return profile

    async def delete_profile(self, profile_id: int) -> bool:
        """Delete a tool profile and cascade-remove its operations.

        Users assigned this profile will have their tool_profile_id set to NULL
        automatically via the ON DELETE SET NULL foreign key constraint.

        Args:
            profile_id: Profile ID to delete

        Returns:
            True if deleted, False if not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(ToolProfile).where(ToolProfile.id == profile_id)
            )
            profile = result.scalar_one_or_none()
            if not profile:
                return False

            await session.delete(profile)
            await session.commit()

            logger.info(f"Deleted tool profile id={profile_id}")
            return True

    # ==================== Operations Management ====================

    async def set_profile_operations(
        self, profile_id: int, operation_names: List[str]
    ) -> Optional[ToolProfile]:
        """Replace the full set of allowed operations for a profile.

        This is a destructive replace: all existing operations are removed and
        the provided list becomes the new set.

        Args:
            profile_id: Tool profile ID
            operation_names: Complete list of operation names to allow

        Returns:
            Updated ToolProfile or None if profile not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(ToolProfile).where(ToolProfile.id == profile_id)
            )
            profile = result.scalar_one_or_none()
            if not profile:
                return None

            # Replace all operations atomically
            await session.execute(
                delete(ToolProfileOperation).where(
                    ToolProfileOperation.profile_id == profile_id
                )
            )

            for op_name in operation_names:
                session.add(
                    ToolProfileOperation(
                        profile_id=profile_id,
                        operation_name=op_name,
                    )
                )

            await session.commit()

            logger.info(
                f"Set {len(operation_names)} operations on tool profile id={profile_id}"
            )
            return await self.get_profile(profile_id)

    # ==================== User Assignment ====================

    async def assign_profile_to_user(
        self, user_id: int, profile_id: Optional[int]
    ) -> bool:
        """Assign (or remove) a tool profile from a user.

        Args:
            user_id: User ID to update
            profile_id: Tool profile ID to assign, or None to clear the assignment

        Returns:
            True on success, False if user or profile not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                logger.warning(f"assign_profile_to_user: user id={user_id} not found")
                return False

            # Validate that the profile exists when not clearing
            if profile_id is not None:
                profile_result = await session.execute(
                    select(ToolProfile).where(ToolProfile.id == profile_id)
                )
                if not profile_result.scalar_one_or_none():
                    logger.warning(
                        f"assign_profile_to_user: tool profile id={profile_id} not found"
                    )
                    return False

            user.tool_profile_id = profile_id
            await session.commit()

            action = f"assigned profile id={profile_id}" if profile_id else "cleared profile"
            logger.info(f"User id={user_id}: {action}")
            return True

    async def get_user_profile(self, user_id: int) -> Optional[ToolProfile]:
        """Get the tool profile assigned to a user.

        Args:
            user_id: User ID

        Returns:
            ToolProfile or None if user has no profile or user not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user or not user.tool_profile_id:
                return None

            profile_result = await session.execute(
                select(ToolProfile).where(ToolProfile.id == user.tool_profile_id)
            )
            return profile_result.scalar_one_or_none()

    # ==================== Tool Resolution ====================

    async def resolve_tools_for_user(
        self, user: User, all_tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Determine which tools a user is allowed to see.

        Resolution order:
          1. User has a tool profile -> filter to profile operations
          2. User is superuser (no profile) -> all tools
          3. User has role operations -> filter to role operations
          4. No profile, no roles, not superuser -> no tools

        Args:
            user: Authenticated User ORM instance
            all_tools: Full list of tool dictionaries from the MCP server

        Returns:
            Filtered list of tool dictionaries
        """
        # 1. Tool profile takes priority (even for superusers who are profile-restricted)
        if user.tool_profile_id and hasattr(user, "tool_profile") and user.tool_profile:
            profile = user.tool_profile
            if profile.is_active:
                # max_tools == 0 signals Full Access (no operation-level filtering)
                if profile.max_tools == 0 and not profile.operations:
                    logger.debug(
                        f"User '{user.username}' has Full Access profile '{profile.name}'"
                    )
                    return all_tools

                profile_ops = profile.get_operation_names()
                filtered = [t for t in all_tools if t.get("name") in profile_ops]
                logger.debug(
                    f"Tool profile '{profile.name}' filtered {len(all_tools)} -> "
                    f"{len(filtered)} tools for user '{user.username}'"
                )
                return filtered
            else:
                logger.warning(
                    f"User '{user.username}' has inactive profile '{profile.name}', "
                    "falling through to role-based filtering"
                )

        # 2. Superuser without an active profile -> full access
        if user.is_superuser:
            logger.debug(f"User '{user.username}' is superuser, returning all tools")
            return all_tools

        # 3. Role-based filtering
        role_ops = user.get_all_operations()
        if not role_ops:
            logger.info(
                f"User '{user.username}' has no allowed operations (no profile, no roles)"
            )
            return []

        filtered = [t for t in all_tools if t.get("name") in role_ops]
        logger.debug(
            f"Role-based filter: {len(all_tools)} -> {len(filtered)} tools "
            f"for user '{user.username}'"
        )
        return filtered
