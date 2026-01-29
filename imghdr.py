"""
Minimal imghdr replacement for environments where the stdlib module is absent (e.g., Python 3.13 slim builds).
Streamlit imports this module to detect image types; this shim provides a compatible `what` function.
"""
from typing import Optional


# Known magic headers for common web image formats
_MAGIC = {
    b"\x89PNG\r\n\x1a\n": "png",
    b"\xff\xd8\xff": "jpeg",
    b"GIF87a": "gif",
    b"GIF89a": "gif",
    b"BM": "bmp",
    b"II*\x00": "tiff",
    b"MM\x00*": "tiff",
    b"RIFF": "webp",  # further check below
}


def _detect_from_header(h: bytes) -> Optional[str]:
    for magic, name in _MAGIC.items():
        if h.startswith(magic):
            if name == "webp" and not h[8:12] == b"WEBP":
                continue
            return name
    return None


def what(file: Optional[str], h: Optional[bytes] = None) -> Optional[str]:
    """
    Drop-in replacement for imghdr.what.
    Args:
        file: path to the file to inspect (used if `h` is not provided)
        h: optional bytes-like header. If provided, detection is done on this buffer.
    Returns:
        A lower-case string like "png", "jpeg", "gif", etc., or None if unknown.
    """
    if h is not None:
        return _detect_from_header(h)

    if file is None:
        return None

    try:
        with open(file, "rb") as f:
            header = f.read(32)
        return _detect_from_header(header)
    except Exception:
        return None
