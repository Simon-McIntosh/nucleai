"""ITER SimDB integration module.

This module provides async Python interfaces to ITER's SimDB for querying and
retrieving fusion simulation data. Authentication uses environment variables
to support non-interactive agent workflows.

Modules:
    client: SimDBClient class for querying simulations
    auth: Credential management and authentication
    parser: Parse SimDB CLI output to Python objects

Environment Variables:
    SIMDB_USERNAME: ITER username
    SIMDB_PASSWORD: ITER password
    SIMDB_REMOTE_URL: SimDB API endpoint
    SIMDB_REMOTE_NAME: SimDB remote name

Examples:
    >>> import nucleai.simdb
    >>> help(nucleai.simdb.query)

    >>> # Query simulations
    >>> results = await nucleai.simdb.query({'machine': 'ITER'}, limit=5)
    >>> for sim in results:
    ...     print(sim.alias, sim.code.name)
"""

from nucleai.simdb.client import SimDBClient, get_simulation, list_simulations, query

__all__ = ["SimDBClient", "query", "get_simulation", "list_simulations"]
