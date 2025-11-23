"""Nexus Dashboard API client for authentication and requests."""

import logging
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import httpx

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class NexusAPIClient:
    """Client for interacting with Nexus Dashboard APIs."""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        verify_ssl: bool = False,
    ):
        """Initialize Nexus Dashboard API client.

        Args:
            base_url: Nexus Dashboard base URL
            username: Username for authentication
            password: Password for authentication
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.settings = get_settings()

        # Session management
        self.access_token: Optional[str] = None
        self.cookies: Optional[dict] = None

        # HTTP client configuration
        self.client = httpx.AsyncClient(
            verify=verify_ssl,
            timeout=httpx.Timeout(self.settings.api_timeout),
            follow_redirects=True,
        )

    async def authenticate(self) -> bool:
        """Authenticate with Nexus Dashboard using Basic Auth.

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Nexus Dashboard typically uses /login endpoint with Basic Auth
            login_url = urljoin(self.base_url, "/login")

            response = await self.client.post(
                login_url,
                json={"username": self.username, "password": self.password},
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                # Extract session cookies or token from response
                self.cookies = dict(response.cookies)

                # Some Nexus Dashboard versions return a token in the response
                if response.headers.get("set-cookie"):
                    logger.info("Authentication successful, session cookies obtained")
                    return True

                # Check for token in response body
                try:
                    data = response.json()
                    if "token" in data:
                        self.access_token = data["token"]
                        logger.info("Authentication successful, token obtained")
                        return True
                except Exception:
                    pass

                # If we got 200 but no clear token, assume cookies are enough
                if self.cookies:
                    logger.info("Authentication successful using cookies")
                    return True

            logger.error(f"Authentication failed with status {response.status_code}")
            return False

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    async def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make authenticated request to Nexus Dashboard.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: API endpoint path
            params: Query parameters
            json_data: JSON request body
            headers: Additional headers

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPStatusError: If request fails
        """
        # Ensure we're authenticated
        if not self.cookies and not self.access_token:
            authenticated = await self.authenticate()
            if not authenticated:
                raise RuntimeError("Failed to authenticate with Nexus Dashboard")

        # Build full URL
        url = urljoin(self.base_url, path.lstrip("/"))

        # Prepare headers
        request_headers = headers or {}
        if self.access_token:
            request_headers["Authorization"] = f"Bearer {self.access_token}"

        # Make request with retry logic
        max_retries = self.settings.api_retry_attempts
        last_exception = None

        for attempt in range(max_retries):
            try:
                response = await self.client.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    json=json_data,
                    headers=request_headers,
                    cookies=self.cookies,
                )

                # Handle 401 by re-authenticating and retrying once
                if response.status_code == 401 and attempt == 0:
                    logger.warning("Received 401, re-authenticating...")
                    await self.authenticate()
                    continue

                response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                    continue
                else:
                    raise

            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger.warning(f"Request error (attempt {attempt + 1}/{max_retries}): {e}")
                    continue
                else:
                    raise

        # If we get here, all retries failed
        if last_exception:
            raise last_exception

    async def close(self):
        """Close HTTP client connection."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.authenticate()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
