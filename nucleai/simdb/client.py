"""SimDB client for querying ITER simulation database.

Provides async Python interface to SimDB REST API. Uses httpx for HTTP
requests with authentication and connection pooling. All queries automatically
fetch important metadata fields.

Classes:
    SimDBClient: Async client for SimDB REST API operations

Functions:
    query: Query simulations (returns summaries with all fields populated)
    fetch_simulation: Get detailed simulation info by ID (returns complete Simulation)
    list_simulations: List recent simulations (returns summaries)
    discover_available_fields: Get all available fields from API

Auto-Populated Fields:
    All query() and list_simulations() results include:
    - author_email: Email of person who uploaded simulation - use to find user's work
    - description: Detailed scenario description with parameters
    - datetime: Upload timestamp
    - ids_types: Available IDS data types (e.g., ['core_profiles', 'equilibrium'])
    - code: Code name, version, and description
    - ids_properties: IDS file metadata (creation_date, version, homogeneous_time)
    - metadata: All structured metadata fields

    Model schema = API contract: all SimulationSummary fields are always populated.

    For complete simulation data (IMAS URI, files):
    Use fetch_simulation() to get full Simulation object.

Query Filtering:
    Pass filters=None or filters={} to query() to return all simulations (no filtering).
    Pass filters={'field': 'value'} to filter results.

HTTP Error Codes:
    - 401 Unauthorized: Invalid credentials (check SIMDB_USERNAME/PASSWORD)
    - 404 Not Found: Simulation ID not found
    - 500 Internal Server Error: SimDB server error
    - 503 Service Unavailable: SimDB server down

Examples:
    >>> from nucleai.simdb import query
    >>> help(query)

    >>> # Query ITER simulations (metadata auto-fetched)
    >>> results = await query({'machine': 'ITER'}, limit=5)
    >>> for sim in results:
    ...     print(f"{sim.alias}: {sim.author_email}")
    ...     print(f"Description: {sim.description[:80]}...")

    >>> # Search by code name (contains)
    >>> results = await query({'code.name': 'in:METIS'}, limit=10)

    >>> # Multiple filters (AND logic)
    >>> results = await query({'machine': 'ITER', 'status': 'passed'})
    >>>
    >>> # No filters - get all simulations
    >>> all_sims = await query(filters=None, limit=200)
"""

import os
import pickle
from pathlib import Path
from urllib.parse import urlparse

import anyio
import httpx

