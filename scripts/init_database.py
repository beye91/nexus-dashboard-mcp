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
    """Initialize database and optionally add default cluster."""
    try:
        # Initialize database
        logger.info("Initializing database schema...")
        await init_db()
        logger.info("Database initialized successfully")

        # Check if we should add credentials from environment
        settings = get_settings()

        if settings.nexus_cluster_url and settings.nexus_username and settings.nexus_password:
            logger.info("Found Nexus Dashboard credentials in environment")
            logger.info(f"Adding default cluster: {settings.nexus_cluster_url}")

            credential_manager = CredentialManager()
            await credential_manager.store_credentials(
                name="default",
                url=settings.nexus_cluster_url,
                username=settings.nexus_username,
                password=settings.nexus_password,
                verify_ssl=settings.nexus_verify_ssl,
            )

            logger.info("Default cluster credentials stored successfully")
        else:
            logger.warning("No Nexus Dashboard credentials found in environment")
            logger.warning(
                "Please set NEXUS_CLUSTER_URL, NEXUS_USERNAME, and NEXUS_PASSWORD "
                "or add credentials manually"
            )

    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
