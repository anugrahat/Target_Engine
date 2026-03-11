"""Load disease-slice STRING network support over fused candidate genes."""

from __future__ import annotations

import hashlib
import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from prioritx_data.remote_cache import cache_dir

STRING_API_BASE = "https://version-12-0.string-db.org/api/json"


def _post(method: str, payload: dict[str, object]) -> object:
    encoded = urlencode(payload).encode("utf-8")
    url = f"{STRING_API_BASE}/{method}"
    digest = hashlib.sha256(f"{url}\n".encode("utf-8") + encoded).hexdigest()[:16]
    cache_path = cache_dir("string_cache") / f"{digest}.json"
    if not cache_path.exists():
        request = Request(url, data=encoded)
        with urlopen(request, timeout=60) as response:
            cache_path.write_bytes(response.read())
    return json.loads(cache_path.read_text())


def load_string_id_map(gene_symbols: list[str]) -> dict[str, dict[str, str]]:
    """Map gene symbols to STRING identifiers."""
    symbols = sorted({symbol for symbol in gene_symbols if symbol})
    if not symbols:
        return {}

    rows = _post(
        "get_string_ids",
        {
            "identifiers": "\r".join(symbols),
            "species": 9606,
            "echo_query": 1,
            "caller_identity": "prioritx.local",
        },
    ) or []
    mapping: dict[str, dict[str, str]] = {}
    for row in rows:
        query_item = row.get("queryItem")
        string_id = row.get("stringId")
        if not query_item or not string_id or query_item in mapping:
            continue
        mapping[str(query_item)] = {
            "string_id": str(string_id),
            "preferred_name": str(row.get("preferredName") or query_item),
        }
    return mapping


def load_string_network_edges(string_ids: list[str], *, limit: int = 50) -> list[dict[str, Any]]:
    """Load STRING interaction partners for a candidate set."""
    unique_ids = sorted({string_id for string_id in string_ids if string_id})
    if not unique_ids:
        return []
    rows = _post(
        "interaction_partners",
        {
            "identifiers": "\r".join(unique_ids),
            "species": 9606,
            "limit": limit,
            "caller_identity": "prioritx.local",
        },
    ) or []
    return [dict(row) for row in rows]
