import base64, time, zstandard as zstd
from typing import Tuple
def now_ts() -> int:
    return int(time.time())
def b64_to_bytes(s: str) -> bytes:
    return base64.b64decode(s)
def bytes_to_b64(b: bytes) -> str:
    return base64.b64encode(b).decode()
def compress_bytes(b: bytes, level: int = 3) -> bytes:
    c = zstd.ZstdCompressor(level=level)
    return c.compress(b)
def decompress_bytes(b: bytes) -> bytes:
    d = zstd.ZstdDecompressor()
    return d.decompress(b)
