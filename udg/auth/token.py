import secrets
import os
from pathlib import Path
from typing import Optional

def generate_token() -> str:
    """Generate a 64-character hex token (32 bytes)"""
    return secrets.token_hex(32)

def load_token(path: Path) -> str:
    """Load token from file, create if not exists"""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        token = generate_token()
        save_token(token, path)
    return path.read_text().strip()

def save_token(token: str, path: Path) -> None:
    """Save token with 0o600 permissions"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(token)
    os.chmod(path, 0o600)

def validate_token(token: str, expected: str) -> bool:
    """Constant-time comparison"""
    return secrets.compare_digest(token, expected)

def rotate_token(path: Path) -> str:
    """Generate new token, save, return"""
    new_token = generate_token()
    save_token(new_token, path)
    return new_token