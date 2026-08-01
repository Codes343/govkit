"""Async HTTP client shared by every GovKit actor.

Responsibilities:
  * polite, bounded concurrency against .gov endpoints
  * exponential backoff with jitter on 429/5xx, honouring Retry-After
  * a single place to change the User-Agent and timeouts
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Federal APIs are not high-throughput services and several are explicitly
# rate-limited (openFDA is 240 req/min without a key). Five concurrent requests
# with a small floor between them keeps us well inside every documented limit
# while still finishing a 10k-record pull in a couple of minutes.
DEFAULT_CONCURRENCY = 5
DEFAULT_MIN_INTERVAL = 0.05
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 4

RETRY_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})


class UpstreamError(RuntimeError):
    """Raised when an upstream government API cannot be reached or understood.

    Actors surface this to the user as a readable message rather than a stack
    trace, and — critically — never charge for a run that produced no data.
    """

    def __init__(self, source: str, message: str, *, status: int | None = None) -> None:
        self.source = source
        self.status = status
        super().__init__(f"[{source}] {message}")


class GovKitClient:
    """A rate-limited, retrying JSON client scoped to one upstream source."""

    def __init__(
        self,
        source: str,
        *,
        concurrency: int = DEFAULT_CONCURRENCY,
        min_interval: float = DEFAULT_MIN_INTERVAL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        from govkit import USER_AGENT

        self.source = source
        self.max_retries = max_retries
        self._min_interval = min_interval
        self._sem = asyncio.Semaphore(concurrency)
        self._lock = asyncio.Lock()
        self._next_allowed = 0.0
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )

    async def __aenter__(self) -> GovKitClient:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _throttle(self) -> None:
        """Enforce a minimum wall-clock gap between request starts."""
        async with self._lock:
            loop = asyncio.get_running_loop()
            wait = self._next_allowed - loop.time()
            if wait > 0:
                await asyncio.sleep(wait)
            self._next_allowed = loop.time() + self._min_interval

    def _backoff(self, attempt: int, response: httpx.Response | None) -> float:
        """Retry-After wins when present; otherwise exponential with jitter."""
        if response is not None:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    return min(float(retry_after), 60.0)
                except ValueError:
                    pass
        return min(2.0**attempt, 30.0) * (0.5 + random.random())

    async def request_json(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        last_error: str = "unknown error"
        last_status: int | None = None

        for attempt in range(self.max_retries + 1):
            async with self._sem:
                await self._throttle()
                try:
                    response = await self._client.request(
                        method, url, params=params, json=json_body
                    )
                except httpx.HTTPError as exc:
                    last_error, last_status, response = str(exc), None, None
                else:
                    if response.status_code < 400:
                        try:
                            return response.json()
                        except ValueError as exc:
                            raise UpstreamError(
                                self.source,
                                f"upstream returned non-JSON content ({exc})",
                                status=response.status_code,
                            ) from exc

                    last_status = response.status_code
                    last_error = f"HTTP {response.status_code}"
                    if response.status_code not in RETRY_STATUS:
                        raise UpstreamError(self.source, last_error, status=last_status)

            if attempt < self.max_retries:
                delay = self._backoff(attempt, response)
                logger.warning(
                    "%s: %s — retry %d/%d in %.1fs",
                    self.source,
                    last_error,
                    attempt + 1,
                    self.max_retries,
                    delay,
                )
                await asyncio.sleep(delay)

        raise UpstreamError(
            self.source,
            f"giving up after {self.max_retries + 1} attempts ({last_error})",
            status=last_status,
        )

    async def get_json(self, url: str, **params: Any) -> dict[str, Any]:
        clean = {k: v for k, v in params.items() if v is not None}
        return await self.request_json("GET", url, params=clean)

    async def post_json(self, url: str, body: dict[str, Any]) -> dict[str, Any]:
        return await self.request_json("POST", url, json_body=body)
