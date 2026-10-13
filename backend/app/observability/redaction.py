"""Redaction for persisted traces and audit details; not used to alter business inputs."""
import re
from collections.abc import Mapping, Sequence

_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE = re.compile(r"(?<!\w)(?!\d{4}-\d{2}-\d{2}(?!\d))(?:\+?\d[\d ()-]{7,}\d)(?!\w)")
_SENSITIVE_KEY = re.compile(r"(?:email|phone|password|secret|token|customer_code|address|payment)", re.IGNORECASE)


def _redact_text(value: str) -> str:
    value = _EMAIL.sub("[REDACTED_EMAIL]", value)
    return _PHONE.sub("[REDACTED_PHONE]", value)


def redact_sensitive(value):
    """Return a JSON-compatible copy with sensitive keys and embedded PII masked."""
    if isinstance(value, Mapping):
        return {str(key): "[REDACTED]" if _SENSITIVE_KEY.search(str(key)) else redact_sensitive(item)
                for key, item in value.items()}
    if isinstance(value, str):
        return _redact_text(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact_sensitive(item) for item in value]
    return value
