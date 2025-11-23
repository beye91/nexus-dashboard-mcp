"""Encryption utilities for secure credential storage."""

from cryptography.fernet import Fernet

from src.config.settings import get_settings


def generate_encryption_key() -> bytes:
    """Generate a new Fernet encryption key.

    Returns:
        New Fernet encryption key
    """
    return Fernet.generate_key()


def get_fernet() -> Fernet:
    """Get Fernet instance with encryption key from settings.

    Returns:
        Fernet instance

    Raises:
        ValueError: If encryption key is not configured
    """
    settings = get_settings()
    key = settings.get_encryption_key()
    return Fernet(key)


def encrypt_password(password: str) -> str:
    """Encrypt a password using Fernet symmetric encryption.

    Args:
        password: Plain text password to encrypt

    Returns:
        Encrypted password as string
    """
    fernet = get_fernet()
    encrypted_bytes = fernet.encrypt(password.encode())
    return encrypted_bytes.decode()


def decrypt_password(encrypted_password: str) -> str:
    """Decrypt a password using Fernet symmetric encryption.

    Args:
        encrypted_password: Encrypted password string

    Returns:
        Decrypted plain text password

    Raises:
        cryptography.fernet.InvalidToken: If decryption fails
    """
    fernet = get_fernet()
    decrypted_bytes = fernet.decrypt(encrypted_password.encode())
    return decrypted_bytes.decode()
