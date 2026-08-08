import os
import base64

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    _has_crypto = True
except ImportError:
    _has_crypto = False


_KEY_FILE = None
_fernet = None
_enabled = False


def init_crypto(base_dir, password=None):
    global _KEY_FILE, _fernet, _enabled
    if not _has_crypto:
        _enabled = False
        return False
    _KEY_FILE = os.path.join(base_dir, 'data', 'crypto_key.key')
    os.makedirs(os.path.dirname(_KEY_FILE), exist_ok=True)

    if os.path.exists(_KEY_FILE):
        with open(_KEY_FILE, 'rb') as f:
            key = f.read()
    else:
        if password:
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        else:
            key = Fernet.generate_key()
        with open(_KEY_FILE, 'wb') as f:
            f.write(key)

    try:
        _fernet = Fernet(key)
        _enabled = True
        return True
    except Exception:
        _enabled = False
        return False


def is_crypto_enabled():
    return _enabled


def encrypt_file(input_path, output_path=None):
    if not _enabled:
        return False
    if output_path is None:
        output_path = input_path
    with open(input_path, 'rb') as f:
        data = f.read()
    encrypted = _fernet.encrypt(data)
    with open(output_path, 'wb') as f:
        f.write(encrypted)
    return True


def decrypt_file(input_path, output_path=None):
    if not _enabled:
        return False
    with open(input_path, 'rb') as f:
        encrypted = f.read()
    try:
        data = _fernet.decrypt(encrypted)
    except Exception:
        return False
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(data)
        return True
    return data


def decrypt_stream(filepath, chunk_size=64 * 1024):
    if not _enabled:
        return None
    try:
        with open(filepath, 'rb') as f:
            encrypted = f.read()
        data = _fernet.decrypt(encrypted)
    except Exception:
        return None

    offset = 0
    total = len(data)
    while offset < total:
        end = min(offset + chunk_size, total)
        yield data[offset:end]
        offset = end


def is_file_encrypted(filepath):
    if not _enabled:
        return False
    try:
        with open(filepath, 'rb') as f:
            header = f.read(10)
        return header.startswith(b'gAAAAA')
    except Exception:
        return False
