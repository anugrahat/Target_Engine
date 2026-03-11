"""Shared remote text caching for provenance-backed public resources."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

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
    data = load_bytes_with_cache(url, namespace=namespace)
    if normalize_geo_url(url).endswith(".gz"):
        return gzip.decompress(data).decode("utf-8", "replace")
    return data.decode("utf-8", "replace")


def load_bytes_with_cache(url: str, *, namespace: str) -> bytes:
    """Load a binary payload from cache or download it once."""
    normalized = normalize_geo_url(url)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    basename = normalized.rsplit("/", 1)[-1] or "payload"
    cache_path = cache_dir(namespace) / f"{digest}-{basename}"
    if not cache_path.exists():
        with urlopen(normalized, timeout=60) as response:
            cache_path.write_bytes(response.read())
    return cache_path.read_bytes()


def load_json_post_with_cache(url: str, *, namespace: str, payload: dict[str, object]) -> object:
    """POST a JSON payload once, then reuse the cached JSON response."""
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(f"{url}\n{serialized}".encode("utf-8")).hexdigest()[:16]
    cache_path = cache_dir(namespace) / f"{digest}.json"
    if not cache_path.exists():
        request = Request(
            url,
            data=serialized.encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=60) as response:
            cache_path.write_bytes(response.read())
    return json.loads(cache_path.read_text())


def load_json_text_post_with_cache(
    url: str,
    *,
    namespace: str,
    payload: str,
    content_type: str = "text/plain",
    accept: str = "application/json",
) -> object:
    """POST a text payload once, then reuse the cached JSON response."""
    digest = hashlib.sha256(f"{url}\n{content_type}\n{payload}".encode("utf-8")).hexdigest()[:16]
    cache_path = cache_dir(namespace) / f"{digest}.json"
    if not cache_path.exists():
        request = Request(
            url,
            data=payload.encode("utf-8"),
            headers={
                "Content-Type": content_type,
                "Accept": accept,
            },
        )
        with urlopen(request, timeout=60) as response:
            cache_path.write_bytes(response.read())
    return json.loads(cache_path.read_text())
