"""IDS data loading with imas-python and xarray conversion.

Provides async interface to imas-python for loading IDS data with automatic
URI optimization, lazy loading support, and xarray conversion capabilities.

Thread Safety:
    IdsLoader uses a threading.Lock to serialize all access to the underlying
    imas.DBEntry. This is necessary because imas-python's IDSMetadata is not
    thread-safe when accessed concurrently from multiple Python threads.

    The anyio.to_thread.run_sync() calls run blocking HDF5 I/O in worker threads,
    but the lock ensures only one thread executes IMAS operations at a time.

Classes:
    IdsLoader: Load IDS data from URIs or Simulation objects

Examples:
    >>> from nucleai.imas import IdsLoader
    >>> from nucleai.simdb import fetch_simulation
    >>>
    >>> # Load from simulation
    >>> sim = await fetch_simulation("koechlf/jetto/iter/53298/oct1118/seq-1")
    >>> loader = IdsLoader.from_simulation(sim)
    >>>
    >>> # Get IDS with lazy loading
    >>> async with loader:
    ...     equilibrium = await loader.get("equilibrium", lazy=True)
    ...     print(f"Time points: {len(equilibrium.time)}")
"""

import ctypes
import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

import anyio

from nucleai.core.models import ImasUri
from nucleai.imas.exceptions import ImasAccessError, ImasDataError

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Thread-local storage to track if HDF5 errors have been suppressed
_hdf5_errors_suppressed = threading.local()

# Global lock to serialize all IMAS-python access
# This prevents race conditions in imas-python's IDSMetadata
_imas_lock = threading.Lock()


def _suppress_hdf5_errors() -> None:
    """Suppress HDF5 error output for the current thread.

    HDF5's error handler is thread-local, so this must be called in each
    worker thread before making HDF5 calls. This prevents noisy error
    messages when HDF5 attempts read-write access before falling back
    to read-only.
    """
    if getattr(_hdf5_errors_suppressed, "done", False):
        return  # Already suppressed in this thread

    try:
        # Locate the bundled HDF5 library from imas_core
        from pathlib import Path

        import imas_core

        imas_core_path = Path(imas_core.__file__).parent.parent / "imas_core.libs"
        hdf5_lib = next(imas_core_path.glob("libhdf5.so.*"), None)

        if hdf5_lib:
            hdf5 = ctypes.CDLL(str(hdf5_lib))
            h5e_default = ctypes.c_int64(0)
            hdf5.H5Eset_auto2(h5e_default, None, None)
            _hdf5_errors_suppressed.done = True
    except Exception:
        pass  # Silently ignore if we can't suppress - errors are just noise anyway


