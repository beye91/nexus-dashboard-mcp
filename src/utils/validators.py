"""Validation utilities for input validation."""

import re
from urllib.parse import urlparse


def validate_url(url: str) -> bool:
    """Validate if a string is a valid URL.

    Args:
        url: URL string to validate

    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_http_method(method: str) -> bool:
    """Validate if a string is a valid HTTP method.

    Args:
        method: HTTP method to validate

    Returns:
        True if valid HTTP method, False otherwise
    """
    valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
    return method.upper() in valid_methods


def validate_operation_id(operation_id: str) -> bool:
    """Validate if operation ID follows expected format.

    Args:
        operation_id: Operation ID to validate

    Returns:
        True if valid, False otherwise
    """
    # Operation IDs should be alphanumeric with underscores/hyphens
    pattern = r"^[a-zA-Z0-9_-]+$"
    return bool(re.match(pattern, operation_id))


def sanitize_log_message(message: str, max_length: int = 1000) -> str:
    """Sanitize log message to prevent injection attacks.

    Args:
        message: Message to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized message
    """
    if not message:
        return ""

    # Remove null bytes and control characters
    sanitized = "".join(char for char in message if ord(char) >= 32 or char in "\n\r\t")

    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "... (truncated)"

    return sanitized
