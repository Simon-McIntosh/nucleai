"""ITER SimDB integration module.

This module provides async Python interfaces to ITER's SimDB REST API for
querying and retrieving fusion simulation data. Authentication uses environment
variables to support non-interactive agent workflows.

REST API Access:
    Direct HTTP access via httpx to SimDB REST API at:
    https://simdb.iter.org/scenarios/api/v1.2/

    Authentication: F5 firewall via POST /my.policy (automatic)
    Cookie caching: ~/.config/simdb/iter-cookies.pkl
    Auto-detects latest API version with v1.2 fallback

Modules:
    client: SimDBClient class and convenience functions
    auth: Credential management and authentication

Data Models:
    nucleai.core.models.Simulation: Unified model for all simulation metadata
    - Uses model_config(extra="allow") for unknown API fields
    - Parse JSON via from_api_response() classmethod

    Discover available fields:
    >>> from nucleai.core.models import Simulation
    >>> print(Simulation.model_json_schema()['properties'].keys())

Environment Variables:
    SIMDB_USERNAME: ITER username
    SIMDB_PASSWORD: ITER password
    SIMDB_REMOTE_URL: SimDB API base URL (default: https://simdb.iter.org/scenarios/api)

Query Operators:
    eq: - Exact match (default, can omit)
    in: - Contains substring (case-insensitive)
    gt:, ge:, lt:, le: - Numeric comparisons
    agt:, age:, alt:, ale: - Array element comparisons

Metadata Extraction:
    Use include_metadata parameter to request fields beyond basic ones.

    Available metadata fields:
    - 'uploaded_by': Author email addresses (comma-separated if multiple)
    - 'code.name', 'code.version': Code identification (version may be N/A)
    - 'status', 'description': Simulation metadata
    - Physics quantities: See discover_available_fields() for full list

    NOTE: Metadata must be explicitly requested via include_metadata parameter.
    Default query returns only: alias, machine, datetime, uuid

    Discover all available fields:
    >>> fields = await nucleai.simdb.discover_available_fields()
    >>> print(list(fields.keys()))

HTTP Status Codes:
    - 200: Success
    - 401: Authentication failed (check credentials)
    - 404: Simulation not found
    - 500: Server error

Examples:
    >>> import nucleai.simdb
    >>> from nucleai.core.introspect import get_docstring

    >>> # Read full documentation
    >>> print(get_docstring(nucleai.simdb))

    >>> # Basic query (minimal metadata)
    >>> results = await nucleai.simdb.query({'machine': 'ITER'}, limit=5)
    >>> for sim in results:
    ...     print(sim.alias)

    >>> # Query with metadata (includes author emails)
    >>> results = await nucleai.simdb.query(
    ...     {'machine': 'ITER', 'code.name': 'in:JINTRAC'},
    ...     limit=10,
    ...     include_metadata=['uploaded_by', 'code.name', 'code.version']
    ... )
    >>> for sim in results:
    ...     print(f"{sim.alias}: {sim.uploaded_by}")

    >>> # Query by code with operator
    >>> results = await nucleai.simdb.query(
    ...     {'machine': 'ITER', 'code.name': 'eq:ASTRA'},
    ...     limit=5,
    ...     include_metadata=['code.name']
    ... )

    >>> # Batch queries with persistent connection
    >>> async with nucleai.simdb.SimDBClient() as client:
    ...     iter_sims = await client.query({'machine': 'ITER'}, limit=100)
    ...     jet_sims = await client.query({'machine': 'JET'}, limit=100)

    >>> # Count simulations by code
    >>> from collections import Counter
    >>> results = await nucleai.simdb.query(
    ...     {'machine': 'ITER'},
    ...     limit=5000,
    ...     include_metadata=['code.name']
    ... )
    >>> code_counts = Counter(sim.code.name for sim in results if sim.code)
    >>> for code, count in code_counts.most_common(5):
    ...     print(f"{code}: {count}")
"""

from nucleai.simdb.client import (
    SimDBClient,
    discover_available_fields,
    get_simulation,
    list_simulations,
    query,
)

__all__ = [
    "SimDBClient",
    "query",
    "get_simulation",
    "list_simulations",
    "discover_available_fields",
]
