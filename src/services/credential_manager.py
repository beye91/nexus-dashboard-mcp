"""Credential management service for secure storage and retrieval."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.models import Cluster
from src.utils.encryption import decrypt_password, encrypt_password


class CredentialManager:
    """Manager for cluster credentials with encryption."""

    def __init__(self):
        """Initialize credential manager."""
        self.db = get_db()

    async def store_credentials(
        self,
        name: str,
        url: str,
        username: str,
        password: str,
        verify_ssl: bool = False,
    ) -> Cluster:
        """Store cluster credentials with encryption.

        Args:
            name: Cluster name (unique identifier)
            url: Cluster URL
            username: Username for authentication
            password: Password (will be encrypted)
            verify_ssl: Whether to verify SSL certificates

        Returns:
            Created Cluster instance
        """
        # Encrypt password before storing
        encrypted_password = encrypt_password(password)

        async with self.db.session() as session:
            # Check if cluster already exists
            result = await session.execute(
                select(Cluster).where(Cluster.name == name)
            )
            existing_cluster = result.scalar_one_or_none()

            if existing_cluster:
                # Update existing cluster
                existing_cluster.url = url
                existing_cluster.username = username
                existing_cluster.password_encrypted = encrypted_password
                existing_cluster.verify_ssl = verify_ssl
                await session.commit()
                await session.refresh(existing_cluster)
                return existing_cluster
            else:
                # Create new cluster
                cluster = Cluster(
                    name=name,
                    url=url,
                    username=username,
                    password_encrypted=encrypted_password,
                    verify_ssl=verify_ssl,
                )
                session.add(cluster)
                await session.commit()
                await session.refresh(cluster)
                return cluster

    async def get_credentials(self, name: str) -> Optional[dict]:
        """Retrieve and decrypt cluster credentials.

        Args:
            name: Cluster name

        Returns:
            Dictionary with url, username, password, verify_ssl or None if not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(Cluster).where(Cluster.name == name, Cluster.is_active == True)
            )
            cluster = result.scalar_one_or_none()

            if not cluster:
                return None

            # Decrypt password
            password = decrypt_password(cluster.password_encrypted)

            return {
                "url": cluster.url,
                "username": cluster.username,
                "password": password,
                "verify_ssl": cluster.verify_ssl,
            }

    async def get_cluster(self, name: str) -> Optional[Cluster]:
        """Get cluster instance by name.

        Args:
            name: Cluster name

        Returns:
            Cluster instance or None if not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(Cluster).where(Cluster.name == name)
            )
            return result.scalar_one_or_none()

    async def list_clusters(self, active_only: bool = True) -> list[Cluster]:
        """List all clusters.

        Args:
            active_only: If True, only return active clusters

        Returns:
            List of Cluster instances
        """
        async with self.db.session() as session:
            query = select(Cluster)
            if active_only:
                query = query.where(Cluster.is_active == True)

            result = await session.execute(query)
            return list(result.scalars().all())

    async def delete_credentials(self, name: str) -> bool:
        """Delete cluster credentials.

        Args:
            name: Cluster name

        Returns:
            True if deleted, False if not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(Cluster).where(Cluster.name == name)
            )
            cluster = result.scalar_one_or_none()

            if not cluster:
                return False

            await session.delete(cluster)
            await session.commit()
            return True

    async def deactivate_cluster(self, name: str) -> bool:
        """Deactivate a cluster (soft delete).

        Args:
            name: Cluster name

        Returns:
            True if deactivated, False if not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(Cluster).where(Cluster.name == name)
            )
            cluster = result.scalar_one_or_none()

            if not cluster:
                return False

            cluster.is_active = False
            await session.commit()
            return True
