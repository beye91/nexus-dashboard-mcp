"""User authentication and management service."""

import logging
import secrets
from datetime import datetime, timedelta
from typing import List, Optional

import bcrypt
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from src.config.database import get_db
from src.models.user import User, UserSession
from src.models.role import Role, UserRole
from src.models.user_cluster import UserCluster
from src.models.cluster import Cluster

logger = logging.getLogger(__name__)

# Lazy import LDAP service to avoid circular imports
_ldap_service = None

def get_ldap_service():
    """Get or create LDAP service instance."""
    global _ldap_service
    if _ldap_service is None:
        from src.services.ldap_service import LDAPService
        _ldap_service = LDAPService()
    return _ldap_service


class UserService:
    """Service for user authentication and management."""

    # Session configuration
    SESSION_TOKEN_LENGTH = 64  # bytes (128 hex chars)
    SESSION_EXPIRY_HOURS = 24
    API_TOKEN_LENGTH = 32  # bytes (64 hex chars)

    def __init__(self):
        """Initialize user service."""
        self.db = get_db()

    # ==================== Password Hashing ====================

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash.

        Args:
            password: Plain text password to verify
            password_hash: Stored bcrypt hash

        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    # ==================== Token Generation ====================

    @staticmethod
    def generate_session_token() -> str:
        """Generate a secure session token.

        Returns:
            Random hex string token
        """
        return secrets.token_hex(UserService.SESSION_TOKEN_LENGTH)

    @staticmethod
    def generate_api_token() -> str:
        """Generate a secure API token for Claude Desktop auth.

        Returns:
            Random hex string token
        """
        return secrets.token_hex(UserService.API_TOKEN_LENGTH)

    # ==================== User CRUD ====================

    async def create_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        display_name: Optional[str] = None,
        is_superuser: bool = False,
        generate_api_token: bool = True,
    ) -> User:
        """Create a new user account.

        Args:
            username: Unique username
            password: Plain text password (will be hashed)
            email: Optional email address
            display_name: Optional display name
            is_superuser: If True, user has all permissions
            generate_api_token: If True, generate API token for Claude Desktop

        Returns:
            Created User instance

        Raises:
            ValueError: If username already exists
        """
        async with self.db.session() as session:
            # Check if username exists
            result = await session.execute(
                select(User).where(User.username == username)
            )
            if result.scalar_one_or_none():
                raise ValueError(f"Username '{username}' already exists")

            # Create user
            user = User(
                username=username,
                password_hash=self.hash_password(password),
                email=email,
                display_name=display_name or username,
                is_superuser=is_superuser,
                api_token=self.generate_api_token() if generate_api_token else None,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            logger.info(f"Created user: {username}")
            return user

    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID with roles and clusters loaded.

        Args:
            user_id: User ID

        Returns:
            User instance or None if not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(User)
                .options(
                    selectinload(User.roles).selectinload(Role.operations),
                    selectinload(User.clusters),
                )
                .where(User.id == user_id)
            )
            return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username with roles and clusters loaded.

        Args:
            username: Username to find

        Returns:
            User instance or None if not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(User)
                .options(
                    selectinload(User.roles).selectinload(Role.operations),
                    selectinload(User.clusters),
                )
                .where(User.username == username)
            )
            return result.scalar_one_or_none()

    async def get_user_by_api_token(self, api_token: str) -> Optional[User]:
        """Get user by API token (for Claude Desktop auth).

        Args:
            api_token: API token to find

        Returns:
            User instance or None if not found or inactive
        """
        if not api_token:
            return None

        async with self.db.session() as session:
            result = await session.execute(
                select(User)
                .options(
                    selectinload(User.roles).selectinload(Role.operations),
                    selectinload(User.clusters),
                )
                .where(User.api_token == api_token, User.is_active == True)
            )
            return result.scalar_one_or_none()

    async def list_users(self, active_only: bool = False) -> List[User]:
        """List all users.

        Args:
            active_only: If True, only return active users

        Returns:
            List of User instances
        """
        async with self.db.session() as session:
            query = select(User).options(
                selectinload(User.roles),
                selectinload(User.clusters),
            )
            if active_only:
                query = query.where(User.is_active == True)
            query = query.order_by(User.username)

            result = await session.execute(query)
            return list(result.scalars().all())

    async def update_user(
        self,
        user_id: int,
        email: Optional[str] = None,
        display_name: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_superuser: Optional[bool] = None,
        password: Optional[str] = None,
    ) -> Optional[User]:
        """Update user properties.

        Args:
            user_id: User ID to update
            email: New email (if provided)
            display_name: New display name (if provided)
            is_active: New active status (if provided)
            is_superuser: New superuser status (if provided)
            password: New password (if provided, will be hashed)

        Returns:
            Updated User instance or None if not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return None

            if email is not None:
                user.email = email
            if display_name is not None:
                user.display_name = display_name
            if is_active is not None:
                user.is_active = is_active
            if is_superuser is not None:
                user.is_superuser = is_superuser
            if password is not None:
                user.password_hash = self.hash_password(password)

            await session.commit()
            await session.refresh(user)

            logger.info(f"Updated user: {user.username}")
            return user

    async def delete_user(self, user_id: int) -> bool:
        """Delete a user account.

        Args:
            user_id: User ID to delete

        Returns:
            True if deleted, False if not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return False

            await session.delete(user)
            await session.commit()

            logger.info(f"Deleted user: {user.username}")
            return True

    async def regenerate_api_token(self, user_id: int) -> Optional[str]:
        """Regenerate API token for a user.

        Args:
            user_id: User ID

        Returns:
            New API token or None if user not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return None

            user.api_token = self.generate_api_token()
            await session.commit()

            logger.info(f"Regenerated API token for user: {user.username}")
            return user.api_token

    # ==================== Authentication ====================

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password.

        Authentication flow:
        1. Try local authentication first (always)
        2. If local fails and LDAP is enabled, try LDAP
        3. If LDAP succeeds, auto-create/update local user with auth_type='ldap'

        Args:
            username: Username
            password: Plain text password

        Returns:
            User instance if authenticated, None otherwise
        """
        # Step 1: Try local authentication first
        user = await self.get_user_by_username(username)

        if user:
            if not user.is_active:
                logger.warning(f"Authentication failed: user '{username}' is inactive")
                return None

            # For local users, verify password directly
            if user.auth_type == "local":
                if self.verify_password(password, user.password_hash):
                    await self._update_last_login(user.id)
                    logger.info(f"Local user authenticated: {username}")
                    return user
                else:
                    logger.warning(f"Authentication failed: invalid password for local user '{username}'")
                    return None

            # For LDAP users, verify against LDAP
            elif user.auth_type == "ldap":
                ldap_service = get_ldap_service()
                if ldap_service.is_available():
                    success, user_info = await ldap_service.authenticate(username, password)
                    if success:
                        await self._update_last_login(user.id)
                        logger.info(f"LDAP user authenticated: {username}")
                        return user
                    else:
                        logger.warning(f"LDAP authentication failed for: {username}")
                        return None
                else:
                    logger.warning(f"LDAP not available for user: {username}")
                    return None

        # Step 2: User not found locally, try LDAP if available
        ldap_service = get_ldap_service()
        if ldap_service.is_available():
            success, user_info = await ldap_service.authenticate(username, password)
            if success and user_info:
                # Auto-create user from LDAP
                user = await self._create_ldap_user(user_info)
                if user:
                    await self._update_last_login(user.id)
                    logger.info(f"New LDAP user authenticated and created: {username}")
                    return user

        logger.warning(f"Authentication failed: user '{username}' not found")
        return None

    async def _update_last_login(self, user_id: int) -> None:
        """Update last login timestamp for user."""
        async with self.db.session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            db_user = result.scalar_one_or_none()
            if db_user:
                db_user.last_login = datetime.utcnow()
                await session.commit()

    async def _create_ldap_user(self, user_info: dict) -> Optional[User]:
        """Create a local user from LDAP authentication info.

        Args:
            user_info: Dictionary with dn, username, email, display_name, groups, ldap_config_id

        Returns:
            Created User instance or None on error
        """
        try:
            async with self.db.session() as session:
                # Generate a random password hash (LDAP users can't use local auth)
                dummy_password = self.hash_password(secrets.token_hex(32))

                user = User(
                    username=user_info["username"],
                    password_hash=dummy_password,
                    email=user_info.get("email"),
                    display_name=user_info.get("display_name") or user_info["username"],
                    auth_type="ldap",
                    ldap_dn=user_info.get("dn"),
                    ldap_config_id=user_info.get("ldap_config_id"),
                    is_active=True,
                    api_token=self.generate_api_token(),
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)

                logger.info(f"Created LDAP user: {user_info['username']}")

                # Apply group mappings if groups provided
                if user_info.get("groups") and user_info.get("ldap_config_id"):
                    ldap_service = get_ldap_service()
                    await ldap_service._apply_group_mappings(
                        user.id,
                        user_info["ldap_config_id"],
                        user_info["groups"],
                    )

                return await self.get_user(user.id)
        except Exception as e:
            logger.error(f"Failed to create LDAP user: {e}")
            return None

    # ==================== Session Management ====================

    async def create_session(self, user: User) -> str:
        """Create a new session for a user.

        Args:
            user: User instance

        Returns:
            Session token string
        """
        token = self.generate_session_token()
        expires_at = datetime.utcnow() + timedelta(hours=self.SESSION_EXPIRY_HOURS)

        async with self.db.session() as session:
            user_session = UserSession(
                user_id=user.id,
                session_token=token,
                expires_at=expires_at,
            )
            session.add(user_session)
            await session.commit()

        logger.info(f"Created session for user: {user.username}")
        return token

    async def validate_session(self, token: str) -> Optional[User]:
        """Validate a session token and return associated user.

        Args:
            token: Session token to validate

        Returns:
            User instance if valid, None otherwise
        """
        if not token:
            return None

        async with self.db.session() as session:
            result = await session.execute(
                select(UserSession)
                .options(selectinload(UserSession.user).selectinload(User.roles).selectinload(Role.operations))
                .where(UserSession.session_token == token)
            )
            user_session = result.scalar_one_or_none()

            if not user_session:
                return None

            if user_session.is_expired():
                # Clean up expired session
                await session.delete(user_session)
                await session.commit()
                logger.debug(f"Cleaned up expired session")
                return None

            if not user_session.user.is_active:
                return None

            return user_session.user

    async def invalidate_session(self, token: str) -> bool:
        """Invalidate (logout) a session.

        Args:
            token: Session token to invalidate

        Returns:
            True if session was found and deleted
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(UserSession).where(UserSession.session_token == token)
            )
            user_session = result.scalar_one_or_none()

            if not user_session:
                return False

            await session.delete(user_session)
            await session.commit()

            logger.info("Session invalidated")
            return True

    async def invalidate_all_sessions(self, user_id: int) -> int:
        """Invalidate all sessions for a user.

        Args:
            user_id: User ID

        Returns:
            Number of sessions invalidated
        """
        async with self.db.session() as session:
            result = await session.execute(
                delete(UserSession).where(UserSession.user_id == user_id)
            )
            await session.commit()

            count = result.rowcount
            logger.info(f"Invalidated {count} sessions for user {user_id}")
            return count

    async def cleanup_expired_sessions(self) -> int:
        """Remove all expired sessions from database.

        Returns:
            Number of sessions cleaned up
        """
        async with self.db.session() as session:
            result = await session.execute(
                delete(UserSession).where(UserSession.expires_at < datetime.utcnow())
            )
            await session.commit()

            count = result.rowcount
            if count > 0:
                logger.info(f"Cleaned up {count} expired sessions")
            return count

    # ==================== Role Assignment ====================

    async def assign_roles(self, user_id: int, role_ids: List[int]) -> Optional[User]:
        """Assign roles to a user (replaces existing role assignments).

        Args:
            user_id: User ID
            role_ids: List of role IDs to assign

        Returns:
            Updated User instance or None if user not found
        """
        async with self.db.session() as session:
            # Get user
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return None

            # Remove existing role assignments
            await session.execute(
                delete(UserRole).where(UserRole.user_id == user_id)
            )

            # Add new role assignments
            for role_id in role_ids:
                user_role = UserRole(user_id=user_id, role_id=role_id)
                session.add(user_role)

            await session.commit()

            # Reload user with roles
            return await self.get_user(user_id)

    async def count_users(self) -> int:
        """Get total number of users.

        Returns:
            User count
        """
        async with self.db.session() as session:
            result = await session.execute(select(User))
            return len(list(result.scalars().all()))

    async def has_any_users(self) -> bool:
        """Check if any users exist in the system.

        Returns:
            True if at least one user exists
        """
        async with self.db.session() as session:
            result = await session.execute(select(User).limit(1))
            return result.scalar_one_or_none() is not None

    # ==================== Cluster Assignment ====================

    async def assign_clusters(self, user_id: int, cluster_ids: List[int]) -> Optional[User]:
        """Assign clusters to a user (replaces existing cluster assignments).

        Args:
            user_id: User ID
            cluster_ids: List of cluster IDs to assign (empty list = no cluster access)

        Returns:
            Updated User instance or None if user not found
        """
        async with self.db.session() as session:
            # Verify user exists
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return None

            # Remove existing cluster assignments
            await session.execute(
                delete(UserCluster).where(UserCluster.user_id == user_id)
            )

            # Add new cluster assignments
            for cluster_id in cluster_ids:
                user_cluster = UserCluster(user_id=user_id, cluster_id=cluster_id)
                session.add(user_cluster)

            await session.commit()

            logger.info(f"Assigned {len(cluster_ids)} clusters to user {user_id}")

            # Reload user with clusters
            return await self.get_user(user_id)

    async def get_user_clusters(self, user_id: int) -> List[Cluster]:
        """Get all clusters assigned to a user.

        Args:
            user_id: User ID

        Returns:
            List of Cluster instances
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(Cluster)
                .join(UserCluster, UserCluster.cluster_id == Cluster.id)
                .where(UserCluster.user_id == user_id)
                .order_by(Cluster.name)
            )
            return list(result.scalars().all())

    async def add_cluster_to_user(self, user_id: int, cluster_id: int) -> bool:
        """Add a single cluster to a user (without removing existing).

        Args:
            user_id: User ID
            cluster_id: Cluster ID to add

        Returns:
            True if added, False if already assigned or user/cluster not found
        """
        async with self.db.session() as session:
            # Check if already assigned
            result = await session.execute(
                select(UserCluster).where(
                    UserCluster.user_id == user_id,
                    UserCluster.cluster_id == cluster_id
                )
            )
            if result.scalar_one_or_none():
                return False  # Already assigned

            # Add assignment
            user_cluster = UserCluster(user_id=user_id, cluster_id=cluster_id)
            session.add(user_cluster)
            await session.commit()

            logger.info(f"Added cluster {cluster_id} to user {user_id}")
            return True

    async def remove_cluster_from_user(self, user_id: int, cluster_id: int) -> bool:
        """Remove a single cluster from a user.

        Args:
            user_id: User ID
            cluster_id: Cluster ID to remove

        Returns:
            True if removed, False if not assigned
        """
        async with self.db.session() as session:
            result = await session.execute(
                delete(UserCluster).where(
                    UserCluster.user_id == user_id,
                    UserCluster.cluster_id == cluster_id
                )
            )
            await session.commit()

            if result.rowcount > 0:
                logger.info(f"Removed cluster {cluster_id} from user {user_id}")
                return True
            return False