from nucleai.core.config import get_settings
from nucleai.core.exceptions import AuthenticationError, ConnectionError
from nucleai.simdb.auth import get_credentials
from nucleai.simdb.models import Simulation, SimulationSummary


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
        filters: dict[str, str] | None = None,
        limit: int = 10,
    ) -> list[SimulationSummary]:
        """Query SimDB for simulations matching filters.

        Automatically fetches all fields defined in SimulationSummary model:
        - author_email, description, ids_types, datetime
        - code (name, version, description)
        - ids_properties (creation_date, version, homogeneous_time)
        - All metadata fields

        Args:
            filters: Field-value pairs to filter by. Pass None or {} for no filtering.
                Common fields: 'machine', 'code.name', 'alias', 'status'
                Operators: 'eq:', 'in:', 'gt:', 'ge:', 'lt:', 'le:'
                Example: {'machine': 'ITER', 'code.name': 'in:METIS'}
            limit: Maximum number of results to return

        Returns:
            List of SimulationSummary objects with all fields populated

        Raises:
            AuthenticationError: If credentials are invalid (HTTP 401)
            ConnectionError: If SimDB is unreachable or returns error
            httpx.HTTPStatusError: For other HTTP errors (404, 500, etc.)

        Examples:
            >>> # Find ITER simulations
            >>> results = await client.query({'machine': 'ITER'}, limit=5)

            >>> # Search by code name (contains)
            >>> results = await client.query({'code.name': 'in:METIS'})

            >>> # Multiple filters (AND logic)
            >>> results = await client.query({
            ...     'machine': 'ITER',
            ...     'status': 'passed'
            ... }, limit=10)
            >>>
            >>> # All fields automatically populated
            >>> for sim in results:
            ...     print(f"{sim.alias}: {sim.author_email}")
            ...     print(f"Description: {sim.description[:80]}...")
            >>>
            >>> # No filters - get all simulations
            >>> all_sims = await client.query(filters=None, limit=200)
        """
        # Handle None filters
        if filters is None:
            filters = {}

        # Build query parameters from filters
        params = {}
        for field, value in filters.items():
            # API expects list values for params
            params[field] = [value]

        # Always fetch all fields defined in SimulationSummary model
        metadata_fields = [
            "description",
            "ids",
            "uploaded_by",
            "datetime",
            "code.name",
            "code.version",
            "code.description",
            "ids_properties.creation_date",
            "ids_properties.version_put.data_dictionary",
            "ids_properties.homogeneous_time",
        ]
        metadata_query = "&".join(metadata_fields)
        endpoint = f"simulations?{metadata_query}"

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

        # Parse JSON response to SimulationSummary objects
        data = response.json()
        results = data.get("results", [])
        simulations = [SimulationSummary.from_api_response(sim_data) for sim_data in results]

        # SimDB API returns one more result than requested - slice to exact limit
        return simulations[:limit]

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
    filters: dict[str, str] | None = None,
    limit: int = 10,
) -> list[SimulationSummary]:
    """Query SimDB for simulations matching filters.

    Automatically fetches all fields defined in SimulationSummary model:
    - author_email: Email of person who uploaded simulation - use to find user's work
    - description: Detailed simulation description with scenario parameters
    - datetime: Upload timestamp
    - ids_types: Available IDS data types (e.g., ['core_profiles', 'equilibrium'])
    - code: Code name, version, and description
    - ids_properties: IDS file metadata (creation_date, version, homogeneous_time)
    - All metadata fields defined in SimulationMetadata

    Args:
        filters: Field-value pairs to filter by. Pass None or {} for no filtering.
        limit: Maximum number of results

    Returns:
        List of SimulationSummary objects with all fields populated

    Raises:
        AuthenticationError: If credentials are invalid
        ConnectionError: If SimDB is unreachable

    Natural Language Query Patterns:
        "Find simulations by user X"
        >>> all_sims = await query(filters=None, limit=200)
        >>> user_sims = [s for s in all_sims if s.author_email and 'Florian.Koechl' in s.author_email]

        "Show ITER simulations"
        >>> results = await query({'machine': 'ITER'}, limit=50)

        "What JINTRAC simulations are available?"
        >>> results = await query({'code.name': 'in:JINTRAC'}, limit=50)

        "Find passed simulations on ITER"
        >>> results = await query({'machine': 'ITER', 'status': 'passed'})

        "What data types are available for this simulation?"
        >>> sim = results[0]
        >>> print(sim.ids_types)  # ['core_profiles', 'equilibrium', ...]

        "Get the latest simulation"
        >>> all_sims = await query(filters=None, limit=100)
        >>> latest = max(all_sims, key=lambda s: s.metadata.datetime or '')

        "Find latest simulation by user X"
        >>> all_sims = await query(filters=None, limit=200)
        >>> user_sims = [s for s in all_sims if s.author_email and 'Florian.Koechl' in s.author_email]
        >>> if user_sims:
        ...     latest = user_sims[0]  # Already sorted by most recent
        ...     complete = await fetch_simulation(latest.uuid)
        ...     print(f"IMAS URI: {complete.imas_uri}")

    Examples:
        >>> from nucleai.simdb import query, fetch_simulation

        >>> # Query simulations (metadata auto-fetched)
        >>> results = await query({'machine': 'ITER'}, limit=5)
        >>> for sim in results:
        ...     print(f"{sim.alias}: {sim.code.name} by {sim.author}")
        ...     print(f"Description: {sim.description[:100]}...")

        >>> # Find user's simulations
        >>> all_sims = await query(filters=None, limit=200)
        >>> florian_sims = [s for s in all_sims if s.author_email and 'Florian.Koechl' in s.author_email]
        >>> if florian_sims:
        ...     latest = florian_sims[0]
        ...     sim = await fetch_simulation(latest.uuid)
        ...     print(f"IMAS URI: {sim.imas_uri}")

        >>> # Search by code name, then fetch complete details
        >>> summaries = await query({'code.name': 'in:JINTRAC'}, limit=10)
        >>> latest = max(summaries, key=lambda s: s.metadata.datetime or '')
        >>> complete = await fetch_simulation(latest.uuid)
        >>> if complete.imas_uri:
        ...     print(f"IMAS: {complete.imas_uri}")

        >>> # Multiple filters (AND logic)
        >>> results = await query({
        ...     'machine': 'ITER',
        ...     'code.name': 'in:JINTRAC',
        ...     'status': 'passed'
        ... })
        >>> latest = max(results, key=lambda s: s.metadata.datetime or '')
        >>> print(f"Latest: {latest.alias} ({latest.metadata.datetime})")
    """
    client = SimDBClient()
    return await client.query(filters, limit)


