"""Tests for simdb.client module."""

import pickle
from pathlib import Path

import httpx
import pytest

from nucleai.core.exceptions import AuthenticationError
from nucleai.simdb.client import SimDBClient, get_simulation, list_simulations, query
from nucleai.simdb.models import Simulation


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings for testing."""
    monkeypatch.setenv("SIMDB_USERNAME", "test_user")
    monkeypatch.setenv("SIMDB_PASSWORD", "test_pass")
    monkeypatch.setenv("SIMDB_REMOTE_URL", "https://test.simdb.org/api")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    from nucleai.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def mock_cookies_file(tmp_path, monkeypatch):
    """Mock cookies file location."""
    config_dir = tmp_path / ".config" / "simdb"
    config_dir.mkdir(parents=True)

    # Mock home directory
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    return config_dir / "iter-cookies.pkl"


class TestSimDBClientInitialization:
    """Tests for SimDBClient initialization."""

    def test_client_initializes(self, mock_settings):
        """Test that client initializes correctly."""
        client = SimDBClient()

        assert client.settings is not None
        assert client._client is None
        assert client._cookies is None


class TestSimDBClientContextManager:
    """Tests for SimDBClient context manager."""

    async def test_context_manager_creates_client(self, mock_settings, mocker):
        """Test that context manager creates HTTP client."""
        # Mock authentication
        mock_cookies = httpx.Cookies({"session": "test123"})
        mocker.patch.object(SimDBClient, "_get_cookies", return_value=mock_cookies)
        mocker.patch.object(SimDBClient, "_detect_api_version", return_value="v1")

        async with SimDBClient() as client:
            assert client._client is not None
            assert isinstance(client._client, httpx.AsyncClient)

    async def test_context_manager_closes_client(self, mock_settings, mocker):
        """Test that context manager closes HTTP client."""
        mock_cookies = httpx.Cookies({"session": "test123"})
        mocker.patch.object(SimDBClient, "_get_cookies", return_value=mock_cookies)
        mocker.patch.object(SimDBClient, "_detect_api_version", return_value="v1")

        client = SimDBClient()
        async with client:
            assert client._client is not None

        # Client should be closed after context exit
        assert client._client is None


class TestSimDBClientAuthentication:
    """Tests for SimDBClient authentication."""

    async def test_get_cookies_with_valid_cache(self, mock_settings, mock_cookies_file, mocker):
        """Test loading valid cached cookies."""
        # Create cached cookies
        cached_cookies = {"session": "cached123", "token": "abc"}
        with mock_cookies_file.open("wb") as f:
            pickle.dump(cached_cookies, f)

        # Mock validation request
        mock_response = mocker.Mock()
        mock_response.json.return_value = {"status": "ok"}

        mock_client_cm = mocker.AsyncMock()
        mock_client_cm.__aenter__.return_value.get = mocker.AsyncMock(return_value=mock_response)
        mock_client_cm.__aexit__.return_value = None

        mocker.patch("httpx.AsyncClient", return_value=mock_client_cm)

        client = SimDBClient()
        cookies = await client._get_cookies()

        assert "session" in cookies
        assert cookies["session"] == "cached123"

    async def test_get_cookies_authenticates_on_invalid_cache(
        self, mock_settings, mock_cookies_file, mocker
    ):
        """Test re-authentication when cache is invalid."""
        # Create invalid cached cookies
        with mock_cookies_file.open("wb") as f:
            pickle.dump({"old": "cookie"}, f)

        # Mock validation failure and successful authentication
        mock_validate_response = mocker.Mock()
        mock_validate_response.json.side_effect = Exception("Invalid JSON")

        mock_auth_response = mocker.Mock()
        mock_auth_response.status_code = 200
        mock_auth_response.cookies = httpx.Cookies({"session": "new123"})

        mock_client_cm = mocker.AsyncMock()
        mock_client = mocker.AsyncMock()
        mock_client.get = mocker.AsyncMock(return_value=mock_validate_response)
        mock_client.post = mocker.AsyncMock(return_value=mock_auth_response)

        mock_client_cm.__aenter__.return_value = mock_client
        mock_client_cm.__aexit__.return_value = None

        mocker.patch("httpx.AsyncClient", return_value=mock_client_cm)

        client = SimDBClient()
        cookies = await client._get_cookies()

        assert "session" in cookies
        assert cookies["session"] == "new123"

    async def test_get_cookies_authenticates_on_missing_cache(
        self, mock_settings, mock_cookies_file, mocker
    ):
        """Test authentication when no cache exists."""
        # Mock successful authentication
        mock_auth_response = mocker.Mock()
        mock_auth_response.status_code = 200
        mock_auth_response.cookies = httpx.Cookies({"session": "new456"})

        mock_client_cm = mocker.AsyncMock()
        mock_client_cm.__aenter__.return_value.post = mocker.AsyncMock(
            return_value=mock_auth_response
        )
        mock_client_cm.__aexit__.return_value = None

        mocker.patch("httpx.AsyncClient", return_value=mock_client_cm)

        client = SimDBClient()
        cookies = await client._get_cookies()

        assert "session" in cookies

    async def test_get_cookies_raises_on_auth_failure(
        self, mock_settings, mock_cookies_file, mocker
    ):
        """Test that authentication failure raises AuthenticationError."""
        # Mock failed authentication
        mock_auth_response = mocker.Mock()
        mock_auth_response.status_code = 401

        mock_client_cm = mocker.AsyncMock()
        mock_client_cm.__aenter__.return_value.post = mocker.AsyncMock(
            return_value=mock_auth_response
        )
        mock_client_cm.__aexit__.return_value = None

        mocker.patch("httpx.AsyncClient", return_value=mock_client_cm)

        client = SimDBClient()

        with pytest.raises(AuthenticationError, match="Failed to authenticate"):
            await client._get_cookies()

    async def test_get_cookies_caches_new_cookies(self, mock_settings, mock_cookies_file, mocker):
        """Test that new cookies are cached to disk."""
        # Mock successful authentication
        mock_auth_response = mocker.Mock()
        mock_auth_response.status_code = 200
        mock_auth_response.cookies = httpx.Cookies({"session": "cached789"})

        mock_client_cm = mocker.AsyncMock()
        mock_client_cm.__aenter__.return_value.post = mocker.AsyncMock(
            return_value=mock_auth_response
        )
        mock_client_cm.__aexit__.return_value = None

        mocker.patch("httpx.AsyncClient", return_value=mock_client_cm)

        client = SimDBClient()
        await client._get_cookies()

        # Verify cookies were cached
        assert mock_cookies_file.exists()
        with mock_cookies_file.open("rb") as f:
            cached = pickle.load(f)
        assert "session" in cached


class TestSimDBClientQuery:
    """Tests for SimDBClient.query method."""

    async def test_query_with_constraints(self, mock_settings, mocker):
        """Test querying with constraints."""
        # Mock HTTP response
        mock_response_data = {
            "results": [
                {
                    "uuid": {"hex": "abc123"},
                    "alias": "100001/2",
                    "metadata": [
                        {"element": "machine", "value": "ITER"},
                        {"element": "code.name", "value": "METIS"},
                        {"element": "status", "value": "passed"},
                        {"element": "description", "value": "Test sim"},
                    ],
                }
            ]
        }

        mock_response = mocker.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = mocker.Mock()

        mock_cookies = httpx.Cookies({"session": "test"})
        mocker.patch.object(SimDBClient, "_get_cookies", return_value=mock_cookies)
        mocker.patch.object(SimDBClient, "_detect_api_version", return_value="v1.2")
        mocker.patch.object(SimDBClient, "_make_request", return_value=mock_response)

        client = SimDBClient()
        results = await client.query({"machine": "ITER"}, limit=10)

        assert len(results) == 1
        assert isinstance(results[0], Simulation)
        assert results[0].machine == "ITER"

    async def test_query_with_persistent_client(self, mock_settings, mocker):
        """Test querying with persistent HTTP client (context manager)."""
        mock_response_data = {
            "results": [
                {
                    "uuid": {"hex": "test123"},
                    "alias": "test/1",
                    "metadata": [
                        {"element": "machine", "value": "JET"},
                        {"element": "code.name", "value": "JINTRAC"},
                        {"element": "status", "value": "passed"},
                        {"element": "description", "value": "Test"},
                    ],
                }
            ]
        }

        mock_response = mocker.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = mocker.Mock()

        mock_cookies = httpx.Cookies({"session": "test"})
        mocker.patch.object(SimDBClient, "_get_cookies", return_value=mock_cookies)
        mocker.patch.object(SimDBClient, "_detect_api_version", return_value="v1.2")
        mocker.patch.object(SimDBClient, "_make_request", return_value=mock_response)

        # Use context manager to test persistent client path
        async with SimDBClient() as client:
            results = await client.query({"machine": "JET"}, limit=5)

        assert len(results) == 1
        assert results[0].machine == "JET"

    async def test_query_module_level_function(self, mock_settings, mocker):
        """Test module-level query function."""
        mock_response_data = {
            "results": [
                {
                    "uuid": {"hex": "test123"},
                    "alias": "test/1",
                    "metadata": [
                        {"element": "machine", "value": "JET"},
                        {"element": "code.name", "value": "JINTRAC"},
                        {"element": "status", "value": "passed"},
                        {"element": "description", "value": "Test"},
                    ],
                }
            ]
        }

        mock_response = mocker.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = mocker.Mock()

        mock_cookies = httpx.Cookies({"session": "test"})

        # Mock the client methods
        mocker.patch.object(SimDBClient, "_get_cookies", return_value=mock_cookies)
        mocker.patch.object(SimDBClient, "_detect_api_version", return_value="v1")
        mocker.patch.object(
            SimDBClient,
            "query",
            return_value=[Simulation.from_api_response(mock_response_data["results"][0])],
        )

        results = await query({"machine": "JET"}, limit=5)

        assert len(results) == 1
        assert results[0].machine == "JET"


class TestSimDBClientGetSimulation:
    """Tests for get_simulation function."""

    async def test_get_simulation_by_id(self, mock_settings, mocker):
        """Test getting simulation by ID."""
        sim_data = {
            "uuid": {"hex": "abc123"},
            "alias": "100001/2",
            "metadata": [
                {"element": "machine", "value": "ITER"},
                {"element": "code.name", "value": "METIS"},
                {"element": "status", "value": "passed"},
                {"element": "description", "value": "Test simulation"},
            ],
        }

        mock_response = mocker.Mock()
        mock_response.json.return_value = sim_data
        mock_response.raise_for_status = mocker.Mock()

        mock_cookies = httpx.Cookies({"session": "test"})
        mocker.patch.object(SimDBClient, "_get_cookies", return_value=mock_cookies)
        mocker.patch.object(SimDBClient, "_detect_api_version", return_value="v1.2")
        mocker.patch.object(SimDBClient, "_make_request", return_value=mock_response)

        result = await get_simulation("abc123")

        assert isinstance(result, Simulation)
        assert result.uuid == "abc123"
        assert result.machine == "ITER"


class TestSimDBClientListSimulations:
    """Tests for list_simulations function."""

    async def test_list_simulations(self, mock_settings, mocker):
        """Test listing recent simulations."""
        mock_response_data = {
            "results": [
                {
                    "uuid": {"hex": f"sim{i:03d}"},
                    "alias": f"test/{i}",
                    "metadata": [
                        {"element": "machine", "value": "ITER"},
                        {"element": "code.name", "value": "TEST"},
                        {"element": "status", "value": "passed"},
                        {"element": "description", "value": "Test"},
                    ],
                }
                for i in range(5)
            ]
        }

        mock_response = mocker.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = mocker.Mock()

        mock_cookies = httpx.Cookies({"session": "test"})
        mocker.patch.object(SimDBClient, "_get_cookies", return_value=mock_cookies)
        mocker.patch.object(SimDBClient, "_detect_api_version", return_value="v1.2")
        mocker.patch.object(SimDBClient, "_make_request", return_value=mock_response)

        results = await list_simulations(limit=5)

        assert len(results) == 5
        assert all(isinstance(s, Simulation) for s in results)


class TestSimDBClientAPIVersion:
    """Tests for API version detection."""

    async def test_detect_api_version_v2(self, mock_settings, mocker):
        """Test detecting latest API version."""
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        # API returns endpoints with version in path
        mock_response.json.return_value = {
            "endpoints": [
                "https://simdb.iter.org/scenarios/api/v1.2",
                "https://simdb.iter.org/scenarios/api/v1.1",
            ]
        }

        mock_client_cm = mocker.AsyncMock()
        mock_client_cm.__aenter__.return_value.get = mocker.AsyncMock(return_value=mock_response)
        mock_client_cm.__aexit__.return_value = None

        mocker.patch("httpx.AsyncClient", return_value=mock_client_cm)

        mock_cookies = httpx.Cookies({"session": "test"})
        client = SimDBClient()
        client._cookies = mock_cookies

        version = await client._detect_api_version()

        assert version == "v1.2"

    async def test_detect_api_version_v1_fallback(self, mock_settings, mocker):
        """Test fallback to v1.2 when detection fails."""
        mock_response = mocker.Mock()
        mock_response.json.side_effect = Exception("Parse error")

        mock_client_cm = mocker.AsyncMock()
        mock_client_cm.__aenter__.return_value.get = mocker.AsyncMock(return_value=mock_response)
        mock_client_cm.__aexit__.return_value = None

        mocker.patch("httpx.AsyncClient", return_value=mock_client_cm)

        mock_cookies = httpx.Cookies({"session": "test"})
        client = SimDBClient()
        client._cookies = mock_cookies

        version = await client._detect_api_version()

        assert version == "v1.2"

    async def test_detect_api_version_no_endpoints(self, mock_settings, mocker):
        """Test fallback when no endpoints returned."""
        mock_response = mocker.Mock()
        mock_response.json.return_value = {"endpoints": []}

        mock_client_cm = mocker.AsyncMock()
        mock_client_cm.__aenter__.return_value.get = mocker.AsyncMock(return_value=mock_response)
        mock_client_cm.__aexit__.return_value = None

        mocker.patch("httpx.AsyncClient", return_value=mock_client_cm)

        mock_cookies = httpx.Cookies({"session": "test"})
        client = SimDBClient()
        client._cookies = mock_cookies

        version = await client._detect_api_version()

        assert version == "v1.2"


class TestSimDBClientErrorHandling:
    """Tests for error handling in SimDB client."""

    async def test_make_request_handles_401_error(self, mock_settings, mocker):
        """Test that 401 errors raise AuthenticationError."""
        mock_response = mocker.Mock()
        mock_response.status_code = 401

        http_error = httpx.HTTPStatusError(
            "401 Unauthorized", request=mocker.Mock(), response=mock_response
        )

        mock_client = mocker.AsyncMock()
        mock_client.get = mocker.AsyncMock(side_effect=http_error)

        client = SimDBClient()

        with pytest.raises(AuthenticationError, match="Invalid SimDB credentials"):
            await client._make_request(mock_client, "simulations", {}, {})

    async def test_make_request_handles_500_error(self, mock_settings, mocker):
        """Test that 500 errors raise ConnectionError."""
        from nucleai.core.exceptions import ConnectionError

        mock_response = mocker.Mock()
        mock_response.status_code = 500

        http_error = httpx.HTTPStatusError(
            "500 Server Error", request=mocker.Mock(), response=mock_response
        )

        mock_client = mocker.AsyncMock()
        mock_client.get = mocker.AsyncMock(side_effect=http_error)

        client = SimDBClient()

        with pytest.raises(ConnectionError, match="SimDB server error"):
            await client._make_request(mock_client, "simulations", {}, {})

    async def test_make_request_handles_connection_error(self, mock_settings, mocker):
        """Test that connection errors are properly wrapped."""
        from nucleai.core.exceptions import ConnectionError

        mock_client = mocker.AsyncMock()
        mock_client.get = mocker.AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

        client = SimDBClient()

        with pytest.raises(ConnectionError, match="Cannot connect to SimDB"):
            await client._make_request(mock_client, "simulations", {}, {})

    async def test_make_request_with_metadata_query_string(self, mock_settings, mocker):
        """Test _make_request with metadata fields in endpoint."""
        mock_response = mocker.Mock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = mocker.Mock()

        mock_client = mocker.AsyncMock()
        mock_client.get = mocker.AsyncMock(return_value=mock_response)

        client = SimDBClient()

        # Test endpoint with existing query string
        await client._make_request(
            mock_client, "simulations?description&ids", {"machine": ["ITER"]}, {}
        )

        # Verify URL was constructed correctly
        call_args = mock_client.get.call_args
        assert "?" in call_args[0][0]
        assert "description" in call_args[0][0]

    async def test_get_cookies_handles_connection_error(
        self, mock_settings, mock_cookies_file, mocker
    ):
        """Test that connection errors during auth are properly raised."""
        from nucleai.core.exceptions import ConnectionError

        mock_client_cm = mocker.AsyncMock()
        mock_client_cm.__aenter__.return_value.post = mocker.AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        mock_client_cm.__aexit__.return_value = None

        mocker.patch("httpx.AsyncClient", return_value=mock_client_cm)

        client = SimDBClient()

        with pytest.raises(ConnectionError, match="Cannot connect to SimDB"):
            await client._get_cookies()


class TestSimDBClientDiscoverFields:
    """Tests for discover_available_fields function."""

    async def test_discover_available_fields(self, mock_settings, mocker):
        """Test discovering available metadata fields."""
        from nucleai.simdb.client import discover_available_fields

        mock_response_data = [
            {"name": "machine", "type": "string"},
            {"name": "code.name", "type": "string"},
            {"name": "status", "type": "string"},
        ]

        # Mock the version detection response
        mock_version_response = mocker.Mock()
        mock_version_response.json.return_value = {
            "endpoints": ["https://simdb.iter.org/scenarios/api/v1.2"]
        }

        # Mock the metadata response
        mock_metadata_response = mocker.Mock()
        mock_metadata_response.json.return_value = mock_response_data
        mock_metadata_response.raise_for_status = mocker.Mock()

        # Mock cookies
        mock_cookies = httpx.Cookies({"session": "test"})
        mocker.patch.object(SimDBClient, "_get_cookies", return_value=mock_cookies)

        # Mock AsyncClient context manager for both calls
        mock_client = mocker.AsyncMock()
        mock_client.__aenter__.return_value.get = mocker.AsyncMock(
            side_effect=[mock_version_response, mock_metadata_response]
        )
        mock_client.__aexit__.return_value = None

        mocker.patch("httpx.AsyncClient", return_value=mock_client)

        fields = await discover_available_fields()

        assert len(fields) == 3
        assert fields[0]["name"] == "machine"

    async def test_discover_available_fields_handles_errors(self, mock_settings, mocker):
        """Test that discover_available_fields returns empty list on error."""
        from nucleai.simdb.client import discover_available_fields

        mock_cookies = httpx.Cookies({"session": "test"})
        mocker.patch.object(SimDBClient, "_get_cookies", return_value=mock_cookies)

        # Mock AsyncClient to raise an error
        mock_client = mocker.AsyncMock()
        mock_client.__aenter__.return_value.get = mocker.AsyncMock(
            side_effect=Exception("API error")
        )
        mock_client.__aexit__.return_value = None

        mocker.patch("httpx.AsyncClient", return_value=mock_client)

        fields = await discover_available_fields()

        assert fields == []
