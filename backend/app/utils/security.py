"""Sicherheits-Dienstprogramme"""

from cryptography.fernet import Fernet
import base64
import hashlib
from app.core.config import settings


def get_fernet():
    """Fernet-Instanz mit Key aus Config"""
    # Key muss 32 Bytes Base64 sein
    key = base64.urlsafe_b64encode(
        hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
    )
    return Fernet(key)


def encrypt_api_key(key: str) -> str:
    """API-Key verschlüsseln"""
    f = get_fernet()
    return f.encrypt(key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """API-Key entschlüsseln"""
    f = get_fernet()
    return f.decrypt(encrypted_key.encode()).decode()