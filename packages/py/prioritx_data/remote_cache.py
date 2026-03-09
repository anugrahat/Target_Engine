"""Shared remote text caching for provenance-backed public resources."""

from __future__ import annotations

import gzip
import hashlib
from pathlib import Path
from urllib.request import urlopen

from prioritx_data.registry import repo_root


def cache_dir(namespace: str) -> Path:
    """Return a cache directory under tmp/ for one remote resource namespace."""
    path = repo_root() / "tmp" / namespace
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_geo_url(url: str) -> str:
    """Translate GEO FTP URLs to HTTPS for standard URL clients."""
    return url.replace("ftp://ftp.ncbi.nlm.nih.gov", "https://ftp.ncbi.nlm.nih.gov")


def load_text_with_cache(url: str, *, namespace: str) -> str:
    """Load a text payload from cache or download it once."""
    normalized = normalize_geo_url(url)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    basename = normalized.rsplit("/", 1)[-1] or "payload"
    cache_path = cache_dir(namespace) / f"{digest}-{basename}"
    if not cache_path.exists():
        with urlopen(normalized, timeout=60) as response:
            cache_path.write_bytes(response.read())
    data = cache_path.read_bytes()
    if cache_path.suffix == ".gz":
        return gzip.decompress(data).decode("utf-8", "replace")
    return data.decode("utf-8", "replace")
