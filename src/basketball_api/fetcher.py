from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

import httpx


def _cache_path_for_url(url: str, cache_dir: str | Path) -> Path:
    parsed = urlparse(url)
    host = parsed.netloc.replace(":", "-").replace(".", "-")
    path = parsed.path.strip("/") or "root"
    target = Path(cache_dir)
    target.mkdir(parents=True, exist_ok=True)
    return target / f"{host}-{path.replace('/', '-')}.json"


def fetch_json(
    url: str,
    *,
    cache_dir: str | Path = "data/raw",
    timeout: float = 10.0,
    max_retries: int = 3,
) -> dict:
    """Fetch JSON from a URL with a disk cache and a small retry loop for transient failures."""
    cache_file = _cache_path_for_url(url, cache_dir)

    if cache_file.exists():
        return json.loads(cache_file.read_text())

    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = httpx.get(url, timeout=timeout)
            response.raise_for_status()
            payload = response.json()
            cache_file.write_text(json.dumps(payload, indent=2, sort_keys=True))
            return payload
        except (httpx.HTTPError, ValueError) as exc:
            last_error = exc
            if attempt == max_retries - 1:
                break

    if last_error is not None:
        raise last_error

    raise RuntimeError(f"Failed to fetch JSON from {url}")
