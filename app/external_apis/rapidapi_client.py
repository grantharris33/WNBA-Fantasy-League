from __future__ import annotations

import os
from typing import Any, Dict

import httpx

try:
    from tenacity import RetryError, retry, stop_after_attempt, wait_exponential
except ModuleNotFoundError:  # pragma: no cover
    # Provide minimal no-op fallback so that code can run without tenacity in CI
    import functools

    def retry(*dargs, **dkwargs):  # type: ignore
        max_attempts = 3

        def decorator(fn):
            @functools.wraps(fn)
            async def wrapper(*args, **kwargs):
                attempts = 0
                while True:
                    try:
                        return await fn(*args, **kwargs)
                    except Exception as exc:  # noqa: BLE001
                        attempts += 1
                        if attempts >= max_attempts:
                            raise RetryError(str(exc)) from exc
                        # No sleep to keep tests fast

            return wrapper

        return decorator

    def stop_after_attempt(*args, **kwargs):  # type: ignore
        return None

    def wait_exponential(*args, **kwargs):  # type: ignore
        return None

    class RetryError(Exception):
        pass


class RapidApiClient:
    """Client for interacting with RapidAPI services."""

    def __init__(self, base_url: str, host: str, timeout: int = 10):
        self.base_url = base_url
        self.host = host
        self.timeout = timeout
        self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy initialization of httpx client."""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self) -> httpx.AsyncClient:
        """Create and configure an httpx AsyncClient with proper headers."""
        api_key = os.getenv("WNBA_API_KEY") or os.getenv("RAPIDAPI_KEY")
        if not api_key:
            raise RuntimeError("WNBA_API_KEY (or RAPIDAPI_KEY) env var not set")

        headers = {"x-rapidapi-host": self.host, "x-rapidapi-key": api_key}

        return httpx.AsyncClient(timeout=self.timeout, headers=headers)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _get_json(self, endpoint: str, params: Dict[str, Any] | None = None) -> Any:
        """
        Make a GET request to the API with retry logic.

        Args:
            endpoint: API endpoint path (without base URL)
            params: Optional query parameters

        Returns:
            Parsed JSON response

        Raises:
            RetryError: If all retry attempts fail
        """
        url = f"{self.base_url}/{endpoint}"
        resp = await self.client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    async def fetch_game_summary(self, game_id: str) -> Any:
        """Fetch game summary data for a specific game."""

        return await self._get_json("wnbasummary", params={"gameId": game_id})

    async def fetch_game_playbyplay(self, game_id: str) -> Any:
        """Fetch play-by-play data for a specific game."""

        return await self._get_json("wnbaplay", params={"gameId": game_id})

    async def close(self) -> None:
        """Close the client session."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None


# Singleton instance for WNBA API
wnba_client = RapidApiClient(base_url="https://wnba-api.p.rapidapi.com", host="wnba-api.p.rapidapi.com")
