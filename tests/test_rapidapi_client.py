import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from tenacity import RetryError

from app.external_apis.rapidapi_client import RapidApiClient


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
                timeout=10,
                headers={
                    "x-rapidapi-host": "test.com",
                    "x-rapidapi-key": "test_key",
                }
            )

    @pytest.mark.asyncio
    async def test_get_json_success(self, mock_env_vars, mock_response):
        """Test successful API call."""
        client = RapidApiClient(base_url="https://test.com", host="test.com")
        client._client = AsyncMock()
        client._client.get.return_value = mock_response

        result = await client._get_json("test_endpoint", {"param": "value"})

        client._client.get.assert_called_once_with(
            "https://test.com/test_endpoint",
            params={"param": "value"}
        )
        assert result == {"data": "test_data"}

    @pytest.mark.asyncio
    async def test_get_json_retry(self, mock_env_vars):
        """Test retry logic failure leads to RetryError."""
        # Create a failing function that always raises an error
        async def failing_get(url, params=None):
            raise httpx.HTTPStatusError("Error", request=MagicMock(), response=MagicMock())

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