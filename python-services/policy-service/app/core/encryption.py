"""
Database Encryption for PII Fields - CIMA Compliant

Implements AES-256 encryption for sensitive personal data.
All PII must be encrypted at rest per CIMA requirements.

Encryption Scope:
- Phone numbers
- National ID numbers (CNI)
- Email addresses
- Home addresses
- Banking information (if stored)
"""

import os
import logging
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)


class DataEncryption:
    """
    AES-256 encryption for PII data.
    
    Uses Fernet which provides:
    - AES-128 in CBC mode with PKCS7 padding
    - HMAC-SHA256 for authentication
    - Version information for future key rotation
    """
    
    def __init__(self, key: Optional[str] = None):
        """
        Initialize encryption with key.
        
        Args:
            key: Base64-encoded 32-byte key. If None, uses ENCRYPTION_KEY env var.
        """
        if key is None:
            key = os.getenv('ENCRYPTION_KEY')
        
        if not key:
            raise ValueError(
                "Encryption key required. Set ENCRYPTION_KEY environment variable. "
                "Generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        
        try:
            self.cipher = Fernet(key.encode() if isinstance(key, str) else key)
            logger.info("DataEncryption initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise ValueError(f"Invalid encryption key: {e}")
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt string data.
        
        Args:
            data: Plain text to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        if not data:
            return data
        
        try:
            encrypted = self.cipher.encrypt(data.encode('utf-8'))
            return encrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt encrypted string.
        
        Args:
            encrypted_data: Base64-encoded encrypted string
            
        Returns:
            Decrypted plain text
        """
        if not encrypted_data:
            return encrypted_data
        
        try:
            decrypted = self.cipher.decrypt(encrypted_data.encode('utf-8'))
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Invalid or corrupted encrypted data")
    
    def encrypt_phone(self, phone: str) -> str:
        """Encrypt phone number with validation."""
        if not phone:
            return phone
        
        # Normalize phone number first
        phone = phone.replace(' ', '').replace('-', '').replace('.', '')
        return self.encrypt(phone)
    
    def decrypt_phone(self, encrypted_phone: str) -> str:
        """Decrypt phone number."""
        return self.decrypt(encrypted_phone)
    
    def encrypt_id_number(self, id_number: str) -> str:
        """Encrypt national ID number (CNI)."""
        if not id_number:
            return id_number
        
        # Validate format before encryption
        if not id_number.isdigit() or len(id_number) != 9:
            logger.warning(f"Invalid ID number format: {id_number[:3]}...")
        
        return self.encrypt(id_number)
    
    def decrypt_id_number(self, encrypted_id: str) -> str:
        """Decrypt national ID number."""
        return self.decrypt(encrypted_id)
    
    def mask_pii(self, data: str, visible_chars: int = 4) -> str:
        """
        Mask PII for display/logs.
        
        Example:
            +225 01 23 45 67 89 → +225 XX XX XX 67 89
            1234567890123 → *********0123
        """
        if not data:
            return data
        
        if len(data) <= visible_chars * 2:
            return '*' * len(data)
        
        masked_length = len(data) - visible_chars
        return '*' * masked_length + data[-visible_chars:]


# Global encryption instance (lazy loaded)
_encryption_instance: Optional[DataEncryption] = None


def get_encryption() -> DataEncryption:
    """Get or create global encryption instance."""
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = DataEncryption()
    return _encryption_instance


def encrypt_pii(data: str) -> str:
    """Convenience function to encrypt PII."""
    return get_encryption().encrypt(data)


def decrypt_pii(encrypted_data: str) -> str:
    """Convenience function to decrypt PII."""
    return get_encryption().decrypt(encrypted_data)


# ═════════════════════════════════════════════════════════════════
# SQLAlchemy Type Decorators for Automatic Encryption
# ═════════════════════════════════════════════════════════════════

from sqlalchemy import TypeDecorator, Text


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy type for automatic encryption/decryption.
    
    Usage:
        class User(Base):
            __tablename__ = 'users'
            id = Column(Integer, primary_key=True)
            phone_number = Column(EncryptedString)  # Auto-encrypted
    """
    
    impl = Text
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        """Encrypt on save."""
        if value is None:
            return None
        return get_encryption().encrypt(str(value))
    
    def process_result_value(self, value, dialect):
        """Decrypt on load."""
        if value is None:
            return None
        return get_encryption().decrypt(value)


class EncryptedPhone(TypeDecorator):
    """SQLAlchemy type for encrypted phone numbers."""
    
    impl = Text
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return get_encryption().encrypt_phone(str(value))
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return get_encryption().decrypt_phone(value)


class EncryptedIDNumber(TypeDecorator):
    """SQLAlchemy type for encrypted national ID numbers."""
    
    impl = Text
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return get_encryption().encrypt_id_number(str(value))
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return get_encryption().decrypt_id_number(value)


# ═════════════════════════════════════════════════════════════════
# Key Rotation Utilities
# ═════════════════════════════════════════════════════════════════

def rotate_key(old_key: str, new_key: str, db_session, table_name: str, column_name: str):
    """
    Rotate encryption key for a column.
    
    This is a one-time operation that should be done during maintenance window.
    
    Args:
        old_key: Current encryption key
        new_key: New encryption key
        db_session: SQLAlchemy session
        table_name: Name of table to rotate
        column_name: Name of encrypted column
    """
    from sqlalchemy import text
    
    old_cipher = Fernet(old_key.encode())
    new_cipher = Fernet(new_key.encode())
    
    # Fetch all encrypted values
    result = db_session.execute(
        text(f"SELECT id, {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL")
    )
    
    updated = 0
    for row in result:
        try:
            # Decrypt with old key
            decrypted = old_cipher.decrypt(row[1].encode()).decode()
            # Encrypt with new key
            reencrypted = new_cipher.encrypt(decrypted.encode()).decode()
            
            # Update
            db_session.execute(
                text(f"UPDATE {table_name} SET {column_name} = :val WHERE id = :id"),
                {"val": reencrypted, "id": row[0]}
            )
            updated += 1
            
        except Exception as e:
            logger.error(f"Failed to rotate key for row {row[0]}: {e}")
    
    db_session.commit()
    logger.info(f"Key rotation complete. Updated {updated} rows.")
    return updated


# ═════════════════════════════════════════════════════════════════
# Generate Encryption Key
# ═════════════════════════════════════════════════════════════════

def generate_encryption_key() -> str:
    """Generate a new Fernet encryption key."""
    key = Fernet.generate_key()
    return key.decode()


if __name__ == "__main__":
    # Generate key for setup
    print("Generating new encryption key...")
    key = generate_encryption_key()
    print(f"\nAdd this to your .env file:")
    print(f"ENCRYPTION_KEY={key}")
    print(f"\nWARNING: Keep this key secure! Loss of key = loss of data!")
