"""Generic Pydantic data models for nucleai.

This module defines generic data structures used across nucleai modules.
For SimDB-specific models, see nucleai.simdb.models.

Classes:
    SearchResult: Generic search result with similarity score
    FeatureMetadata: Feature extraction metadata

Examples:
    >>> from nucleai.core.models import SearchResult
    >>> result = SearchResult(
    ...     id="sim-001",
    ...     content="ITER baseline scenario",
    ...     similarity=0.92,
    ...     metadata={"machine": "ITER"}
    ... )
"""

from typing import Literal

import pydantic


class SearchResult(pydantic.BaseModel):
    """Search result with similarity score.

    Attributes:
        id: Unique identifier for the result
        content: Result content or description
        similarity: Similarity score (0.0 to 1.0)
        metadata: Additional metadata dictionary

    Examples:
        >>> result = SearchResult(
        ...     id="sim-001",
        ...     content="ITER baseline scenario",
        ...     similarity=0.92,
        ...     metadata={"machine": "ITER", "code": "METIS"}
        ... )
        >>> print(result.similarity)
        0.92
        >>> print(result.metadata["machine"])
        ITER
    """

    id: str
    content: str
    similarity: float
    metadata: dict[str, str | float | int] = pydantic.Field(default_factory=dict)


class FeatureMetadata(pydantic.BaseModel):
    """Feature extraction metadata.

    Attributes:
        name: Feature name
        type: Feature type (time_series, spatial, statistical)
        source: Data source (e.g., "global_quantities.ip")
        units: Physical units
        description: Feature description

    Examples:
        >>> feature = FeatureMetadata(
        ...     name="plasma_current",
        ...     type="time_series",
        ...     source="global_quantities.ip",
        ...     units="A",
        ...     description="Plasma current evolution"
        ... )
        >>> print(feature.name)
        plasma_current
        >>> print(feature.units)
        A
    """

    name: str
    type: Literal["time_series", "spatial", "statistical"]
    source: str
    units: str
    description: str


BackendType = Literal["hdf5", "netcdf", "ascii", "mdsplus", "uda", "memory"]


class ImasUri(pydantic.BaseModel):
    """IMAS URI with automatic remote-to-local conversion.

    Parses IMAS URIs and provides automatic conversion from remote UDA access
    to local file access when data files exist locally.

    Attributes:
        original: Original URI string
        backend: Backend type
        is_remote: True if URI uses remote server
        server: Remote server hostname
        port: Remote server port
        path: File system path to data
        shot: Shot number (legacy format)
        run: Run number (legacy format)
        database: Database name (legacy format)
        user: User name (legacy format)
        version: DD version (legacy format)
    """

    original: str
    backend: BackendType
    is_remote: bool = False
    server: str | None = None
    port: int | None = None
    path: str | None = None
    shot: int | None = None
    run: int | None = None
    database: str | None = None
    user: str | None = None
    version: str | None = None

    @classmethod
    def from_string(cls, uri: str) -> "ImasUri":
        """Parse IMAS URI string."""
        from pathlib import Path
        from urllib.parse import parse_qs, urlparse

        if not uri.startswith("imas"):
            path = Path(uri)
            backend = "netcdf" if path.suffix == ".nc" else "hdf5"
            return cls(original=uri, backend=backend, is_remote=False, path=str(path))

        parsed = urlparse(uri)
        query = parse_qs(parsed.query) if parsed.query else {}
        backend = query.get("backend", [None])[0]
        if not backend and parsed.path:
            backend = parsed.path.lstrip("/").split("?")[0]
        is_remote = parsed.netloc != ""
        server = parsed.hostname if is_remote else None
        port = parsed.port if is_remote else None
        path = query.get("path", [None])[0]
        shot = query.get("shot", [None])[0]
        run = query.get("run", [None])[0]
        database = query.get("database", [None])[0]
        user = query.get("user", [None])[0]
        version_str = query.get("version", [None])[0]
        shot = int(shot) if shot else None
        run = int(run) if run else None
        return cls(
            original=uri,
            backend=backend or "unknown",
            is_remote=is_remote,
            server=server,
            port=port,
            path=path,
            shot=shot,
            run=run,
            database=database,
            user=user,
            version=version_str,
        )

    def can_convert_to_local(self) -> bool:
        """Check if URI can be converted to local access."""
        if not self.is_remote or not self.path:
            return False
        return self._local_files_exist()

    def _local_files_exist(self) -> bool:
        """Check if local IMAS files exist at path."""
        from pathlib import Path

        if not self.path:
            return False
        path = Path(self.path)
        if self.backend == "hdf5":
            return (path / "master.h5").exists()
        if self.backend == "netcdf":
            if path.suffix == ".nc":
                return path.exists()
            return len(list(path.glob("*.nc"))) > 0
        if self.backend == "ascii":
            return len(list(path.glob("*.ids"))) > 0
        return False

    def to_local(self) -> str:
        """Convert to local URI format."""
        import warnings

        if not self.can_convert_to_local():
            if not self.is_remote:
                return self.original
            warnings.warn(
                f"Cannot convert remote URI to local (files not found at {self.path}). Using original remote URI.",
                stacklevel=2,
            )
            return self.original
        return f"imas:{self.backend}?path={self.path}"

    def __str__(self) -> str:
        """Return optimal URI (local if available, otherwise original)."""
        if self.is_remote and self.can_convert_to_local():
            return self.to_local()
        return self.original
