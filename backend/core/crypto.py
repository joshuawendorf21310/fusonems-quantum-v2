"""
FIPS 140-2 compliant cryptographic operations wrapper.

This module provides a unified interface for cryptographic operations that
supports FIPS 140-2 validated modules when available, with graceful fallback
to standard cryptographic libraries.

FedRAMP SC-13: Use FIPS 140-2 validated cryptographic modules.
"""

import os
import base64
import hashlib
import hmac
from typing import Optional, Tuple
from enum import Enum

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import hashes, padding
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

try:
    import argon2
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False

from .config import settings


class FIPSMode(Enum):
    """FIPS mode status."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


class CryptoBackend:
    """Cryptographic backend with FIPS support detection."""
    
    def __init__(self):
        self._fips_mode = self._detect_fips_mode()
        self._backend = self._get_backend()
    
    def _detect_fips_mode(self) -> FIPSMode:
        """
        Detect if FIPS mode is enabled in the system.
        
        Checks:
        - /proc/sys/crypto/fips_enabled (Linux)
        - FIPS_MODE environment variable
        - Settings configuration
        """
        # Check system FIPS mode (Linux)
        if os.path.exists("/proc/sys/crypto/fips_enabled"):
            try:
                with open("/proc/sys/crypto/fips_enabled", "r") as f:
                    if f.read().strip() == "1":
                        return FIPSMode.ENABLED
            except (IOError, OSError):
                pass
        
        # Check environment variable
        fips_env = os.environ.get("FIPS_MODE", "").lower()
        if fips_env in ("1", "true", "enabled", "yes"):
            return FIPSMode.ENABLED
        
        # Check settings
        if hasattr(settings, "FIPS_MODE_ENABLED") and settings.FIPS_MODE_ENABLED:
            return FIPSMode.ENABLED
        
        return FIPSMode.DISABLED
    
    def _get_backend(self):
        """Get appropriate cryptography backend."""
        if not CRYPTOGRAPHY_AVAILABLE:
            return None
        
        try:
            # Try to get FIPS backend if available
            # Note: This requires cryptography with FIPS support compiled
            # For now, use default backend which will use OpenSSL FIPS if available
            backend = default_backend()
            
            # Verify backend supports FIPS algorithms
            if self._fips_mode == FIPSMode.ENABLED:
                # Test that we can create FIPS-approved algorithms
                try:
                    # Test AES-256-GCM (FIPS approved)
                    test_key = os.urandom(32)
                    test_nonce = os.urandom(12)
                    cipher = AESGCM(test_key)
                    cipher.encrypt(test_nonce, b"test", None)
                except Exception:
                    # FIPS mode requested but not available
                    return None
            
            return backend
        except Exception:
            return None
    
    @property
    def fips_mode(self) -> FIPSMode:
        """Get current FIPS mode status."""
        return self._fips_mode
    
    @property
    def is_fips_enabled(self) -> bool:
        """Check if FIPS mode is enabled."""
        return self._fips_mode == FIPSMode.ENABLED
    
    @property
    def backend(self):
        """Get cryptography backend."""
        return self._backend


# Global backend instance
_crypto_backend = CryptoBackend()


def get_random_bytes(length: int) -> bytes:
    """
    Generate cryptographically secure random bytes.
    
    Uses os.urandom() which is FIPS-compliant when using FIPS-validated
    random number generators.
    
    Args:
        length: Number of bytes to generate
        
    Returns:
        Random bytes
    """
    if length < 1:
        raise ValueError("Length must be at least 1")
    return os.urandom(length)


def hash_sha256(data: bytes) -> bytes:
    """
    Compute SHA-256 hash (FIPS approved).
    
    Args:
        data: Data to hash
        
    Returns:
        SHA-256 hash digest
    """
    return hashlib.sha256(data).digest()


def hash_sha512(data: bytes) -> bytes:
    """
    Compute SHA-512 hash (FIPS approved).
    
    Args:
        data: Data to hash
        
    Returns:
        SHA-512 hash digest
    """
    return hashlib.sha512(data).digest()


def hmac_sha256(key: bytes, data: bytes) -> bytes:
    """
    Compute HMAC-SHA256 (FIPS approved).
    
    Args:
        key: HMAC key
        data: Data to authenticate
        
    Returns:
        HMAC-SHA256 digest
    """
    return hmac.new(key, data, hashlib.sha256).digest()


def hmac_sha512(key: bytes, data: bytes) -> bytes:
    """
    Compute HMAC-SHA512 (FIPS approved).
    
    Args:
        key: HMAC key
        data: Data to authenticate
        
    Returns:
        HMAC-SHA512 digest
    """
    return hmac.new(key, data, hashlib.sha512).digest()


def derive_key_pbkdf2(
    password: bytes,
    salt: bytes,
    iterations: int = 100000,
    key_length: int = 32,
    hash_algorithm: str = "sha256"
) -> bytes:
    """
    Derive key using PBKDF2 (FIPS approved).
    
    Args:
        password: Password to derive key from
        salt: Salt value
        iterations: Number of iterations (minimum 100000 recommended)
        key_length: Desired key length in bytes
        hash_algorithm: Hash algorithm ("sha256" or "sha512")
        
    Returns:
        Derived key
    """
    if not CRYPTOGRAPHY_AVAILABLE:
        raise RuntimeError("cryptography library required for PBKDF2")
    
    if hash_algorithm == "sha256":
        algorithm = hashes.SHA256()
    elif hash_algorithm == "sha512":
        algorithm = hashes.SHA512()
    else:
        raise ValueError(f"Unsupported hash algorithm: {hash_algorithm}")
    
    kdf = PBKDF2HMAC(
        algorithm=algorithm,
        length=key_length,
        salt=salt,
        iterations=iterations,
        backend=_crypto_backend.backend
    )
    return kdf.derive(password)


def derive_key_argon2(
    password: bytes,
    salt: bytes,
    time_cost: int = 2,
    memory_cost: int = 65536,
    parallelism: int = 4
) -> bytes:
    """
    Derive key using Argon2id (not FIPS approved, but secure alternative).
    
    Note: Argon2 is not FIPS approved but is recommended by NIST for
    password hashing. Use PBKDF2 when FIPS compliance is required.
    
    Args:
        password: Password to derive key from
        salt: Salt value (16 bytes recommended)
        time_cost: Time cost parameter
        memory_cost: Memory cost in KB
        parallelism: Parallelism parameter
        
    Returns:
        Derived key (32 bytes)
    """
    if not ARGON2_AVAILABLE:
        raise RuntimeError("argon2 library required for Argon2 key derivation")
    
    # Argon2id is the recommended variant
    hasher = argon2.PasswordHasher(
        time_cost=time_cost,
        memory_cost=memory_cost,
        parallelism=parallelism
    )
    
    # Generate a hash and extract the raw bytes
    # Note: This is a simplified approach; for key derivation, consider
    # using argon2.low_level directly
    hash_str = hasher.hash(password)
    # Extract the hash portion (after the $)
    hash_bytes = base64.b64decode(hash_str.split("$")[-1].split("=")[0])
    return hash_bytes[:32]  # Return 32 bytes


def encrypt_aes256_gcm(
    plaintext: bytes,
    key: bytes,
    associated_data: Optional[bytes] = None
) -> Tuple[bytes, bytes]:
    """
    Encrypt data using AES-256-GCM (FIPS approved).
    
    Args:
        plaintext: Data to encrypt
        key: 32-byte encryption key
        associated_data: Optional associated data for authentication
        
    Returns:
        Tuple of (nonce, ciphertext)
    """
    if not CRYPTOGRAPHY_AVAILABLE:
        raise RuntimeError("cryptography library required for AES-256-GCM")
    
    if len(key) != 32:
        raise ValueError("Key must be 32 bytes for AES-256")
    
    # Generate 12-byte nonce (96 bits) for GCM
    nonce = get_random_bytes(12)
    
    cipher = AESGCM(key)
    ciphertext = cipher.encrypt(nonce, plaintext, associated_data)
    
    return nonce, ciphertext


def decrypt_aes256_gcm(
    ciphertext: bytes,
    key: bytes,
    nonce: bytes,
    associated_data: Optional[bytes] = None
) -> bytes:
    """
    Decrypt data using AES-256-GCM (FIPS approved).
    
    Args:
        ciphertext: Encrypted data
        key: 32-byte decryption key
        nonce: Nonce used during encryption
        associated_data: Optional associated data used during encryption
        
    Returns:
        Decrypted plaintext
    """
    if not CRYPTOGRAPHY_AVAILABLE:
        raise RuntimeError("cryptography library required for AES-256-GCM")
    
    if len(key) != 32:
        raise ValueError("Key must be 32 bytes for AES-256")
    
    if len(nonce) != 12:
        raise ValueError("Nonce must be 12 bytes for GCM")
    
    cipher = AESGCM(key)
    plaintext = cipher.decrypt(nonce, ciphertext, associated_data)
    
    return plaintext


def encrypt_aes256_gcm_base64(
    plaintext: str,
    key: bytes,
    associated_data: Optional[str] = None
) -> str:
    """
    Encrypt string data using AES-256-GCM and return base64-encoded result.
    
    Args:
        plaintext: String data to encrypt
        key: 32-byte encryption key
        associated_data: Optional associated data string
        
    Returns:
        Base64-encoded string containing nonce and ciphertext
    """
    plaintext_bytes = plaintext.encode("utf-8")
    ad_bytes = associated_data.encode("utf-8") if associated_data else None
    
    nonce, ciphertext = encrypt_aes256_gcm(plaintext_bytes, key, ad_bytes)
    
    # Combine nonce and ciphertext, then base64 encode
    combined = nonce + ciphertext
    return base64.urlsafe_b64encode(combined).decode("utf-8")


def decrypt_aes256_gcm_base64(
    encrypted_data: str,
    key: bytes,
    associated_data: Optional[str] = None
) -> str:
    """
    Decrypt base64-encoded AES-256-GCM encrypted data.
    
    Args:
        encrypted_data: Base64-encoded encrypted data
        key: 32-byte decryption key
        associated_data: Optional associated data string
        
    Returns:
        Decrypted plaintext string
    """
    combined = base64.urlsafe_b64decode(encrypted_data.encode("utf-8"))
    
    # Extract nonce (first 12 bytes) and ciphertext (rest)
    nonce = combined[:12]
    ciphertext = combined[12:]
    
    ad_bytes = associated_data.encode("utf-8") if associated_data else None
    plaintext_bytes = decrypt_aes256_gcm(ciphertext, key, nonce, ad_bytes)
    
    return plaintext_bytes.decode("utf-8")


def generate_key(length: int = 32) -> bytes:
    """
    Generate a random cryptographic key.
    
    Args:
        length: Key length in bytes (default 32 for AES-256)
        
    Returns:
        Random key bytes
    """
    return get_random_bytes(length)


def is_fips_enabled() -> bool:
    """
    Check if FIPS mode is enabled.
    
    Returns:
        True if FIPS mode is enabled, False otherwise
    """
    return _crypto_backend.is_fips_enabled


def get_fips_mode() -> FIPSMode:
    """
    Get current FIPS mode status.
    
    Returns:
        FIPSMode enum value
    """
    return _crypto_backend.fips_mode
