from __future__ import annotations

from pathlib import Path

import httpx

from basketball_api.fetcher import fetch_json


class DummyResponse:
    def __init__(self, status_code: int, payload: object):
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=httpx.Request("GET", "https://example.com"),
                response=httpx.Response(status_code=self.status_code),
            )

    def json(self) -> object:
        return self._payload


def test_fetch_json_caches_and_reads_from_disk(tmp_path: Path, monkeypatch) -> None:
    calls: list[str] = []
    cache_dir = tmp_path / "cache"

    def fake_get(url: str, timeout: float):
        calls.append(url)
        return DummyResponse(200, {"ok": True, "value": 42})

    monkeypatch.setattr(httpx, "get", fake_get)

    first = fetch_json("https://example.com/teams", cache_dir=cache_dir)
    second = fetch_json("https://example.com/teams", cache_dir=cache_dir)

    assert first == {"ok": True, "value": 42}
    assert second == {"ok": True, "value": 42}
    assert len(calls) == 1
    assert (cache_dir / "example-com-teams.json").exists()


def test_fetch_json_retries_transient_failures(tmp_path: Path, monkeypatch) -> None:
    responses = iter(
        [
            DummyResponse(500, {"error": "temporary"}),
            DummyResponse(200, {"ok": True, "retried": True}),
        ]
    )

    def fake_get(url: str, timeout: float):
        return next(responses)

    monkeypatch.setattr(httpx, "get", fake_get)

    result = fetch_json("https://example.com/retry", cache_dir=tmp_path / "retry-cache", max_retries=2)

    assert result == {"ok": True, "retried": True}
    assert (tmp_path / "retry-cache" / "example-com-retry.json").exists()
