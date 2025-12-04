"""LDAP authentication and synchronization service.

This service provides optional LDAP integration for user authentication.
Local authentication remains the default and is always available.
"""

import logging
import secrets
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from src.config.database import get_db
from src.models.ldap_config import LDAPConfig, LDAPGroupRoleMapping, LDAPGroupClusterMapping
from src.models.user import User
from src.models.user_cluster import UserCluster
from src.models.role import Role, UserRole
from src.utils.encryption import encrypt_password, decrypt_password

logger = logging.getLogger(__name__)

# LDAP3 is optional - only import if available
try:
    import ldap3
    from ldap3 import Server, Connection, ALL, SIMPLE, SUBTREE
    from ldap3.core.exceptions import LDAPException, LDAPBindError
    LDAP_AVAILABLE = True
except ImportError:
    LDAP_AVAILABLE = False
    logger.warning("ldap3 package not installed. LDAP authentication will not be available.")


class LDAPService:
    """Service for LDAP operations.

    LDAP is optional - if ldap3 is not installed or LDAP is not configured,
    the service methods will return appropriate errors.
    """

    def __init__(self):
        """Initialize LDAP service."""
        self.db = get_db()

    def is_available(self) -> bool:
        """Check if LDAP functionality is available."""
        return LDAP_AVAILABLE

    # ==================== Configuration CRUD ====================

    async def create_config(
        self,
        name: str,
        server_url: str,
        base_dn: str,
        bind_dn: Optional[str] = None,
        bind_password: Optional[str] = None,
        **kwargs,
    ) -> LDAPConfig:
        """Create a new LDAP configuration.

        Args:
            name: Unique configuration name
            server_url: LDAP server URL (ldap:// or ldaps://)
            base_dn: Base DN for searches
            bind_dn: Optional bind DN for admin searches
            bind_password: Optional bind password (will be encrypted)
            **kwargs: Additional configuration fields

        Returns:
            Created LDAPConfig instance
        """
        async with self.db.session() as session:
            # Encrypt bind password if provided
            encrypted_password = None
            if bind_password:
                encrypted_password = encrypt_password(bind_password)

            config = LDAPConfig(
                name=name,
                server_url=server_url,
                base_dn=base_dn,
                bind_dn=bind_dn,
                bind_password_encrypted=encrypted_password,
                **kwargs,
            )
            session.add(config)
            await session.commit()
            await session.refresh(config)

            logger.info(f"Created LDAP config: {name}")
            return config

    async def get_config(self, config_id: int) -> Optional[LDAPConfig]:
        """Get LDAP configuration by ID."""
        async with self.db.session() as session:
            result = await session.execute(
                select(LDAPConfig)
                .options(
                    selectinload(LDAPConfig.role_mappings),
                    selectinload(LDAPConfig.cluster_mappings),
                )
                .where(LDAPConfig.id == config_id)
            )
            return result.scalar_one_or_none()

    async def get_primary_config(self) -> Optional[LDAPConfig]:
        """Get the primary enabled LDAP configuration."""
        async with self.db.session() as session:
            result = await session.execute(
                select(LDAPConfig)
                .where(LDAPConfig.is_enabled == True, LDAPConfig.is_primary == True)
            )
            return result.scalar_one_or_none()

    async def list_configs(self) -> List[LDAPConfig]:
        """List all LDAP configurations."""
        async with self.db.session() as session:
            result = await session.execute(
                select(LDAPConfig)
                .options(
                    selectinload(LDAPConfig.role_mappings),
                    selectinload(LDAPConfig.cluster_mappings),
                )
                .order_by(LDAPConfig.name)
            )
            return list(result.scalars().all())

    async def update_config(
        self,
        config_id: int,
        bind_password: Optional[str] = None,
        **kwargs,
    ) -> Optional[LDAPConfig]:
        """Update LDAP configuration."""
        async with self.db.session() as session:
            result = await session.execute(
                select(LDAPConfig).where(LDAPConfig.id == config_id)
            )
            config = result.scalar_one_or_none()
            if not config:
                return None

            # Handle bind password separately
            if bind_password is not None:
                if bind_password:
                    config.bind_password_encrypted = encrypt_password(bind_password)
                else:
                    config.bind_password_encrypted = None

            # Update other fields
            for key, value in kwargs.items():
                if hasattr(config, key) and key != "bind_password_encrypted":
                    setattr(config, key, value)

            # If setting as primary, unset other primaries
            if kwargs.get("is_primary"):
                await session.execute(
                    select(LDAPConfig)
                    .where(LDAPConfig.id != config_id)
                )
                # Unset other primaries
                other_configs = await session.execute(
                    select(LDAPConfig).where(LDAPConfig.id != config_id, LDAPConfig.is_primary == True)
                )
                for other in other_configs.scalars().all():
                    other.is_primary = False

            await session.commit()
            await session.refresh(config)

            logger.info(f"Updated LDAP config: {config.name}")
            return config

    async def delete_config(self, config_id: int) -> bool:
        """Delete LDAP configuration."""
        async with self.db.session() as session:
            result = await session.execute(
                select(LDAPConfig).where(LDAPConfig.id == config_id)
            )
            config = result.scalar_one_or_none()
            if not config:
                return False

            await session.delete(config)
            await session.commit()

            logger.info(f"Deleted LDAP config: {config.name}")
            return True

    # ==================== Connection Testing ====================

    async def test_connection(self, config_id: int) -> Dict[str, Any]:
        """Test LDAP connection and return diagnostic info.

        Args:
            config_id: ID of the LDAP configuration to test

        Returns:
            Dictionary with test results
        """
        if not LDAP_AVAILABLE:
            return {
                "success": False,
                "error": "LDAP support not available. Install ldap3 package.",
                "error_type": "DependencyError",
            }

        config = await self.get_config(config_id)
        if not config:
            return {
                "success": False,
                "error": "Configuration not found",
                "error_type": "NotFound",
            }

        try:
            conn = self._get_connection(config)

            # Get server info
            server_info = {}
            if conn.server.info:
                server_info = {
                    "vendor": str(conn.server.info.vendor_name or "Unknown"),
                    "version": str(conn.server.info.vendor_version or "Unknown"),
                    "naming_contexts": list(conn.server.info.naming_contexts or []),
                }

            # Test user search
            user_count = 0
            search_base = self._get_user_search_base(config)

            conn.search(
                search_base,
                config.user_search_filter,
                search_scope=SUBTREE,
                attributes=[config.username_attribute],
                size_limit=100,
            )
            user_count = len(conn.entries)

            conn.unbind()

            return {
                "success": True,
                "server_info": server_info,
                "users_found": user_count,
                "message": f"Connection successful. Found {user_count} users (limited to 100).",
            }

        except LDAPBindError as e:
            return {
                "success": False,
                "error": f"Bind failed: {str(e)}",
                "error_type": "BindError",
            }
        except LDAPException as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }
        except Exception as e:
            logger.exception("LDAP connection test failed")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    # ==================== Authentication ====================

    async def authenticate(
        self,
        username: str,
        password: str,
        config_id: Optional[int] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Authenticate user against LDAP.

        This is called AFTER local authentication fails and if LDAP is enabled.

        Args:
            username: Username to authenticate
            password: Password to verify
            config_id: Optional specific LDAP config ID (uses primary if not specified)

        Returns:
            Tuple of (success, user_info_dict)
        """
        if not LDAP_AVAILABLE:
            return False, None

        # Get LDAP config
        if config_id:
            config = await self.get_config(config_id)
        else:
            config = await self.get_primary_config()

        if not config or not config.is_enabled:
            return False, None

        try:
            # First, find the user DN using service account
            conn = self._get_connection(config)

            search_base = self._get_user_search_base(config)
            search_filter = f"(&{config.user_search_filter}({config.username_attribute}={ldap3.utils.conv.escape_filter_chars(username)}))"

            # Build attribute list - memberOf is optional
            auth_attributes = [
                config.username_attribute,
                config.email_attribute,
                config.display_name_attribute,
            ]

            # Try with memberOf first, fall back without it if not supported
            try:
                conn.search(
                    search_base,
                    search_filter,
                    search_scope=SUBTREE,
                    attributes=auth_attributes + [config.member_of_attribute],
                )
            except LDAPException as member_err:
                if "invalid attribute" in str(member_err).lower() or "memberof" in str(member_err).lower():
                    logger.warning(f"memberOf attribute not supported for auth: {member_err}")
                    conn.search(
                        search_base,
                        search_filter,
                        search_scope=SUBTREE,
                        attributes=auth_attributes,
                    )
                else:
                    raise

            if not conn.entries:
                conn.unbind()
                logger.debug(f"LDAP user not found: {username}")
                return False, None

            user_entry = conn.entries[0]
            user_dn = user_entry.entry_dn
            conn.unbind()

            # Try to bind as the user to verify password
            user_conn = self._get_connection(config, user_dn, password)
            user_conn.unbind()

            # Extract user info
            user_info = {
                "dn": user_dn,
                "username": self._get_attr(user_entry, config.username_attribute, username),
                "email": self._get_attr(user_entry, config.email_attribute),
                "display_name": self._get_attr(user_entry, config.display_name_attribute),
                "groups": self._extract_groups(user_entry, config),
                "ldap_config_id": config.id,
            }

            logger.info(f"LDAP authentication successful for: {username}")
            return True, user_info

        except LDAPBindError:
            logger.debug(f"LDAP bind failed for user: {username}")
            return False, None
        except LDAPException as e:
            logger.warning(f"LDAP authentication error for {username}: {e}")
            return False, None
        except Exception as e:
            logger.exception(f"Unexpected LDAP error for {username}")
            return False, None

    # ==================== User Synchronization ====================

    async def sync_users(self, config_id: int) -> Dict[str, Any]:
        """Sync users from LDAP to local database.

        Args:
            config_id: LDAP configuration ID

        Returns:
            Dictionary with sync results
        """
        if not LDAP_AVAILABLE:
            return {
                "success": False,
                "error": "LDAP support not available",
            }

        config = await self.get_config(config_id)
        if not config:
            return {"success": False, "error": "Configuration not found"}

        try:
            conn = self._get_connection(config)

            search_base = self._get_user_search_base(config)

            # Build attribute list - memberOf is optional since not all LDAP servers support it
            search_attributes = [
                config.username_attribute,
                config.email_attribute,
                config.display_name_attribute,
            ]

            # Try with memberOf first, fall back without it if not supported
            try:
                conn.search(
                    search_base,
                    config.user_search_filter,
                    search_scope=SUBTREE,
                    attributes=search_attributes + [config.member_of_attribute],
                )
            except LDAPException as e:
                if "invalid attribute" in str(e).lower() or "memberof" in str(e).lower():
                    logger.warning(f"memberOf attribute not supported, syncing without group information: {e}")
                    conn.search(
                        search_base,
                        config.user_search_filter,
                        search_scope=SUBTREE,
                        attributes=search_attributes,
                    )
                else:
                    raise

            created = 0
            updated = 0
            errors = []

            for entry in conn.entries:
                try:
                    result = await self._sync_user_entry(config, entry)
                    if result == "created":
                        created += 1
                    elif result == "updated":
                        updated += 1
                except Exception as e:
                    errors.append(f"{entry.entry_dn}: {str(e)}")

            conn.unbind()

            # Update sync status
            await self._update_sync_status(
                config_id,
                status="success" if not errors else "partial",
                message=f"Created: {created}, Updated: {updated}, Errors: {len(errors)}",
                created=created,
                updated=updated,
            )

            return {
                "success": True,
                "created": created,
                "updated": updated,
                "errors": errors[:10],  # Limit error list
                "total_errors": len(errors),
            }

        except LDAPException as e:
            await self._update_sync_status(
                config_id,
                status="failed",
                message=str(e),
            )
            return {"success": False, "error": str(e)}

    async def _sync_user_entry(self, config: LDAPConfig, entry) -> str:
        """Sync a single LDAP user entry to database.

        Returns: "created", "updated", or "skipped"
        """
        username = self._get_attr(entry, config.username_attribute)
        if not username:
            return "skipped"

        async with self.db.session() as session:
            # Check if user exists
            result = await session.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()

            email = self._get_attr(entry, config.email_attribute)
            display_name = self._get_attr(entry, config.display_name_attribute)
            groups = self._extract_groups(entry, config)

            if user:
                # Update existing user
                if user.auth_type == "ldap":
                    user.email = email
                    user.display_name = display_name
                    user.ldap_dn = entry.entry_dn
                    user.ldap_config_id = config.id
                    await session.commit()

                    # Update role and cluster mappings
                    await self._apply_group_mappings(user.id, config.id, groups)

                    return "updated"
                return "skipped"  # Don't overwrite local users
            else:
                # Create new user if auto_create_users is enabled
                if not config.auto_create_users:
                    return "skipped"

                # Generate a random password hash (LDAP users can't use local auth)
                import bcrypt
                dummy_password = bcrypt.hashpw(
                    secrets.token_bytes(32),
                    bcrypt.gensalt()
                ).decode()

                user = User(
                    username=username,
                    password_hash=dummy_password,
                    email=email,
                    display_name=display_name,
                    auth_type="ldap",
                    ldap_dn=entry.entry_dn,
                    ldap_config_id=config.id,
                    is_active=True,
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)

                # Apply default role if configured
                if config.default_role_id:
                    user_role = UserRole(user_id=user.id, role_id=config.default_role_id)
                    session.add(user_role)
                    await session.commit()

                # Apply group mappings
                await self._apply_group_mappings(user.id, config.id, groups)

                return "created"

    async def _apply_group_mappings(
        self,
        user_id: int,
        config_id: int,
        groups: List[str],
    ) -> None:
        """Apply LDAP group to role/cluster mappings for a user."""
        async with self.db.session() as session:
            # Get role mappings for this config
            role_result = await session.execute(
                select(LDAPGroupRoleMapping).where(
                    LDAPGroupRoleMapping.ldap_config_id == config_id
                )
            )
            role_mappings = list(role_result.scalars().all())

            # Get cluster mappings for this config
            cluster_result = await session.execute(
                select(LDAPGroupClusterMapping).where(
                    LDAPGroupClusterMapping.ldap_config_id == config_id
                )
            )
            cluster_mappings = list(cluster_result.scalars().all())

            # Find matching roles
            role_ids = set()
            for mapping in role_mappings:
                if mapping.ldap_group_dn in groups:
                    role_ids.add(mapping.role_id)

            # Find matching clusters
            cluster_ids = set()
            for mapping in cluster_mappings:
                if mapping.ldap_group_dn in groups:
                    cluster_ids.add(mapping.cluster_id)

            # Update user roles (add only, don't remove existing)
            for role_id in role_ids:
                existing = await session.execute(
                    select(UserRole).where(
                        UserRole.user_id == user_id,
                        UserRole.role_id == role_id
                    )
                )
                if not existing.scalar_one_or_none():
                    session.add(UserRole(user_id=user_id, role_id=role_id))

            # Update user clusters (add only, don't remove existing)
            for cluster_id in cluster_ids:
                existing = await session.execute(
                    select(UserCluster).where(
                        UserCluster.user_id == user_id,
                        UserCluster.cluster_id == cluster_id
                    )
                )
                if not existing.scalar_one_or_none():
                    session.add(UserCluster(user_id=user_id, cluster_id=cluster_id))

            await session.commit()

    async def _update_sync_status(
        self,
        config_id: int,
        status: str,
        message: str,
        created: int = 0,
        updated: int = 0,
    ) -> None:
        """Update sync status on LDAP config."""
        async with self.db.session() as session:
            result = await session.execute(
                select(LDAPConfig).where(LDAPConfig.id == config_id)
            )
            config = result.scalar_one_or_none()
            if config:
                config.last_sync_at = datetime.utcnow()
                config.last_sync_status = status
                config.last_sync_message = message
                config.last_sync_users_created = created
                config.last_sync_users_updated = updated
                await session.commit()

    # ==================== Group Discovery ====================

    async def discover_groups(self, config_id: int) -> List[Dict[str, str]]:
        """Discover available groups from LDAP server.

        Args:
            config_id: LDAP configuration ID

        Returns:
            List of group dictionaries with dn, name, description
        """
        if not LDAP_AVAILABLE:
            return []

        config = await self.get_config(config_id)
        if not config:
            return []

        try:
            conn = self._get_connection(config)

            search_base = config.group_search_base or config.base_dn
            if config.group_search_base and not config.group_search_base.endswith(config.base_dn):
                search_base = f"{config.group_search_base},{config.base_dn}"

            conn.search(
                search_base,
                config.group_search_filter,
                search_scope=SUBTREE,
                attributes=[config.group_name_attribute, "description"],
            )

            groups = []
            for entry in conn.entries:
                groups.append({
                    "dn": entry.entry_dn,
                    "name": self._get_attr(entry, config.group_name_attribute, ""),
                    "description": self._get_attr(entry, "description"),
                })

            conn.unbind()
            return groups

        except LDAPException as e:
            logger.error(f"Failed to discover groups: {e}")
            return []

    # ==================== Group Mapping CRUD ====================

    async def add_role_mapping(
        self,
        config_id: int,
        ldap_group_dn: str,
        ldap_group_name: str,
        role_id: int,
    ) -> Optional[LDAPGroupRoleMapping]:
        """Add LDAP group to role mapping."""
        async with self.db.session() as session:
            mapping = LDAPGroupRoleMapping(
                ldap_config_id=config_id,
                ldap_group_dn=ldap_group_dn,
                ldap_group_name=ldap_group_name,
                role_id=role_id,
            )
            session.add(mapping)
            await session.commit()
            await session.refresh(mapping)
            return mapping

    async def delete_role_mapping(self, mapping_id: int) -> bool:
        """Delete LDAP group to role mapping."""
        async with self.db.session() as session:
            result = await session.execute(
                select(LDAPGroupRoleMapping).where(LDAPGroupRoleMapping.id == mapping_id)
            )
            mapping = result.scalar_one_or_none()
            if not mapping:
                return False
            await session.delete(mapping)
            await session.commit()
            return True

    async def add_cluster_mapping(
        self,
        config_id: int,
        ldap_group_dn: str,
        ldap_group_name: str,
        cluster_id: int,
    ) -> Optional[LDAPGroupClusterMapping]:
        """Add LDAP group to cluster mapping."""
        async with self.db.session() as session:
            mapping = LDAPGroupClusterMapping(
                ldap_config_id=config_id,
                ldap_group_dn=ldap_group_dn,
                ldap_group_name=ldap_group_name,
                cluster_id=cluster_id,
            )
            session.add(mapping)
            await session.commit()
            await session.refresh(mapping)
            return mapping

    async def delete_cluster_mapping(self, mapping_id: int) -> bool:
        """Delete LDAP group to cluster mapping."""
        async with self.db.session() as session:
            result = await session.execute(
                select(LDAPGroupClusterMapping).where(LDAPGroupClusterMapping.id == mapping_id)
            )
            mapping = result.scalar_one_or_none()
            if not mapping:
                return False
            await session.delete(mapping)
            await session.commit()
            return True

    async def get_role_mappings(self, config_id: int) -> List[LDAPGroupRoleMapping]:
        """Get all role mappings for a config."""
        async with self.db.session() as session:
            result = await session.execute(
                select(LDAPGroupRoleMapping)
                .options(selectinload(LDAPGroupRoleMapping.role))
                .where(LDAPGroupRoleMapping.ldap_config_id == config_id)
            )
            return list(result.scalars().all())

    async def get_cluster_mappings(self, config_id: int) -> List[LDAPGroupClusterMapping]:
        """Get all cluster mappings for a config."""
        async with self.db.session() as session:
            result = await session.execute(
                select(LDAPGroupClusterMapping)
                .options(selectinload(LDAPGroupClusterMapping.cluster))
                .where(LDAPGroupClusterMapping.ldap_config_id == config_id)
            )
            return list(result.scalars().all())

    # ==================== Helper Methods ====================

    def _get_connection(
        self,
        config: LDAPConfig,
        user_dn: Optional[str] = None,
        password: Optional[str] = None,
    ) -> "Connection":
        """Create LDAP connection.

        If user_dn/password provided, bind as that user.
        Otherwise, bind as the configured bind_dn.
        """
        if not LDAP_AVAILABLE:
            raise RuntimeError("LDAP support not available")

        use_ssl = config.use_ssl or config.server_url.startswith("ldaps://")
        server = Server(
            config.server_url,
            get_info=ALL,
            use_ssl=use_ssl,
        )

        if user_dn and password:
            # User authentication
            bind_dn = user_dn
            bind_password = password
        else:
            # Service account binding
            bind_dn = config.bind_dn
            bind_password = decrypt_password(config.bind_password_encrypted) if config.bind_password_encrypted else None

        conn = Connection(
            server,
            user=bind_dn,
            password=bind_password,
            authentication=SIMPLE,
            auto_bind=True,
        )

        if config.use_starttls and not use_ssl:
            conn.start_tls()

        return conn

    def _get_user_search_base(self, config: LDAPConfig) -> str:
        """Get the full search base for user searches."""
        if config.user_search_base:
            if config.user_search_base.endswith(config.base_dn):
                return config.user_search_base
            return f"{config.user_search_base},{config.base_dn}"
        return config.base_dn

    def _get_attr(self, entry, attr_name: str, default: Optional[str] = None) -> Optional[str]:
        """Safely get attribute value from LDAP entry."""
        try:
            value = getattr(entry, attr_name, None)
            if value is None:
                return default
            if isinstance(value, (list, tuple)):
                return str(value[0]) if value else default
            return str(value) if value else default
        except Exception:
            return default

    def _extract_groups(self, entry, config: LDAPConfig) -> List[str]:
        """Extract group DNs from user entry."""
        try:
            member_of = getattr(entry, config.member_of_attribute, None)
            if member_of is None:
                return []
            if isinstance(member_of, str):
                return [member_of]
            return list(member_of) if member_of else []
        except Exception:
            return []
