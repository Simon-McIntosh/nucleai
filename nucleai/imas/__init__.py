"""IMAS data access with automatic performance optimization.

Provides high-level interface to IMAS data with automatic conversion from
remote UDA access to local file access when data exists locally (81x speedup).

Classes:
    ImasUri: IMAS URI with automatic optimization
    IdsLoader: Load IDS data with lazy loading support

Exceptions:
    ImasAccessError: Connection or authentication failures
    ImasDataError: Missing or malformed IDS data
    ImasConversionError: xarray conversion issues

Examples:
    >>> from nucleai.imas import IdsLoader
    >>> from nucleai.simdb import fetch_simulation
    >>>
    >>> # Load from simulation
    >>> sim = await fetch_simulation("koechlf/jetto/iter/53298/oct1118/seq-1")
    >>> loader = IdsLoader.from_simulation(sim)
    >>>
    >>> # Load equilibrium IDS with lazy loading
    >>> async with loader:
    ...     equilibrium = await loader.get("equilibrium", lazy=True)
    ...     print(f"Time points: {len(equilibrium.time)}")
    ...     ip = float(equilibrium.time_slice[0].global_quantities.ip)
    ...     print(f"Plasma current: {ip/1e6:.2f} MA")
    >>>
    >>> # Direct URI usage
    >>> from nucleai.imas import ImasUri
    >>> uri = ImasUri.from_string("imas://uda.iter.org/uda?path=/work/imas/data&backend=hdf5")
    >>> # Automatic optimization - str(uri) returns local path if data exists locally
    >>> print(uri.original)  # Original UDA URI
    >>> print(str(uri))      # Optimal URI (local if available)
"""

from nucleai.core.models import ImasUri
from nucleai.imas.exceptions import (
    ImasAccessError,
    ImasConversionError,
    ImasDataError,
)
from nucleai.imas.loader import IdsLoader

__all__ = [
    "ImasAccessError",
    "ImasConversionError",
    "ImasDataError",
    "IdsLoader",
    "ImasUri",
]
