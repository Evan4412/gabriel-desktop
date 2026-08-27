"""HTTP client seam wiring gabriel-desktop to gabriel-core.

Phase 4 wiring rule: the desktop gateway is a Backend-For-Frontend and must
not import or install ``gabriel-core``. All agent-specification logic lives in
gabriel-core and is consumed purely over HTTP (``/api/v1/agent-specs``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

_PREFIX = "/api/v1/agent-specs"


class CoreServiceError(RuntimeError):
    """gabriel-core returned an error; carries status/detail for relaying."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class SpecificationNotFoundError(CoreServiceError):
    """A named specification does not exist in gabriel-core's store."""

    def __init__(self, detail: str = "Specification not found") -> None:
        super().__init__(404, detail)


def _extract_detail(resp: httpx.Response) -> str:
    try:
        body = resp.json()
        if isinstance(body, dict) and "detail" in body:
            return str(body["detail"])
    except Exception:  # noqa: BLE001 - non-JSON error body
        pass
    return resp.text or f"gabriel-core error {resp.status_code}"


@dataclass
class CoreSpecClient:
    """Thin httpx client for gabriel-core's spec API.

    Pass a pre-built ``client`` (e.g. wrapping an ASGI transport) for tests.
    """

    base_url: str = "http://localhost:8000"
    timeout: float = 10.0
    client: httpx.Client | None = None

    def __post_init__(self) -> None:
        self._client = self.client or httpx.Client(
            base_url=self.base_url.rstrip("/"), timeout=self.timeout
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            resp = self._client.request(method, f"{_PREFIX}{path}", **kwargs)
        except httpx.HTTPError as exc:  # network/connection failures
            raise CoreServiceError(502, f"gabriel-core unreachable: {exc}") from exc
        if resp.status_code >= 400:
            detail = _extract_detail(resp)
            if resp.status_code == 404:
                raise SpecificationNotFoundError(detail)
            raise CoreServiceError(resp.status_code, detail)
        return resp

    def describe_templates(self) -> list[dict[str, Any]]:
        return self._request("GET", "/templates").json()["templates"]

    def instantiate(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/instantiate", json=payload).json()

    def save(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "", json=payload).json()

    def list_saved(self) -> list[str]:
        return self._request("GET", "").json()["specs"]

    def load(self, name: str) -> dict[str, Any]:
        return self._request("GET", f"/{name}").json()

    def delete(self, name: str) -> None:
        self._request("DELETE", f"/{name}")
