"""ITER SimDB integration module.

This module provides async Python interfaces to ITER's SimDB for querying and
retrieving fusion simulation data. Authentication uses environment variables
to support non-interactive agent workflows.

Modules:
    client: SimDBClient class for querying simulations
    auth: Credential management and authentication
    parser: Parse SimDB CLI output to Python objects

Data Models:
    nucleai.core.models.Simulation: Unified model for all simulation metadata
    - Basic fields always present (from query)
    - Extended fields optional (from 'simdb remote info')

    Discover available fields:
    >>> from nucleai.core.models import Simulation
    >>> print(Simulation.model_json_schema()['properties'].keys())

Environment Variables:
    SIMDB_USERNAME: ITER username
    SIMDB_PASSWORD: ITER password
    SIMDB_REMOTE_URL: SimDB API endpoint
    SIMDB_REMOTE_NAME: SimDB remote name

Metadata Extraction:
    IMPORTANT: Use include_metadata parameter to request fields beyond alias/machine.

    Commonly requested fields:
    - 'uploaded_by': Author email addresses (comma-separated if multiple)
    - 'code.name', 'code.version': Code identification
    - 'status', 'description': Simulation metadata

    For detailed physics data, use 'simdb remote info <id>' which returns:
    - Full IDS metadata and physics quantities
    - Global quantities (ip, energy, beta, etc.)
    - Composition, heating, fusion rates
    - Profiles and local values

    Explore available fields: 'simdb remote schema --depth 3'

Examples:
    >>> import nucleai.simdb
    >>> from nucleai.core.introspect import get_docstring

    >>> # Read full documentation
    >>> print(get_docstring(nucleai.simdb))

    >>> # Basic query (only alias and machine in results)
    >>> results = await nucleai.simdb.query({'machine': 'ITER'}, limit=5)
    >>> for sim in results:
    ...     print(sim.alias)  # sim.uploaded_by will be None

    >>> # Query with metadata (includes author emails)
    >>> results = await nucleai.simdb.query(
    ...     {'machine': 'ITER', 'code.name': 'in:JINTRAC'},
    ...     limit=10,
    ...     include_metadata=['uploaded_by', 'code.name', 'code.version']
    ... )
    >>> for sim in results:
    ...     print(f"{sim.alias}: {sim.uploaded_by}")
"""

from nucleai.simdb.client import SimDBClient, get_simulation, list_simulations, query

__all__ = ["SimDBClient", "query", "get_simulation", "list_simulations"]
