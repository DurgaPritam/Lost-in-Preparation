"""Lost in Preparation research pipeline."""
import os as _os

PIPELINE_VERSION = "0.1.0"

if _os.environ.get("LIP_CACHE_ONLY", "").lower() in ("1", "true", "yes"):
    # Cache-only mode (Phase 9 reproducibility): every network connection is refused, so a step can only use committed
    # files and on-disk caches. A cache miss fails loudly instead of downloading. Covers urllib, the provider SDKs and
    # localhost services alike, because it guards the socket layer. Unix-domain sockets are left alone.
    import socket as _socket

    class CacheOnlyError(ConnectionRefusedError):
        pass

    _connect = _socket.socket.connect
    _connect_ex = _socket.socket.connect_ex

    def _guard(fn):
        def wrapped(self, address, *a, **k):
            if self.family in (_socket.AF_INET, _socket.AF_INET6):
                raise CacheOnlyError(f"LIP_CACHE_ONLY=1: network access refused ({address!r}); this step needs data that is not cached")
            return fn(self, address, *a, **k)
        return wrapped

    _socket.socket.connect = _guard(_connect)
    _socket.socket.connect_ex = _guard(_connect_ex)
    _orig_cc = _socket.create_connection

    def _create_connection(address, *a, **k):
        raise CacheOnlyError(f"LIP_CACHE_ONLY=1: network access refused ({address!r}); this step needs data that is not cached")

    _socket.create_connection = _create_connection
