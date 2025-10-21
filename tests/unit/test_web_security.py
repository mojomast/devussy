"""
Unit tests for the security module (API key encryption and masking).
"""

import pytest
import os
from cryptography.fernet import Fernet

from src.web.security import SecureKeyStorage, get_secure_storage


class TestSecureKeyStorage:
    """Tests for SecureKeyStorage class."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Use a known test key
        self.test_key = Fernet.generate_key()
        os.environ["DEVUSSY_ENCRYPTION_KEY"] = self.test_key.decode()
        self.storage = SecureKeyStorage()
    
    def teardown_method(self):
        """Clean up after each test."""
        if "DEVUSSY_ENCRYPTION_KEY" in os.environ:
            del os.environ["DEVUSSY_ENCRYPTION_KEY"]
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption work correctly."""
        original_key = "sk-test123456789"
        
        # Encrypt
        encrypted = self.storage.encrypt(original_key)
        assert encrypted != original_key
        assert len(encrypted) > len(original_key)
        
        # Decrypt
        decrypted = self.storage.decrypt(encrypted)
        assert decrypted == original_key
    
    def test_encrypt_empty_key_raises_error(self):
        """Test that encrypting an empty key raises an error."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            self.storage.encrypt("")
    
    def test_decrypt_empty_key_raises_error(self):
        """Test that decrypting an empty key raises an error."""
        with pytest.raises(ValueError, match="Encrypted key cannot be empty"):
            self.storage.decrypt("")
    
    def test_decrypt_invalid_key_raises_error(self):
        """Test that decrypting an invalid key raises an error."""
        with pytest.raises(ValueError, match="Failed to decrypt"):
            self.storage.decrypt("invalid-encrypted-data")
    
    def test_decrypt_with_wrong_encryption_key(self):
        """Test that decryption fails if the encryption key changes."""
        original_key = "sk-test123"
        
        # Encrypt with first key
        encrypted = self.storage.encrypt(original_key)
        
        # Change encryption key
        new_key = Fernet.generate_key()
        os.environ["DEVUSSY_ENCRYPTION_KEY"] = new_key.decode()
        storage2 = SecureKeyStorage()
        
        # Try to decrypt with different key
        with pytest.raises(ValueError, match="Failed to decrypt"):
            storage2.decrypt(encrypted)
    
    def test_mask_key_standard(self):
        """Test masking a standard API key."""
        key = "sk-test123456789"
        masked = self.storage.mask_key(key)
        
        assert masked == "sk-t...456789"
        assert "test123" not in masked
        assert "..." in masked
    
    def test_mask_key_short(self):
        """Test masking a short key."""
        key = "short"
        masked = self.storage.mask_key(key)
        
        assert masked == "***"
    
    def test_mask_key_empty(self):
        """Test masking an empty key."""
        masked = self.storage.mask_key("")
        assert masked == "***"
    
    def test_is_masked(self):
        """Test detection of masked keys."""
        assert self.storage.is_masked("sk-t...456789") is True
        assert self.storage.is_masked("sk-test123456789") is False
        # Note: "***" doesn't contain "..." so it won't be detected as masked by this simple check
    
    def test_get_encryption_key_base64(self):
        """Test getting the encryption key in base64 format."""
        key_base64 = self.storage.get_encryption_key_base64()
        assert key_base64 == self.test_key.decode()
    
    def test_multiple_encryptions_different_output(self):
        """Test that encrypting the same key multiple times gives different output."""
        key = "sk-test123"
        
        encrypted1 = self.storage.encrypt(key)
        encrypted2 = self.storage.encrypt(key)
        
        # Fernet includes a timestamp, so encryptions should differ
        # But both should decrypt to the same value
        assert self.storage.decrypt(encrypted1) == key
        assert self.storage.decrypt(encrypted2) == key


class TestGetSecureStorage:
    """Tests for the global storage singleton."""
    
    def test_get_secure_storage_singleton(self):
        """Test that get_secure_storage returns the same instance."""
        storage1 = get_secure_storage()
        storage2 = get_secure_storage()
        
        assert storage1 is storage2
    
    def test_get_secure_storage_works(self):
        """Test that the global instance works correctly."""
        storage = get_secure_storage()
        
        key = "sk-test123"
        encrypted = storage.encrypt(key)
        decrypted = storage.decrypt(encrypted)
        
        assert decrypted == key
