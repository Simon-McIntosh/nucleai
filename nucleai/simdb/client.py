"""SimDB client for querying ITER simulation database.

Provides async Python interface to SimDB REST API. Uses httpx for HTTP
requests with authentication and connection pooling.

Classes:
    SimDBClient: Async client for SimDB REST API operations

Functions:
    query: Query simulations with constraints
    get_simulation: Get detailed simulation info by ID
    list_simulations: List recent simulations
    discover_available_fields: Get available metadata fields from API

Metadata Fields:
    Request with include_metadata parameter:
    - 'code.name', 'code.version', 'code.commit', 'code.repository'
    - 'uploaded_by': Email address(es) of uploader (comma-separated)
    - 'status': 'passed', 'pending', 'failed'
    - 'description': Text description
    - 'ids': Available IDS types (e.g., 'core_profiles', 'equilibrium')
    - 'simulation.time_begin', 'simulation.time_end', 'simulation.time_step'
    - 'ids_properties.creation_date', 'ids_properties.version_put.data_dictionary'
    - Physics quantities: 'global_quantities.ip.value', 'heating_current_drive.*'
    - 'composition.*', 'fusion.*', 'local.*', 'volume_average.*'

    Use discover_available_fields() to query current API schema dynamically.

HTTP Error Codes:
    - 401 Unauthorized: Invalid credentials (check SIMDB_USERNAME/PASSWORD)
    - 404 Not Found: Simulation ID not found
    - 500 Internal Server Error: SimDB server error
    - 503 Service Unavailable: SimDB server down

Examples:
    >>> from nucleai.simdb import query
    >>> help(query)

    >>> # Query ITER simulations
    >>> results = await query({'machine': 'ITER'}, limit=5)
    >>> for sim in results:
    ...     print(f"{sim.alias}: {sim.code.name}")

    >>> # Search by code name (contains)
    >>> results = await query({'code.name': 'in:METIS'}, limit=10)

    >>> # Multiple constraints (AND logic)
    >>> results = await query({'machine': 'ITER', 'status': 'passed'})

    >>> # Request specific metadata fields
    >>> results = await query(
    ...     {'machine': 'ITER'},
    ...     include_metadata=['uploaded_by', 'code.name', 'description']
    ... )

    >>> # Batch queries with persistent connection
    >>> from nucleai.simdb import SimDBClient
    >>> async with SimDBClient() as client:
    ...     iter_sims = await client.query({'machine': 'ITER'}, limit=100)
    ...     jet_sims = await client.query({'machine': 'JET'}, limit=100)
"""

import os
import pickle
from pathlib import Path
from urllib.parse import urlparse

import anyio
import httpx

from nucleai.core.config import get_settings
from nucleai.core.exceptions import AuthenticationError, ConnectionError
from nucleai.core.models import Simulation
from nucleai.simdb.auth import get_credentials


