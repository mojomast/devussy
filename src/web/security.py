"""
Security utilities for API key encryption and masking.

This module provides secure storage of API keys using Fernet symmetric encryption.
Keys are encrypted at rest and only decrypted when needed.
"""

from cryptography.fernet import Fernet
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SecureKeyStorage:
    """
    Encrypts and decrypts API keys using Fernet symmetric encryption.
    
    The encryption key is loaded from the DEVUSSY_ENCRYPTION_KEY environment variable.
    If not set, a new key is generated (not recommended for production).
    
    Set DEVUSSY_DEV_MODE=true to disable encryption entirely during development.
    """
    
    def __init__(self):
        """Initialize the secure key storage with encryption key from environment."""
        # Check if development mode (no encryption)
        dev_mode = os.getenv("DEVUSSY_DEV_MODE", "").lower() in ("true", "1", "yes")
        
        if dev_mode:
            logger.info("🔓 Development mode: API key encryption DISABLED")
            self.dev_mode = True
            self.cipher = None
            return
        
        self.dev_mode = False
        key = os.getenv("DEVUSSY_ENCRYPTION_KEY")
        
        if not key:
            # Generate a new key (development mode)
            key_bytes = Fernet.generate_key()
            logger.warning(
                f"No DEVUSSY_ENCRYPTION_KEY found. Generated new key: {key_bytes.decode()}\n"
                "Store this in your environment to persist encryption:\n"
                "[System.Environment]::SetEnvironmentVariable('DEVUSSY_ENCRYPTION_KEY', "
                f"'{key_bytes.decode()}', 'User')\n\n"
                "Or disable encryption during development:\n"
                "[System.Environment]::SetEnvironmentVariable('DEVUSSY_DEV_MODE', 'true', 'User')"
            )
            self.key = key_bytes
        else:
            # Use existing key
            self.key = key.encode() if isinstance(key, str) else key
        
        self.cipher = Fernet(self.key)
    
    def encrypt(self, api_key: str) -> str:
        """
        Encrypt an API key.
        
        In development mode, returns the key as-is without encryption.
        
        Args:
            api_key: The plaintext API key to encrypt
            
        Returns:
            The encrypted API key as a base64-encoded string (or plaintext in dev mode)
        """
        if not api_key:
            raise ValueError("API key cannot be empty")
        
        # Development mode: no encryption
        if self.dev_mode:
            return api_key
        
        try:
            encrypted_bytes = self.cipher.encrypt(api_key.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError(f"Failed to encrypt API key: {e}")
    
    def decrypt(self, encrypted_key: str) -> str:
        """
        Decrypt an encrypted API key.
        
        In development mode, returns the key as-is (no decryption needed).
        
        Args:
            encrypted_key: The encrypted API key (base64-encoded string, or plaintext in dev mode)
            
        Returns:
            The decrypted API key as plaintext
            
        Raises:
            ValueError: If decryption fails (wrong key or corrupted data)
        """
        if not encrypted_key:
            raise ValueError("Encrypted key cannot be empty")
        
        # Development mode: no decryption needed
        if self.dev_mode:
            return encrypted_key
        
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_key.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"Failed to decrypt API key. Key may be corrupted or encryption key changed: {e}")
    
    def mask_key(self, api_key: str) -> str:
        """
        Return a masked version of an API key for safe display.
        
        Shows first 4 and last 6 characters, masks the rest.
        Example: "sk-test123456789" -> "sk-t...456789"
        
        Args:
            api_key: The API key to mask
            
        Returns:
            The masked API key safe for display/logging
        """
        if not api_key:
            return "***"
        
        if len(api_key) < 10:
            return "***"
        
        return f"{api_key[:4]}...{api_key[-6:]}"
    
    def is_masked(self, key_str: str) -> bool:
        """
        Check if a string appears to be a masked API key.
        
        Args:
            key_str: String to check
            
        Returns:
            True if the string contains masking pattern (...)
        """
        return "..." in key_str
    
    def get_encryption_key_base64(self) -> str:
        """
        Get the current encryption key as a base64 string.
        
        WARNING: This should only be used for backup/migration purposes.
        Never expose this key to users or logs!
        
        Returns:
            The encryption key as a base64-encoded string
        """
        return self.key.decode()


# Global instance for convenience
_secure_storage: Optional[SecureKeyStorage] = None


def get_secure_storage() -> SecureKeyStorage:
    """
    Get the global SecureKeyStorage instance (singleton pattern).
    
    Returns:
        The global SecureKeyStorage instance
    """
    global _secure_storage
    if _secure_storage is None:
        _secure_storage = SecureKeyStorage()
    return _secure_storage
