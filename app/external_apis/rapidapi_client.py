from __future__ import annotations

import os
from typing import Any, Dict

import httpx

try:
    from tenacity import RetryError, retry, stop_after_attempt, wait_exponential, retry_if_exception_type
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

    def retry_if_exception_type(*args, **kwargs):  # type: ignore
        return None

    class RetryError(Exception):
        pass


class RapidApiError(Exception):
    """Base exception for RapidAPI errors."""
    pass


class RateLimitError(RapidApiError):
    """Exception raised when API rate limit is exceeded."""
    pass


class ApiKeyError(RapidApiError):
    """Exception raised when API key is invalid or missing."""
    pass


class RetryableError(RapidApiError):
    """Exception for errors that should be retried."""
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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RetryableError)
    )
    async def _get_json(self, endpoint: str, params: Dict[str, Any] | None = None) -> Any:
        """
        Make a GET request to the API with retry logic.

        Args:
            endpoint: API endpoint path (without base URL)
            params: Optional query parameters

        Returns:
            Parsed JSON response

        Raises:
            RateLimitError: If API rate limit is exceeded
            ApiKeyError: If API key is invalid or missing
            RetryError: If all retry attempts fail
        """
        url = f"{self.base_url}/{endpoint}"
        try:
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # Don't retry rate limit errors - raise immediately
                raise RateLimitError(f"API rate limit exceeded for {endpoint}") from e
            elif e.response.status_code in (401, 403):
                # Don't retry auth errors - raise immediately
                raise ApiKeyError(f"Invalid API key or unauthorized access to {endpoint}") from e
            else:
                # Retry other HTTP errors
                raise RetryableError(f"HTTP {e.response.status_code} error for {endpoint}: {e}") from e
        except httpx.RequestError as e:
            # Retry network/connection errors
            raise RetryableError(f"Request failed for {endpoint}: {e}") from e

    async def fetch_game_summary(self, game_id: str) -> Any:
        """Fetch game summary data for a specific game."""
        return await self._get_json("wnbasummary", params={"gameId": game_id})

    async def fetch_game_playbyplay(self, game_id: str) -> Any:
        """Fetch play-by-play data for a specific game."""
        return await self._get_json("wnbaplay", params={"gameId": game_id})

    async def fetch_box_score(self, game_id: str) -> Any:
        """Fetch box score data for a specific game."""
        return await self._get_json("wnbabox", params={"gameId": game_id})

    async def fetch_schedule(self, year: str, month: str, day: str) -> Any:
        """Fetch the schedule for a given date."""
        data = await self._get_json(
            "wnbaschedule",
            params={"year": year, "month": month, "day": day},
        )
        key = f"{year}{month}{day}"
        return data.get(key, [])

    async def fetch_wnba_news(self, limit: int = 20) -> Any:
        """Fetch recent WNBA news articles."""
        return await self._get_json("wnba-news", params={"limit": str(limit)})

    async def fetch_league_injuries(self) -> Any:
        """Fetch league-wide injury information."""
        return await self._get_json("injuries")

    async def fetch_team_roster(self, team_id: str) -> Any:
        """Fetch roster data for a specific team."""
        return await self._get_json("team-roster", params={"teamId": team_id})

    async def fetch_player_bio(self, player_id: str) -> Any:
        """Fetch biographical data for a specific player."""
        return await self._get_json("player/bio", params={"playerId": player_id})

    async def fetch_all_teams(self) -> Any:
        """Fetch all WNBA teams."""
        return await self._get_json("team/id")

    async def fetch_standings(self, year: str) -> Any:
        """Fetch current standings."""
        return await self._get_json("wnbastandings", params={"year": year})

    async def fetch_team_schedule(self, season: str, team_id: str) -> Any:
        """Fetch a team's full season schedule."""
        return await self._get_json("team/schedulev2", params={"season": season, "teamId": team_id})

    async def close(self) -> None:
        """Close the client session."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None


# Singleton instance for WNBA API
wnba_client = RapidApiClient(base_url="https://wnba-api.p.rapidapi.com", host="wnba-api.p.rapidapi.com")
