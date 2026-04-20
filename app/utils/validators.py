"""
Input validators.
"""
import re
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def sanitise_text(text: str, max_len: int = 10_000) -> str:
    """Strip leading/trailing whitespace and truncate."""
    return text.strip()[:max_len]


def validate_text_input(text: str, min_len: int = 50, max_len: int = 10_000) -> tuple[bool, str]:
    if not text:
        return False, "Text cannot be empty."
    if len(text) < min_len:
        return False, f"Text is too short (minimum {min_len} characters)."
    if len(text) > max_len:
        return False, f"Text is too long (maximum {max_len} characters)."
    return True, ""