class IdsLoader:
    """Load IDS data with automatic URI optimization.

    Handles IMAS data access via imas-python with automatic conversion from
    remote UDA to local file access when data exists locally (81x speedup).
    Supports lazy loading and xarray conversion.

    Attributes:
        uri: ImasUri object managing data access and optimization
        entry: Open imas.DBEntry (None until connected)

    Examples:
        >>> from nucleai.imas import IdsLoader
        >>> from nucleai.simdb import fetch_simulation
        >>>
        >>> # From Simulation
        >>> sim = await fetch_simulation("100001/2")
        >>> loader = IdsLoader.from_simulation(sim)
        >>>
        >>> # From URI string
        >>> loader = IdsLoader("imas://uda.iter.org/uda?path=/work/imas/data&backend=hdf5")
        >>>
        >>> # From ImasUri object
        >>> from nucleai.imas import ImasUri
        >>> uri = ImasUri.from_string("imas:hdf5?path=/work/imas/data")
        >>> loader = IdsLoader(uri)
        >>>
        >>> # Use with context manager
        >>> async with loader:
        ...     eq = await loader.get("equilibrium", lazy=True)
        ...     print(f"Plasma current: {eq.time_slice[0].global_quantities.ip/1e6:.2f} MA")
    """

    def __init__(self, uri: str | ImasUri) -> None:
        """Initialize loader with IMAS URI.

        Args:
            uri: IMAS URI string or ImasUri object

        Examples:
            >>> loader = IdsLoader("imas:hdf5?path=/work/imas/data")
            >>> # Or with ImasUri object
            >>> uri = ImasUri.from_string("imas:hdf5?path=/work/imas/data")
            >>> loader = IdsLoader(uri)
        """
        if isinstance(uri, str):
            self.uri = ImasUri.from_string(uri)
        else:
            self.uri = uri

        self.entry: Any = None  # imas.DBEntry when connected

    @classmethod
    def from_simulation(cls, simulation: Any) -> "IdsLoader":
        """Create loader from SimDB simulation.

        Extracts IMAS URI from simulation metadata and creates loader with
        automatic optimization.

        Args:
            simulation: Simulation object from fetch_simulation()

        Returns:
            IdsLoader instance

        Raises:
            ImasAccessError: If simulation has no IMAS data

        Examples:
            >>> from nucleai.simdb import fetch_simulation
            >>> sim = await fetch_simulation("100001/2")
            >>> loader = IdsLoader.from_simulation(sim)
            >>> async with loader:
            ...     ids_names = await loader.list_ids()
        """
        if not simulation.imas_uri:
            msg = f"Simulation {simulation.alias} has no IMAS data (imas_uri is None)"
            raise ImasAccessError(
                msg,
                recovery_hint="Check that simulation has IMAS outputs. "
                "Try sim.outputs to see available data types.",
            )

        return cls(simulation.imas_uri)

    @classmethod
    def from_file(cls, path: str | Path) -> "IdsLoader":
        """Create loader from local HDF5/netCDF file.

        Args:
            path: Path to local IMAS file (*.h5, *.nc, or directory with master.h5)

        Returns:
            IdsLoader instance

        Examples:
            >>> loader = IdsLoader.from_file("/work/imas/data/master.h5")
            >>> loader = IdsLoader.from_file("/work/imas/data/simulation.nc")
            >>> loader = IdsLoader.from_file("/work/imas/data")  # Directory with master.h5
        """
        path_obj = Path(path)

        # Single file
        if path_obj.is_file():
            if path_obj.suffix == ".nc":
                return cls(str(path_obj))
            if path_obj.suffix == ".h5":
                # Use parent directory for HDF5 backend
                return cls(f"imas:hdf5?path={path_obj.parent}")

        # Directory
        if path_obj.is_dir():
            # Check for HDF5 backend
            if (path_obj / "master.h5").exists():
                return cls(f"imas:hdf5?path={path_obj}")
            # Check for netCDF files
            nc_files = list(path_obj.glob("*.nc"))
            if nc_files:
                return cls(str(nc_files[0]))

        msg = f"Cannot find IMAS data at {path}"
        raise ImasAccessError(
            msg,
            recovery_hint="Path should be a directory with master.h5, a .h5 file, or a .nc file",
        )

    async def connect(self) -> None:
        """Open IMAS DBEntry connection.

        Uses optimal URI (local if available, otherwise remote). Connection
        is cached and reused. Access is serialized via threading lock.

        Raises:
            ImasAccessError: If connection fails

        Examples:
            >>> loader = IdsLoader("imas:hdf5?path=/work/imas/data")
            >>> await loader.connect()
            >>> # Connection now open, can call get()
        """
        if self.entry is not None:
            logger.debug("Already connected to IMAS entry")
            return  # Already connected

        def _connect():
            import imas

            _suppress_hdf5_errors()
            optimal_uri = str(self.uri)  # Gets optimal URI automatically
            logger.debug("Acquiring IMAS lock for connection")
            with _imas_lock:
                logger.info("Connecting to IMAS: %s", optimal_uri)
                return imas.DBEntry(optimal_uri, "r")

        try:
            self.entry = await anyio.to_thread.run_sync(_connect)
            logger.debug("IMAS connection established")
        except Exception as e:
            msg = f"Failed to open IMAS data entry: {e}"
            raise ImasAccessError(
                msg,
                recovery_hint="Check that imas-python is installed and URI is valid. "
                "For remote UDA access, imas_core must be installed.",
            ) from e

    async def disconnect(self) -> None:
        """Close IMAS DBEntry connection.

        Examples:
            >>> await loader.disconnect()
        """
        if self.entry is not None:
            self.entry.close()
            self.entry = None

    async def get(self, ids_name: str, *, lazy: bool = True) -> Any:
        """Get IDS data structure.

        Access is serialized via threading lock to prevent race conditions
        in imas-python's IDSMetadata.

        Args:
            ids_name: IDS name (e.g., 'equilibrium', 'core_profiles')
            lazy: Use lazy loading (default True for better performance)

        Returns:
            IDS toplevel object from imas-python

        Raises:
            ImasDataError: If IDS not found or read fails

        Examples:
            >>> async with loader:
            ...     # Lazy loading (recommended)
            ...     equilibrium = await loader.get("equilibrium", lazy=True)
            ...     ip = float(equilibrium.time_slice[0].global_quantities.ip)
            ...     print(f"Plasma current: {ip/1e6:.2f} MA")
            ...
            ...     # Eager loading (loads all data immediately)
            ...     core_profiles = await loader.get("core_profiles", lazy=False)
        """
        if self.entry is None:
            msg = "Loader not connected. Call connect() or use context manager."
            raise ImasDataError(
                msg,
                recovery_hint="Use 'async with loader:' or call 'await loader.connect()'",
            )

        def _get_ids():
            _suppress_hdf5_errors()
            logger.debug("Acquiring IMAS lock for get('%s')", ids_name)
            with _imas_lock:
                logger.info("Loading IDS '%s' (lazy=%s)", ids_name, lazy)
                result = self.entry.get(ids_name, lazy=lazy)
                logger.debug("IDS '%s' loaded successfully", ids_name)
                return result

        try:
            # Run in thread pool since imas.DBEntry.get() is blocking
            # Lock ensures serialized access to imas-python internals
            return await anyio.to_thread.run_sync(_get_ids)
        except Exception as e:
            msg = f"Failed to load IDS '{ids_name}': {e}"
            raise ImasDataError(
                msg,
                recovery_hint=f"Check that IDS '{ids_name}' exists with loader.list_ids(). "
                "Available IDS types depend on simulation code used.",
            ) from e

    async def list_ids(self) -> list[str]:
        """List available IDS names in this data entry.

        Access is serialized via threading lock.

        Returns:
            List of IDS names present in the data

        Raises:
            ImasDataError: If listing fails

        Examples:
            >>> async with loader:
            ...     ids_names = await loader.list_ids()
            ...     print(f"Available IDS: {', '.join(ids_names)}")
        """
        if self.entry is None:
            msg = "Loader not connected. Call connect() or use context manager."
            raise ImasDataError(
                msg,
                recovery_hint="Use 'async with loader:' or call 'await loader.connect()'",
            )

        def _list_ids():
            _suppress_hdf5_errors()
            logger.debug("Acquiring IMAS lock for list_ids")
            with _imas_lock:
                logger.info("Listing available IDS")
                result = self.entry.list_all_occurrences("")
                logger.debug("Found %d IDS entries", len(result))
                return result

        try:
            return await anyio.to_thread.run_sync(_list_ids)
        except Exception as e:
            msg = f"Failed to list IDS: {e}"
            raise ImasDataError(msg, recovery_hint="Check data entry is valid") from e

    async def __aenter__(self) -> "IdsLoader":
        """Context manager entry - connect to data.

        Examples:
            >>> async with loader:
            ...     eq = await loader.get("equilibrium")
        """
        await self.connect()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Context manager exit - disconnect from data."""
        await self.disconnect()
