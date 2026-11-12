from urllib.parse import urlsplit


def local_redirect(value, default):
    """Only absolute paths on this app; never a scheme or network location."""
    if not isinstance(value, str) or any(c in value for c in ('\\', '\r', '\n')):
        return default
    parts = urlsplit(value)
    return value if value.startswith('/') and not value.startswith('//') and not parts.scheme and not parts.netloc else default