async def fetch_simulation(simulation_id: str) -> Simulation:
    """Get detailed simulation information by ID.

    Fetches full simulation details including inputs/outputs with IMAS URIs
    and all simulation artifact files. Returns complete information with:
    - Basic metadata (alias, code, description, status)
    - IMAS URI (sim.imas_uri) for direct access
    - All data objects (sim.outputs, sim.inputs) with checksums
    - Structured metadata (datetime, composition, etc.)

    Args:
        simulation_id: Simulation UUID or alias

    Returns:
        Simulation object with full metadata, inputs, and outputs

    Raises:
        ConnectionError: If SimDB is unreachable or simulation not found
        AuthenticationError: If credentials are invalid

    Examples:
        >>> from nucleai.simdb import fetch_simulation
        >>> import imas
        >>>
        >>> # Get simulation with IMAS data
        >>> sim = await fetch_simulation("koechlf/jetto/iter/53298/oct1118/seq-1")
        >>> print(f"Code: {sim.code.name} v{sim.code.version}")
        >>> print(f"Status: {sim.status}")
        >>> print(f"Uploaded: {sim.metadata.datetime}")
        >>>
        >>> # Simple IMAS access
        >>> if sim.imas_uri:
        ...     print(f"IMAS URI: {sim.imas_uri}")
        ...     with imas.DBEntry(sim.imas_uri, "r") as entry:
        ...         equilibrium = entry.get("equilibrium")
        ...         print(f"Time points: {len(equilibrium.time)}")
        >>>
        >>> # Rich IMAS access (parsed structure)
        >>> if sim.imas:
        ...     uri = sim.imas.uri
        ...     print(f"Backend: {uri.backend}")
        ...     print(f"Server: {uri.server}")
        ...     print(f"Remote: {uri.is_remote}")
        >>>
        >>> # Access all simulation files
        >>> print(f"Total outputs: {len(sim.outputs)}")
        >>> for obj in sim.outputs:
        ...     if obj.type == 'FILE':
        ...         filename = obj.uri.split('/')[-1]
        ...         print(f"  {filename}: {obj.checksum[:8]}...")
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


async def list_simulations(limit: int = 10) -> list[SimulationSummary]:
    """List recent simulations from SimDB.

    Args:
        limit: Maximum number of simulations to return

    Returns:
        List of recent SimulationSummary objects

    Raises:
        ConnectionError: If SimDB is unreachable
        AuthenticationError: If credentials are invalid

    Examples:
        >>> from nucleai.simdb import list_simulations
        >>> recent = await list_simulations(limit=10)
        >>> for sim in recent:
        ...     print(f"{sim.alias}: {sim.machine}")
    """
    return await query(filters=None, limit=limit)


async def discover_available_fields() -> list[dict[str, str]]:
    """Discover all available metadata fields from SimDB REST API.

    Returns list of dicts with 'name' (field path) and 'type' (data type).
    Use for exploring what fields are queryable via constraints parameter.

    Most fields are ndarray time series - use IDS download for those.
    Query functions automatically fetch important metadata fields.

    Returns:
        List of dicts with keys:
            - 'name': Field path (e.g., 'global_quantities.ip.value')
            - 'type': Data type ('str', 'int', 'float', 'ndarray')

    Examples:
        >>> from nucleai.simdb import discover_available_fields
        >>>
        >>> # Returns list of dicts, not strings
        >>> all_fields = await discover_available_fields()
        >>> print(all_fields[0])  # {'name': 'machine', 'type': 'str'}
        >>>
        >>> # Access field names
        >>> field_names = [f['name'] for f in all_fields]
        >>> print('machine' in field_names)  # True
        >>>
        >>> # Filter by type
        >>> from collections import Counter
        >>> type_counts = Counter(f['type'] for f in all_fields)
        >>> print(type_counts)  # {'ndarray': 377, 'str': 184, ...}
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

            # API returns list of {name, type} dicts
            return response.json()

    except Exception:
        # If metadata endpoint doesn't exist or fails, return empty list
        return []