class SimDBClient:
    """Async client for ITER SimDB REST API operations.

    Provides HTTP-based access to SimDB with authentication and connection
    pooling. Supports context manager for persistent connections across
    multiple queries.

    Attributes:
        settings: Application settings with SimDB configuration
        _client: Optional persistent httpx.AsyncClient (when used as context manager)

    Examples:
        >>> from nucleai.simdb import SimDBClient
        >>>
        >>> # One-off query (ephemeral client)
        >>> client = SimDBClient()
        >>> results = await client.query({'machine': 'ITER'}, limit=5)
        >>> print(len(results))
        5
        >>>
        >>> # Batch queries (persistent connection)
        >>> async with SimDBClient() as client:
        ...     iter_sims = await client.query({'machine': 'ITER'}, limit=100)
        ...     jet_sims = await client.query({'machine': 'JET'}, limit=100)
    """

    def __init__(self) -> None:
        """Initialize SimDB client with configuration."""
        self.settings = get_settings()
        self._client: httpx.AsyncClient | None = None
        self._api_version: str | None = None
        self._cookies: httpx.Cookies | None = None

    async def __aenter__(self) -> "SimDBClient":
        """Context manager entry - create persistent HTTP client."""
        # Authenticate and get cookies
        self._cookies = await self._get_cookies()

        # Detect API version
        self._api_version = await self._detect_api_version()

        self._client = httpx.AsyncClient(
            base_url=f"{self.settings.simdb_remote_url}/{self._api_version}/",
            cookies=self._cookies,
            headers={"User-Agent": "it_script_basic"},
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )
        return self

    async def __aexit__(self, *args) -> None:
        """Context manager exit - close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _get_cookies(self) -> httpx.Cookies:
        """Get authentication cookies via F5 firewall.

        Loads cached cookies from ~/.config/simdb/iter-cookies.pkl if valid,
        otherwise authenticates via /my.policy endpoint and caches cookies.

        Returns:
            httpx.Cookies object with authentication cookies

        Raises:
            AuthenticationError: If authentication fails
        """
        # Cookie cache path
        config_dir = Path.home() / ".config" / "simdb"
        cookies_file = config_dir / "iter-cookies.pkl"

        # Try loading cached cookies
        if cookies_file.exists():
            try:
                async with await anyio.open_file(cookies_file, "rb") as f:
                    cached_cookie_dict = pickle.loads(await f.read())

                # Convert dict to httpx.Cookies
                cookie_jar = httpx.Cookies(cached_cookie_dict)

                # Validate cookies with test request
                async with httpx.AsyncClient(
                    base_url=self.settings.simdb_remote_url,
                    cookies=cookie_jar,
                    headers={"User-Agent": "it_script_basic"},
                    timeout=30.0,
                ) as client:
                    response = await client.get("/")
                    try:
                        response.json()  # Valid cookies should return JSON
                        return cookie_jar  # Cookies are valid!
                    except Exception:
                        pass  # Cookies invalid, continue to re-auth

            except Exception:
                pass  # Failed to load/validate, continue to re-auth

        # Cookies missing or invalid - authenticate via F5 firewall
        username, password = get_credentials()
        parsed_url = urlparse(self.settings.simdb_remote_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        try:
            async with httpx.AsyncClient(
                headers={"User-Agent": "it_script_basic"},
                timeout=30.0,
                follow_redirects=True,
            ) as client:
                response = await client.post(
                    f"{base_url}/my.policy",
                    auth=(username, password),
                )

                if response.status_code != 200:
                    raise AuthenticationError(
                        "Failed to authenticate with F5 firewall",
                        recovery_hint="Check SIMDB_USERNAME and SIMDB_PASSWORD in .env",
                    )

                # Extract cookies for caching (httpx cookies aren't directly picklable)
                # Simplified: just store name-value pairs
                cookie_dict = dict(response.cookies)

                # Cache cookies
                config_dir.mkdir(parents=True, exist_ok=True)
                os.umask(0)
                descriptor = os.open(
                    path=cookies_file,
                    flags=os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                    mode=0o600,
                )
                async with await anyio.open_file(descriptor, "wb") as f:
                    await f.write(pickle.dumps(cookie_dict))

                return response.cookies

        except httpx.ConnectError as e:
            raise ConnectionError(
                f"Cannot connect to SimDB at {base_url}",
                recovery_hint="Check network connection and SIMDB_REMOTE_URL setting",
            ) from e

    async def _detect_api_version(self) -> str:
        """Detect latest compatible API version from server.

        Returns:
            API version string (e.g., "v1.2")
        """
        try:
            async with httpx.AsyncClient(
                base_url=self.settings.simdb_remote_url,
                cookies=self._cookies,
                headers={"User-Agent": "it_script_basic"},
                timeout=30.0,
            ) as client:
                response = await client.get("/")
                data = response.json()
                endpoints = data.get("endpoints", [])

                if not endpoints:
                    return "v1.2"  # Fallback to known version

                # Extract versions from endpoint URLs
                versions = [ep.split("/")[-1] for ep in endpoints if "/v" in ep]
                return max(versions) if versions else "v1.2"

        except Exception:
            # If detection fails, use hardcoded fallback
            return "v1.2"

    async def query(
        self,
        constraints: dict[str, str],
        limit: int = 10,
        include_metadata: list[str] | None = None,
    ) -> list[Simulation]:
        """Query SimDB for simulations matching constraints.

        Args:
            constraints: Field-value pairs to filter by.
                Common fields: 'machine', 'code.name', 'alias', 'status'
                Operators: 'eq:', 'in:', 'gt:', 'ge:', 'lt:', 'le:'
                Example: {'machine': 'ITER', 'code.name': 'in:METIS'}
            limit: Maximum number of results to return
            include_metadata: Additional metadata fields to include as query parameters.
                Common fields: 'uploaded_by', 'code.name', 'code.version',
                'status', 'description'.
                Example: ['uploaded_by', 'code.name', 'code.version']

        Returns:
            List of Simulation objects parsed from JSON response

        Raises:
            AuthenticationError: If credentials are invalid (HTTP 401)
            ConnectionError: If SimDB is unreachable or returns error
            httpx.HTTPStatusError: For other HTTP errors (404, 500, etc.)

        Examples:
            >>> # Find ITER simulations
            >>> results = await client.query({'machine': 'ITER'}, limit=5)

            >>> # Search by code name (contains)
            >>> results = await client.query({'code.name': 'in:METIS'})

            >>> # Multiple constraints (AND logic)
            >>> results = await client.query({
            ...     'machine': 'ITER',
            ...     'status': 'passed'
            ... }, limit=10)
            >>>
            >>> # Request specific metadata fields
            >>> results = await client.query(
            ...     {'machine': 'ITER'},
            ...     include_metadata=['uploaded_by', 'description']
            ... )
        """
        # Build query parameters from constraints
        params = {}
        for field, value in constraints.items():
            # API expects list values for params
            params[field] = [value]

        # Build endpoint with metadata fields in query string
        endpoint = "simulations"
        if include_metadata:
            # Metadata fields go in URL query string (no values)
            metadata_query = "&".join(include_metadata)
            endpoint = f"{endpoint}?{metadata_query}"

        # Build HTTP headers for pagination
        headers = {
            "simdb-result-limit": str(limit),
            "simdb-page": "1",
        }

        # Use persistent client if available, otherwise create ephemeral
        if self._client:
            response = await self._make_request(self._client, endpoint, params, headers)
        else:
            cookies = await self._get_cookies()
            api_version = await self._detect_api_version()

            async with httpx.AsyncClient(
                base_url=f"{self.settings.simdb_remote_url}/{api_version}/",
                cookies=cookies,
                headers={"User-Agent": "it_script_basic"},
                timeout=30.0,
            ) as client:
                response = await self._make_request(client, endpoint, params, headers)

        # Parse JSON response to Simulation objects
        data = response.json()
        results = data.get("results", [])
        return [Simulation.from_api_response(sim_data) for sim_data in results]

    async def _make_request(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        params: dict,
        headers: dict,
    ) -> httpx.Response:
        """Make HTTP request with error handling.

        Args:
            client: httpx client to use
            endpoint: API endpoint path (may include query string for metadata fields)
            params: Query parameters (constraint key-value pairs)
            headers: HTTP headers

        Returns:
            HTTP response

        Raises:
            AuthenticationError: On HTTP 401
            ConnectionError: On connection errors or HTTP 5xx
        """
        from urllib.parse import urlencode

        try:
            # Build URL with both metadata query string and constraint params
            if "?" in endpoint:
                # Endpoint has metadata fields, append constraint params
                constraint_params = []
                for key, values in params.items():
                    for value in values:
                        constraint_params.append((key, value))
                param_string = urlencode(constraint_params)
                full_url = f"{endpoint}&{param_string}" if param_string else endpoint
                response = await client.get(full_url, headers=headers)
            else:
                response = await client.get(endpoint, params=params, headers=headers)

            response.raise_for_status()
            return response

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError(
                    "Invalid SimDB credentials",
                    recovery_hint="Check SIMDB_USERNAME and SIMDB_PASSWORD in .env",
                ) from e
            if e.response.status_code >= 500:
                raise ConnectionError(
                    f"SimDB server error: HTTP {e.response.status_code}",
                    recovery_hint="SimDB server may be experiencing issues. Try again later.",
                ) from e
            raise

        except httpx.ConnectError as e:
            raise ConnectionError(
                f"Cannot connect to SimDB at {self.settings.simdb_remote_url}",
                recovery_hint="Check network connection and SIMDB_REMOTE_URL setting",
            ) from e


async def query(
    constraints: dict[str, str],
    limit: int = 10,
    include_metadata: list[str] | None = None,
) -> list[Simulation]:
    """Query SimDB for simulations matching constraints.

    Convenience function that creates a SimDBClient and executes query.

    Args:
        constraints: Field-value pairs to filter by
        limit: Maximum number of results
        include_metadata: List of metadata fields to include in results.
            IMPORTANT: Fields like uploaded_by, code.name, status, description
            are only available if explicitly requested here. Default query
            returns only alias and machine.

    Returns:
        List of Simulation objects matching constraints

    Raises:
        AuthenticationError: If credentials are invalid
        ConnectionError: If SimDB is unreachable

    Examples:
        >>> from nucleai.simdb import query

        >>> # Basic query (only alias and machine)
        >>> results = await query({'machine': 'ITER'}, limit=5)
        >>> for sim in results:
        ...     print(sim.alias)

        >>> # Query with metadata (including author emails)
        >>> results = await query(
        ...     {'machine': 'ITER', 'code.name': 'in:JINTRAC'},
        ...     limit=10,
        ...     include_metadata=['uploaded_by', 'code.name', 'code.version']
        ... )
        >>> for sim in results:
        ...     print(f"{sim.alias}: {sim.uploaded_by}")
    """
    client = SimDBClient()
    return await client.query(constraints, limit, include_metadata)


async def get_simulation(simulation_id: str) -> Simulation:
    """Get detailed simulation information by ID.

    Args:
        simulation_id: Simulation UUID

    Returns:
        Simulation object with full metadata

    Raises:
        ConnectionError: If SimDB is unreachable or simulation not found
        AuthenticationError: If credentials are invalid

    Examples:
        >>> from nucleai.simdb import get_simulation
        >>> sim = await get_simulation("123e4567-e89b-12d3-a456-426614174000")
        >>> print(sim.description)
    """
    client = SimDBClient()
    cookies = await client._get_cookies()
    api_version = await client._detect_api_version()

    async with httpx.AsyncClient(
        base_url=f"{client.settings.simdb_remote_url}/{api_version}/",
        cookies=cookies,
        headers={"User-Agent": "it_script_basic"},
        timeout=30.0,
    ) as http_client:
        response = await client._make_request(
            http_client,
            f"simulation/{simulation_id}",
            params={},
            headers={},
        )
        data = response.json()
        return Simulation.from_api_response(data)


async def list_simulations(limit: int = 10) -> list[Simulation]:
    """List recent simulations from SimDB.

    Args:
        limit: Maximum number of simulations to return

    Returns:
        List of recent Simulation objects

    Raises:
        ConnectionError: If SimDB is unreachable
        AuthenticationError: If credentials are invalid

    Examples:
        >>> from nucleai.simdb import list_simulations
        >>> recent = await list_simulations(limit=10)
        >>> for sim in recent:
        ...     print(f"{sim.alias}: {sim.machine}")
    """
    return await query({}, limit=limit)


async def discover_available_fields() -> list[dict[str, str]]:
    """Discover all 611 metadata fields available from SimDB REST API.

    CRITICAL for AI agents: Use this function to discover what metadata you can
    request. The API provides 611 fields across 18 categories including plasma
    parameters, heating data, composition, and more.

    Returns a list of field metadata dictionaries with 'name' and 'type' keys.
    These field names can be used in the include_metadata parameter of query().

    Returns:
        List of dicts with keys:
            - 'name': Field path (e.g., 'global_quantities.ip.value')
            - 'type': Data type ('str', 'int', 'float', 'ndarray', etc.)

    Field Categories (top 10 by count):
        - local: 288 fields (local plasma parameters)
        - heating_current_drive: 64 fields (heating & current drive)
        - global_quantities: 56 fields (Ip, beta, b0, etc.)
        - code: 27 fields (code metadata)
        - fusion: 27 fields (fusion reactions)
        - composition: 17 fields (D, T, He, impurities)
        - boundary: 23 fields (plasma boundary)
        - volume_average: 20 fields (volume-averaged quantities)
        - line_average: 18 fields (line-averaged quantities)
        - scrape_off_layer: 15 fields (SOL parameters)

    Commonly Used Fields:
        - machine, code.name, code.version, status, uploaded_by
        - global_quantities.ip.value (plasma current time trace)
        - global_quantities.b0.value (magnetic field)
        - composition.deuterium.value, composition.helium.value
        - heating_current_drive.ec[0].power.value
        - simulation.time_begin, simulation.time_end
        - ids (list of available IDS types like 'equilibrium', 'core_profiles')

    Note: These fields reflect IDS (IMAS Data Structure) schema. Not all
    fields have data for all simulations. Use include_metadata with specific
    field names to request them in query().

    Examples:
        >>> from nucleai.simdb import discover_available_fields
        >>>
        >>> # Get all available fields
        >>> fields = await discover_available_fields()
        >>> print(f"Total fields: {len(fields)}")  # 611
        >>>
        >>> # Find plasma current field
        >>> ip_fields = [f for f in fields if 'ip' in f['name'].lower()]
        >>> print(ip_fields[0]['name'])  # 'global_quantities.ip.value'
        >>>
        >>> # Group by category
        >>> from collections import defaultdict
        >>> categories = defaultdict(list)
        >>> for field in fields:
        ...     category = field['name'].split('.')[0]
        ...     categories[category].append(field)
        >>> print(f"Categories: {list(categories.keys())}")
        >>>
        >>> # Request specific fields in a query
        >>> from nucleai.simdb import query
        >>> results = await query(
        ...     {'machine': 'ITER'},
        ...     include_metadata=['global_quantities.ip.value', 'composition.deuterium.value']
        ... )
    """
    settings = get_settings()
    client = SimDBClient()
    cookies = await client._get_cookies()

    # Detect API version
    try:
        async with httpx.AsyncClient(
            base_url=settings.simdb_remote_url,
            cookies=cookies,
            headers={"User-Agent": "it_script_basic"},
            timeout=30.0,
        ) as http_client:
            response = await http_client.get("/")
            data = response.json()
            endpoints = data.get("endpoints", [])
            versions = [ep.split("/")[-1] for ep in endpoints if "/v" in ep]
            api_version = max(versions) if versions else "v1.2"
    except Exception:
        api_version = "v1.2"

    # Try to fetch metadata
    try:
        async with httpx.AsyncClient(
            base_url=f"{settings.simdb_remote_url}/{api_version}/",
            cookies=cookies,
            headers={"User-Agent": "it_script_basic"},
            timeout=30.0,
        ) as http_client:
            response = await http_client.get("metadata")
            response.raise_for_status()

            data = response.json()
            # Assuming metadata endpoint returns {"fields": [{"name": "...", "description": "..."}, ...]}
            if "fields" in data:
                return {field["name"]: field.get("description", "") for field in data["fields"]}
            # Alternative format: direct field->description mapping
            return data

    except Exception:
        # If metadata endpoint doesn't exist or fails, return empty dict
        return {}
