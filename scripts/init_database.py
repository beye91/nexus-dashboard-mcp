"""Database initialization script."""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings, init_db
from src.services.credential_manager import CredentialManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Initialize database and optionally bootstrap default cluster.

    NOTE: Environment variables are only used for initial bootstrap.
    If a cluster already exists in the database, it will NOT be overwritten.
    Use the Web UI to manage cluster credentials after initial setup.
    """
    try:
        # Initialize database
        logger.info("Initializing database schema...")
        await init_db()
        logger.info("Database initialized successfully")

        # Check if default cluster already exists
        credential_manager = CredentialManager()
        existing_cluster = await credential_manager.get_cluster("default")

        if existing_cluster:
            logger.info(f"Default cluster already exists: {existing_cluster.url}")
            logger.info("Skipping environment variable bootstrap (use Web UI to modify)")
            return

        # Bootstrap from environment only if no cluster exists
        settings = get_settings()

        if settings.nexus_cluster_url and settings.nexus_username and settings.nexus_password:
            logger.info("No existing cluster found - bootstrapping from environment")
            logger.info(f"Creating default cluster: {settings.nexus_cluster_url}")

            await credential_manager.store_credentials(
                name="default",
                url=settings.nexus_cluster_url,
                username=settings.nexus_username,
                password=settings.nexus_password,
                verify_ssl=settings.nexus_verify_ssl,
            )

            logger.info("Default cluster created successfully")
            logger.info("NOTE: Future changes should be made via Web UI, not .env file")
        else:
            logger.warning("No Nexus Dashboard credentials found in environment")
            logger.warning(
                "Please configure a cluster via the Web UI or set "
                "NEXUS_CLUSTER_URL, NEXUS_USERNAME, and NEXUS_PASSWORD for first-time setup"
            )

    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
