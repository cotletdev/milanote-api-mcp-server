"""Type and size of an uploaded image from its first bytes; Milanote's card needs width and height."""

from __future__ import annotations

import struct

from milanote_api_mcp.core.errors import ErrorCode, ToolError

TYPES = {"png": "image/png", "jpg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}


def sniff(data: bytes) -> tuple[str, int, int]:
    """(extension, width, height) of a PNG, JPEG, GIF or WebP file."""
    try:
        return _sniff(data)
    except (struct.error, IndexError) as exc:
        raise ToolError("The image file is cut short or damaged.", ErrorCode.INVALID_INPUT) from exc


def _sniff(data: bytes) -> tuple[str, int, int]:
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        width, height = struct.unpack(">II", data[16:24])
        return "png", width, height
    if data[:6] in (b"GIF87a", b"GIF89a"):
        width, height = struct.unpack("<HH", data[6:10])
        return "gif", width, height
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ("webp", *_webp(data))
    if data.startswith(b"\xff\xd8"):
        return ("jpg", *_jpeg(data))
    raise ToolError("The file must be a PNG, JPEG, GIF or WebP image.", ErrorCode.INVALID_INPUT)


def _webp(data: bytes) -> tuple[int, int]:
    chunk = data[12:16]
    if chunk == b"VP8X":
        return 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little")
    if chunk == b"VP8L":
        bits = int.from_bytes(data[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    width, height = struct.unpack("<HH", data[26:30])
    return width & 0x3FFF, height & 0x3FFF


def _jpeg(data: bytes) -> tuple[int, int]:
    at = 2
    while at + 9 < len(data):
        if data[at] != 0xFF:
            at += 1
            continue
        marker = data[at + 1]
        length = struct.unpack(">H", data[at + 2 : at + 4])[0]
        # Start-of-frame markers carry the size; C4, C8 and CC are other segments.
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            height, width = struct.unpack(">HH", data[at + 5 : at + 9])
            return width, height
        at += 2 + length
    raise ToolError("The JPEG file has no image size; it may be damaged.", ErrorCode.INVALID_INPUT)
