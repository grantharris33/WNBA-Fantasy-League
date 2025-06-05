import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from tenacity import RetryError

from app.external_apis.rapidapi_client import ApiKeyError, RapidApiClient, RapidApiError, RateLimitError, RetryableError


@pytest.fixture
def mock_response():
    """Create a mock httpx response."""
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {"data": "test_data"}
    return response


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {"WNBA_API_KEY": "test_key"}):
        yield


class TestRapidApiClient:
    """Tests for the RapidApiClient class."""

    def test_init(self):
        """Test initialization of client."""
        client = RapidApiClient(base_url="https://test.com", host="test.com")
        assert client.base_url == "https://test.com"
        assert client.host == "test.com"
        assert client.timeout == 10
        assert client._client is None

    def test_create_client_missing_key(self):
        """Test exception when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            client = RapidApiClient(base_url="https://test.com", host="test.com")
            with pytest.raises(RuntimeError, match="WNBA_API_KEY .* not set"):
                client._create_client()

    def test_create_client_with_key(self, mock_env_vars):
        """Test client creation with API key."""
        with patch("httpx.AsyncClient") as mock_async_client:
            client = RapidApiClient(base_url="https://test.com", host="test.com")
            client._create_client()

            mock_async_client.assert_called_once_with(
                timeout=10, headers={"x-rapidapi-host": "test.com", "x-rapidapi-key": "test_key"}
            )

    @pytest.mark.asyncio
    async def test_get_json_success(self, mock_env_vars, mock_response):
        """Test successful API call."""
        client = RapidApiClient(base_url="https://test.com", host="test.com")
        client._client = AsyncMock()
        client._client.get.return_value = mock_response

        result = await client._get_json("test_endpoint", {"param": "value"})

        client._client.get.assert_called_once_with("https://test.com/test_endpoint", params={"param": "value"})
        assert result == {"data": "test_data"}

    @pytest.mark.asyncio
    async def test_get_json_rate_limit_error(self, mock_env_vars):
        """Test rate limit error handling - should not retry."""
        client = RapidApiClient(base_url="https://test.com", host="test.com")
        client._client = AsyncMock()

        # Mock 429 response
        mock_response = MagicMock()
        mock_response.status_code = 429
        error = httpx.HTTPStatusError("Rate limited", request=MagicMock(), response=mock_response)
        client._client.get.side_effect = error

        with pytest.raises(RateLimitError, match="API rate limit exceeded"):
            await client._get_json("test_endpoint")

        # Should only call once (no retries)
        assert client._client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_get_json_api_key_error(self, mock_env_vars):
        """Test API key error handling - should not retry."""
        client = RapidApiClient(base_url="https://test.com", host="test.com")
        client._client = AsyncMock()

        # Mock 401 response
        mock_response = MagicMock()
        mock_response.status_code = 401
        error = httpx.HTTPStatusError("Unauthorized", request=MagicMock(), response=mock_response)
        client._client.get.side_effect = error

        with pytest.raises(ApiKeyError, match="Invalid API key"):
            await client._get_json("test_endpoint")

        # Should only call once (no retries)
        assert client._client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_get_json_general_http_error(self, mock_env_vars):
        """Test general HTTP error handling - should retry."""
        client = RapidApiClient(base_url="https://test.com", host="test.com")
        client._client = AsyncMock()

        # Mock 500 response
        mock_response = MagicMock()
        mock_response.status_code = 500
        error = httpx.HTTPStatusError("Server error", request=MagicMock(), response=mock_response)
        client._client.get.side_effect = error

        with pytest.raises(RetryError):
            await client._get_json("test_endpoint")

        # Should retry 3 times
        assert client._client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_get_json_request_error(self, mock_env_vars):
        """Test request error handling - should retry."""
        client = RapidApiClient(base_url="https://test.com", host="test.com")
        client._client = AsyncMock()

        error = httpx.RequestError("Connection failed")
        client._client.get.side_effect = error

        with pytest.raises(RetryError):
            await client._get_json("test_endpoint")

        # Should retry 3 times
        assert client._client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_get_json_retry(self, mock_env_vars):
        """Test retry logic failure leads to RetryError."""

        # Create a failing function that always raises a retryable error
        async def failing_get(url, params=None):
            mock_response = MagicMock()
            mock_response.status_code = 500
            raise httpx.HTTPStatusError("Error", request=MagicMock(), response=mock_response)

        client = RapidApiClient(base_url="https://test.com", host="test.com")
        client._client = AsyncMock()
        client._client.get.side_effect = failing_get

        # The retry logic should eventually give up and raise RetryError
        with pytest.raises(RetryError):
            await client._get_json("test_endpoint")

    @pytest.mark.asyncio
    async def test_close(self, mock_env_vars):
        """Test client close method."""
        client = RapidApiClient(base_url="https://test.com", host="test.com")
        mock_client = AsyncMock()
        client._client = mock_client

        await client.close()

        mock_client.aclose.assert_called_once()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_fetch_game_summary(self, mock_env_vars):
        client = RapidApiClient(base_url="https://test.com", host="test.com")
        with patch.object(client, "_get_json", AsyncMock(return_value={"ok": True})) as mock_get:
            result = await client.fetch_game_summary("123")
            mock_get.assert_called_once_with("wnbasummary", params={"gameId": "123"})
            assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_fetch_game_playbyplay(self, mock_env_vars):
        client = RapidApiClient(base_url="https://test.com", host="test.com")
        with patch.object(client, "_get_json", AsyncMock(return_value={"ok": True})) as mock_get:
            result = await client.fetch_game_playbyplay("999")
            mock_get.assert_called_once_with("wnbaplay", params={"gameId": "999"})
            assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_fetch_box_score(self, mock_env_vars):
        """Test the fetch_box_score method."""
        client = RapidApiClient(base_url="https://test.com", host="test.com")
        with patch.object(client, "_get_json", AsyncMock(return_value={"players": []})) as mock_get:
            result = await client.fetch_box_score("456")
            mock_get.assert_called_once_with("wnbabox", params={"gameId": "456"})
            assert result == {"players": []}

    @pytest.mark.asyncio
    async def test_fetch_schedule(self, mock_env_vars):
        client = RapidApiClient(base_url="https://test.com", host="test.com")
        with patch.object(client, "_get_json", AsyncMock(return_value={"20250101": ["a"]})) as mock_get:
            result = await client.fetch_schedule("2025", "01", "01")
            mock_get.assert_called_once_with("wnbaschedule", params={"year": "2025", "month": "01", "day": "01"})
            assert result == ["a"]

    @pytest.mark.asyncio
    async def test_fetch_wnba_news(self, mock_env_vars):
        client = RapidApiClient(base_url="https://test.com", host="test.com")
        with patch.object(client, "_get_json", AsyncMock(return_value={"articles": []})) as mock_get:
            result = await client.fetch_wnba_news(5)
            mock_get.assert_called_once_with("wnba-news", params={"limit": "5"})
            assert result == {"articles": []}

    @pytest.mark.asyncio
    async def test_fetch_league_injuries(self, mock_env_vars):
        client = RapidApiClient(base_url="https://test.com", host="test.com")
        with patch.object(client, "_get_json", AsyncMock(return_value={"teams": []})) as mock_get:
            result = await client.fetch_league_injuries()
            mock_get.assert_called_once_with("injuries")
            assert result == {"teams": []}
