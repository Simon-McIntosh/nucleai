"""ITER SimDB integration module.

This module provides async Python interfaces to ITER's SimDB REST API for
querying and retrieving fusion simulation data. All queries automatically
include reliable metadata fields validated against the database.

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
    nucleai.simdb.models.Simulation: Simulation with metadata
    - Core fields always present: uuid, alias, machine, code, status, description
    - Metadata fields auto-fetched: uploaded_by, datetime, ids_properties
    - Access via sim.uploaded_by and sim.metadata.ids_properties

    Discover model structure:
    >>> from nucleai.simdb.models import Simulation
    >>> print(Simulation.model_json_schema())

Environment Variables:
    SIMDB_USERNAME: ITER username
    SIMDB_PASSWORD: ITER password
    SIMDB_REMOTE_URL: SimDB API base URL (default: https://simdb.iter.org/scenarios/api)

Query Operators:
    eq: - Exact match (default, can omit)
    in: - Contains substring (case-insensitive)
    gt:, ge:, lt:, le: - Numeric comparisons
    agt:, age:, alt:, ale: - Array element comparisons

Metadata:
    All queries automatically fetch reliable metadata:
    - uploaded_by: Author email(s) - populated for most codes except SOLPS
    - datetime: Upload timestamp - always populated
    - ids_properties.creation_date: IDS file creation date
    - ids_properties.version_put.data_dictionary: IDS schema version
    - ids_properties.homogeneous_time: Time grid structure

    For additional data (physics parameters, time series):
    Use IDS file download with simulation UUID (coming soon)

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

    >>> # Query simulations (metadata auto-fetched)
    >>> results = await nucleai.simdb.query({'machine': 'ITER'}, limit=5)
    >>> for sim in results:
    ...     print(f"{sim.alias}: {sim.uploaded_by}")
    ...     print(f"  IDS version: {sim.metadata.ids_properties.version_put_data_dictionary}")

    >>> # Search by code
    >>> results = await nucleai.simdb.query({'code.name': 'in:METIS'}, limit=10)
    >>> for sim in results:
    ...     print(f"{sim.alias}: {sim.code.name} v{sim.code.version}")

    >>> # Multiple constraints (AND logic)
    >>> results = await nucleai.simdb.query(
    ...     {'machine': 'ITER', 'status': 'passed'}
    ... )

    >>> # Batch queries with persistent connection
    >>> async with nucleai.simdb.SimDBClient() as client:
    ...     iter_sims = await client.query({'machine': 'ITER'}, limit=100)
    ...     jet_sims = await client.query({'machine': 'JET'}, limit=100)

    >>> # Access IDS types for further data retrieval
    >>> sim = results[0]
    >>> print(f"Available IDS types: {sim.ids}")
    >>> # TODO: Download IDS file with UUID for physics data
    >>> # ids_data = await download_ids_file(sim.uuid, 'core_profiles')
"""

from nucleai.simdb.client import (
    SimDBClient,
    discover_available_fields,
    fetch_simulation,
    list_simulations,
    query,
)
from nucleai.simdb.dataframe import query_sql
from nucleai.simdb.models import CodeInfo, QueryConstraint, Simulation, SimulationSummary

__all__ = [
    "SimDBClient",
    "query",
    "fetch_simulation",
    "list_simulations",
    "discover_available_fields",
    "Simulation",
    "SimulationSummary",
    "CodeInfo",
    "CodeInfo",
    "QueryConstraint",
    "query_sql",
]

__agent_exposed__ = True
