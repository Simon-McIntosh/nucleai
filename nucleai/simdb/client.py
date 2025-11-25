"""SimDB client for querying ITER simulation database.

Provides async Python interface to SimDB CLI commands. Wraps CLI calls
in subprocess execution with credential management for non-interactive use.

Classes:
    SimDBClient: Async client for SimDB operations

Functions:
    query: Query simulations with constraints
    get_simulation: Get detailed simulation info by ID
    list_simulations: List recent simulations

Metadata Fields:
    Default fields: alias, machine

    Request additional with include_metadata parameter:
    - 'code.name', 'code.version', 'code.commit', 'code.repository'
    - 'uploaded_by': Email address(es) of uploader (comma-separated)
    - 'status': 'passed', 'pending', 'failed'
    - 'description': Text description
    - 'ids': Available IDS types (e.g., 'core_profiles', 'equilibrium')
    - 'simulation.time_begin', 'simulation.time_end', 'simulation.time_step'
    - 'ids_properties.creation_date', 'ids_properties.version_put.data_dictionary'
    - Physics quantities: 'global_quantities.ip.value', 'heating_current_drive.*'
    - 'composition.*', 'fusion.*', 'local.*', 'volume_average.*'

    Note: Most physics fields empty in query output. Use 'simdb remote info <id>'
    for full metadata. Explore schema: 'simdb remote schema --depth 3'

Author Extraction:
    Many simulations lack user metadata fields. Extract from alias instead:
    - Named format: 'username/code/machine/...' -> extract 'username'
    - Numeric format: '104001/11' -> no author available
    Use split('/')[0] and check if isdigit() to distinguish formats.

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

    >>> # Request metadata fields (note: may be empty)
    >>> results = await query(
    ...     {'machine': 'ITER'},
    ...     include_metadata=['code.name', 'code.version', 'user']
    ... )

    >>> # Extract author from alias when metadata unavailable
    >>> import anyio
    >>> cmd = ['uv', 'run', 'simdb', 'remote', 'query',
    ...        'machine=ITER', 'code.name=in:JINTRAC',
    ...        '-m', 'code.name', '--limit', '100']
    >>> result = await anyio.run_process(cmd, check=True)
    >>> output = result.stdout.decode()
    >>> # Parse table and extract username from alias field:
    >>> # if alias contains '/', split and check if first part isdigit()
"""

import anyio

from nucleai.core.config import get_settings
from nucleai.core.exceptions import ConnectionError
from nucleai.core.models import Simulation
from nucleai.simdb.auth import get_credentials
from nucleai.simdb.parser import parse_query_output


class SimDBClient:
    """Async client for ITER SimDB operations.

    Wraps SimDB CLI commands in async subprocess execution. Handles
    authentication via environment variables.

    Attributes:
        settings: Application settings with SimDB configuration

    Examples:
        >>> from nucleai.simdb import SimDBClient
        >>> client = SimDBClient()
        >>> results = await client.query({'machine': 'ITER'}, limit=5)
        >>> print(len(results))
        5
    """

    def __init__(self) -> None:
        """Initialize SimDB client with configuration."""
        self.settings = get_settings()

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
            include_metadata: Additional metadata fields to include in query.
                REQUIRED to get fields beyond alias and machine.
                Common fields: 'uploaded_by' (email), 'code.name', 'code.version',
                'status', 'description'.
                Example: ['uploaded_by', 'code.name', 'code.version']

        Returns:
            List of Simulation objects matching constraints.
            Note: Parser currently maps limited fields. For rich metadata,
            use run_process() directly and parse output table yourself.

        Raises:
            AuthenticationError: If credentials are invalid
            ConnectionError: If SimDB is unreachable
            ValidationError: If constraints are malformed

        Examples:
            >>> # Find ITER simulations
            >>> results = await query({'machine': 'ITER'}, limit=5)

            >>> # Search by code name (contains)
            >>> results = await query({'code.name': 'in:METIS'})

            >>> # Power greater than 20 MW
            >>> results = await query({
            ...     'heating_current_drive.power_additional.value': 'gt:20000000'
            ... })

            >>> # Multiple constraints (AND logic)
            >>> results = await query({
            ...     'machine': 'ITER',
            ...     'status': 'passed'
            ... }, limit=10)
        """
        # Build constraint arguments
        constraint_args = []
        for field, value in constraints.items():
            if value.startswith(("eq:", "in:", "gt:", "ge:", "lt:", "le:")):
                constraint_args.append(f"{field}={value}")
            else:
                # Default to exact match
                constraint_args.append(f"{field}={value}")

        # Get credentials
        username, password = get_credentials()

        # Build command with authentication
        cmd = [
            "uv",
            "run",
            "simdb",
            "remote",
            "--username",
            username,
            "--password",
            password,
            "query",
            *constraint_args,
            "--limit",
            str(limit),
        ]

        # Add metadata columns if requested
        if include_metadata:
            for field in include_metadata:
                cmd.extend(["-m", field])

        # Execute command
        try:
            result = await anyio.run_process(cmd, check=False)

            if result.returncode != 0:
                error_msg = result.stderr.decode() if result.stderr else "Unknown error"
                raise ConnectionError(
                    f"SimDB query failed: {error_msg}",
                    recovery_hint="Check credentials and network: uv run simdb remote test",
                )

            output = result.stdout.decode()
            return parse_query_output(output)

        except FileNotFoundError as e:
            raise ConnectionError(
                "simdb CLI not found",
                recovery_hint="Install simdb: uv add imas-simdb",
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
        simulation_id: Simulation ID in format "run/version" (e.g., "100001/2")

    Returns:
        Simulation object with detailed metadata

    Raises:
        ConnectionError: If SimDB is unreachable or simulation not found

    Examples:
        >>> from nucleai.simdb import get_simulation
        >>> sim = await get_simulation("100001/2")
        >>> print(sim.description)
    """
    raise NotImplementedError("get_simulation not yet implemented")


async def list_simulations(limit: int = 10) -> list[Simulation]:
    """List recent simulations from SimDB.

    Args:
        limit: Maximum number of simulations to return

    Returns:
        List of recent Simulation objects

    Raises:
        ConnectionError: If SimDB is unreachable

    Examples:
        >>> from nucleai.simdb import list_simulations
        >>> recent = await list_simulations(limit=10)
        >>> for sim in recent:
        ...     print(f"{sim.alias}: {sim.machine}")
    """
    raise NotImplementedError("list_simulations not yet implemented")
