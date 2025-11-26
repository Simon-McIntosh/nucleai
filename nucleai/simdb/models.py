"""Pydantic models for SimDB data structures.

This module defines data models for ITER SimDB simulations using Pydantic
for validation and JSON schema generation.

Note: Import Simulation from nucleai.simdb.models, not nucleai.core.models.

Classes:
    ImasUri: Parsed IMAS URI with structured component access
    ImasDataCollection: Collection of IMAS input/output URIs
    DataObject: SimDB data object (file or IMAS data)
    CodeInfo: Simulation code metadata
    Simulation: SimDB simulation record with metadata
    QueryConstraint: SimDB query constraint with operator

Examples:
    >>> from nucleai.simdb import get_simulation
    >>>
    >>> # Get simulation with IMAS data
    >>> sim = await get_simulation("100001/2")
    >>> print(sim.alias, sim.machine, sim.code.name)
    >>>
    >>> # Access IMAS data
    >>> if sim.imas:
    ...     uri = sim.imas.uri  # Primary IMAS URI
    ...     print(f"Backend: {uri.backend}")
    ...     print(f"Remote: {uri.is_remote}")
    ...
    ...     # Use with imas-python
    ...     import imas
    ...     with imas.DBEntry(str(uri), "r") as entry:
    ...         equilibrium = entry.get("equilibrium", lazy=True)
"""

from typing import Literal
from urllib.parse import parse_qs, urlparse

import pydantic

from nucleai.simdb.metadata import SimulationMetadata


class DataObject(pydantic.BaseModel):
    """SimDB data object (input/output file or IMAS data).

    Represents a file or IMAS data entry associated with a simulation.
    Used in inputs and outputs lists.

    Attributes:
        uuid: Unique identifier for this data object
        uri: Resource URI (file:// for files, imas: for IDS data)
        type: Object type ("FILE" or "IMAS")
        checksum: SHA-1 checksum of the data
        datetime: Upload timestamp

    Examples:
        >>> obj = DataObject(
        ...     uuid="abc123",
        ...     uri="imas://uda.iter.org/uda?path=/work/imas/shared/imasdb/ITER/3/100001/2&backend=hdf5",
        ...     type="IMAS"
        ... )
        >>> print(obj.uri)
        imas://uda.iter.org/uda?path=/work/imas/shared/imasdb/ITER/3/100001/2&backend=hdf5
    """

    uuid: str
    uri: str
    type: Literal["FILE", "IMAS"] | None = None
    checksum: str | None = None
    datetime: str | None = None

    @pydantic.field_validator("uuid", mode="before")
    @classmethod
    def parse_uuid(cls, value):
        """Parse UUID from API format."""
        if isinstance(value, dict) and "hex" in value:
            return value["hex"]
        return value


class ImasUri(pydantic.BaseModel):
    """Parsed IMAS URI with structured access to components.

    Supports both modern (AL5) and legacy (AL4) URI formats:
    - Remote: imas://server:port/uda?path=/work/...&backend=hdf5
    - Local: imas:hdf5?path=/work/...
    - Legacy: imas:?shot=100001&run=2&user=public&database=ITER&backend=hdf5

    Attributes:
        raw: Original URI string
        backend: Backend type (hdf5, mdsplus, ascii, etc.)
        is_remote: True if remote UDA access
        server: Remote server hostname (for remote URIs)
        port: Remote server port (for remote URIs)
        path: File system path to data
        shot: Shot/pulse number (for legacy URIs)
        run: Run number (for legacy URIs)
        database: Database name (for legacy URIs)
        user: User name (for legacy URIs)
        version: Data version (for legacy URIs)

    Examples:
        >>> uri = ImasUri.parse("imas://uda.iter.org/uda?path=/work/imas/shared/imasdb/ITER/3/100001/2&backend=hdf5")
        >>> uri.backend
        'hdf5'
        >>> uri.is_remote
        True
        >>> uri.server
        'uda.iter.org'
        >>> str(uri)  # Returns raw URI for imas.DBEntry()
        'imas://uda.iter.org/uda?path=/work/imas/shared/imasdb/ITER/3/100001/2&backend=hdf5'
    """

    raw: str
    backend: str
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
    def parse(cls, uri: str) -> "ImasUri":
        """Parse IMAS URI string into structured format.

        Args:
            uri: IMAS URI string

        Returns:
            Parsed ImasUri instance

        Examples:
            >>> uri = ImasUri.parse("imas://uda.iter.org/uda?path=/work/...&backend=hdf5")
            >>> uri.backend
            'hdf5'
        """
        parsed = urlparse(uri)
        query = parse_qs(parsed.query) if parsed.query else {}

        # Extract backend
        backend = query.get("backend", [None])[0]
        if not backend and parsed.path:
            # Local format: imas:hdf5?path=...
            backend = parsed.path.lstrip("/").split("?")[0]

        # Check if remote (UDA)
        is_remote = parsed.netloc != ""
        server = parsed.hostname if is_remote else None
        port = parsed.port if is_remote else None

        # Extract path
        path = query.get("path", [None])[0]

        # Extract legacy format fields
        shot = query.get("shot", [None])[0]
        run = query.get("run", [None])[0]
        database = query.get("database", [None])[0]
        user = query.get("user", [None])[0]
        version = query.get("version", [None])[0]

        # Convert numeric fields
        shot = int(shot) if shot else None
        run = int(run) if run else None

        return cls(
            raw=uri,
            backend=backend or "unknown",
            is_remote=is_remote,
            server=server,
            port=port,
            path=path,
            shot=shot,
            run=run,
            database=database,
            user=user,
            version=version,
        )

    def __str__(self) -> str:
        """Return raw URI string for use with imas.DBEntry()."""
        return self.raw


class ImasDataCollection(pydantic.BaseModel):
    """IMAS data URIs for simulation inputs and outputs.

    Most simulations have exactly one output URI pointing to an IMAS data entry
    containing multiple IDS types (equilibrium, core_profiles, etc.).

    Attributes:
        inputs: List of input IMAS URIs (rarely used)
        outputs: List of output IMAS URIs (typically one per simulation)

    Examples:
        >>> # Get the main IMAS URI
        >>> if sim.imas:
        ...     with imas.DBEntry(str(sim.imas.uri), "r") as entry:
        ...         equilibrium = entry.get("equilibrium", lazy=True)
        >>>
        >>> # Access specific outputs
        >>> for uri in sim.imas.outputs:
        ...     print(f"Backend: {uri.backend}, Path: {uri.path}")
        >>>
        >>> # Check if remote
        >>> if sim.imas.uri and sim.imas.uri.is_remote:
        ...     print(f"Remote: {uri.server}:{uri.port}")
    """

    inputs: list[ImasUri] = []
    outputs: list[ImasUri] = []

    @property
    def uri(self) -> ImasUri | None:
        """Get IMAS data entry URI (output preferred, fallback to input).

        Returns the simulation's IMAS data location. Most simulations have
        exactly one output URI containing all IDS data.

        Returns:
            ImasUri or None if no IMAS data exists

        Examples:
            >>> uri = sim.imas.uri
            >>> if uri:
            ...     print(f"Backend: {uri.backend}")
            ...     with imas.DBEntry(str(uri), "r") as entry:
            ...         data = entry.get("equilibrium")
        """
        return self.outputs[0] if self.outputs else (self.inputs[0] if self.inputs else None)

    def __bool__(self) -> bool:
        """True if any IMAS data exists."""
        return bool(self.outputs or self.inputs)


class CodeInfo(pydantic.BaseModel):
    """Simulation code information.

    Attributes:
        name: Code name (e.g., METIS, JINTRAC, ASTRA)
        version: Code version string (e.g., "1.2.3"), optional

    Examples:
        >>> code = CodeInfo(name="METIS", version="1.0.0")
        >>> print(code.name)
        METIS
        >>> print(code.model_dump())
        {'name': 'METIS', 'version': '1.0.0'}
    """

    name: str
    version: str | None = None


class Simulation(pydantic.BaseModel):
    """ITER SimDB simulation metadata.

    Single model for both query results and detailed info. Basic fields
    (uuid, alias, machine, code, description, status) always present.
    Extended fields (uploaded_by, ids, metadata) auto-fetched by query().

    Attributes:
        uuid: Unique simulation identifier (UUID format)
        alias: Human-readable alias (e.g., "100001/2")
        machine: Machine name (e.g., "ITER")
        code: Simulation code information
        description: Detailed simulation description
        status: Validation status (passed, failed, pending)
        uploaded_by: Email address(es) of uploader (optional, varies by code)
        ids: Available IDS types (e.g., ['core_profiles', 'equilibrium'])
        metadata: Structured metadata (access via sim.metadata.datetime, etc.)

    Examples:
        >>> from nucleai.simdb import query
        >>>
        >>> # Query returns Simulation with metadata auto-fetched
        >>> results = await query({'machine': 'ITER'}, limit=5)
        >>> sim = results[0]
        >>>
        >>> # Access basic fields (always present)
        >>> print(sim.uuid, sim.alias, sim.machine)
        >>> print(sim.code.name, sim.code.version)
        >>> print(sim.description[:100])  # Often long text
        >>>
        >>> # Access metadata (auto-fetched)
        >>> print(sim.uploaded_by)  # May be None for some codes
        >>> print(sim.ids)  # List of IDS types
        >>> print(sim.metadata.datetime)  # Upload timestamp
        >>> print(sim.metadata.composition.deuterium)  # If available
    """

    uuid: str
    alias: str
    machine: str
    code: CodeInfo
    description: str
    status: Literal["passed", "failed", "pending"]
    uploaded_by: str | None = None
    ids: list[str] | None = None
    metadata: SimulationMetadata | None = None
    inputs: list[DataObject] | None = None
    outputs: list[DataObject] | None = None

    @property
    def imas(self) -> ImasDataCollection:
        """IMAS data URIs with structured access.

        Returns a collection containing parsed IMAS URIs for both inputs and outputs.
        Most simulations have exactly one output URI.

        Returns:
            ImasDataCollection with parsed URIs

        Examples:
            >>> sim = await get_simulation("100001/2")
            >>>
            >>> # Get the main URI
            >>> if sim.imas:
            ...     uri = sim.imas.uri
            ...     print(f"Backend: {uri.backend}")
            ...     with imas.DBEntry(str(uri), "r") as entry:
            ...         equilibrium = entry.get("equilibrium", lazy=True)
            >>>
            >>> # Access all outputs
            >>> for uri in sim.imas.outputs:
            ...     print(f"{uri.backend}: {uri.path}")
            >>>
            >>> # Check if remote
            >>> if sim.imas.uri and sim.imas.uri.is_remote:
            ...     print(f"Server: {sim.imas.uri.server}")
        """
        inputs = [ImasUri.parse(obj.uri) for obj in (self.inputs or []) if obj.type == "IMAS"]
        outputs = [ImasUri.parse(obj.uri) for obj in (self.outputs or []) if obj.type == "IMAS"]
        return ImasDataCollection(inputs=inputs, outputs=outputs)

    @pydantic.field_validator("ids", mode="before")
    @classmethod
    def parse_ids_string(cls, value):
        """Parse ids field from string representation to list.

        API returns ids as string like '[core_profiles, equilibrium]'.
        Convert to proper list of strings.
        """
        if isinstance(value, str):
            # Remove brackets and split by comma
            value = value.strip("[]")
            if value:
                return [s.strip() for s in value.split(",")]
            return None
        return value

    @pydantic.field_validator("uuid", mode="before")
    @classmethod
    def parse_uuid(cls, value):
        """Parse UUID from API format.

        API returns uuid as {"_type": "uuid.UUID", "hex": "..."}.
        Extract the hex string.
        """
        if isinstance(value, dict) and "hex" in value:
            return value["hex"]
        return value

    @pydantic.model_validator(mode="before")
    @classmethod
    def transform_api_response(cls, data):
        """Transform SimDB REST API response to model format.

        Handles the metadata array structure from API and flattens it.
        API format:
            {"uuid": {...}, "alias": "...", "metadata": [{"element": "field", "value": "val"}, ...]}

        Transforms to flat structure with metadata fields unpacked and structured.
        """
        if not isinstance(data, dict):
            return data

        # If no metadata array, pass through (already transformed or direct construction)
        if "metadata" not in data:
            return data

        # Start with copy of data
        transformed = {}

        # Copy non-metadata fields
        for key in ["uuid", "alias"]:
            if key in data:
                transformed[key] = data[key]

        # Parse metadata array into flat dict
        metadata_dict = {}
        for item in data["metadata"]:
            element = item.get("element", "")
            value = item.get("value")
            if element and value is not None:
                metadata_dict[element] = value

        # Copy datetime from top level if present
        if "datetime" in data:
            metadata_dict["datetime"] = data["datetime"]

        # Map well-known fields to model attributes
        if "machine" in metadata_dict:
            transformed["machine"] = metadata_dict["machine"]

        # Handle nested code info
        if "code.name" in metadata_dict:
            code_info = {"name": metadata_dict["code.name"]}
            if "code.version" in metadata_dict:
                code_info["version"] = metadata_dict["code.version"]
            transformed["code"] = code_info

        # Map simple optional fields
        for field in ["status", "description", "uploaded_by", "ids"]:
            if field in metadata_dict:
                transformed[field] = metadata_dict[field]

        # Parse structured metadata
        transformed["metadata"] = SimulationMetadata.from_metadata_dict(metadata_dict)

        # Parse inputs/outputs if present (from per-simulation endpoint)
        if "inputs" in data:
            transformed["inputs"] = data["inputs"]

        if "outputs" in data:
            transformed["outputs"] = data["outputs"]

        # Set defaults for required fields if missing
        if "machine" not in transformed:
            transformed["machine"] = ""
        if "code" not in transformed:
            transformed["code"] = {"name": ""}
        if "description" not in transformed:
            transformed["description"] = ""
        if "status" not in transformed:
            transformed["status"] = "pending"

        return transformed

    @classmethod
    def from_api_response(cls, data: dict) -> "Simulation":
        """Create Simulation from SimDB REST API JSON response.

        Handles API field mapping and nested structures. The API returns:
        - uuid as {"_type": "uuid.UUID", "hex": "..."}
        - metadata as array: [{"element": "field", "value": "val"}, ...]

        Transforms this into the Simulation model schema using Pydantic validators.

        Args:
            data: JSON dict from SimDB REST API

        Returns:
            Simulation instance with validated fields

        Examples:
            >>> api_json = {
            ...     "uuid": {"_type": "uuid.UUID", "hex": "abc123"},
            ...     "alias": "100001/2",
            ...     "metadata": [
            ...         {"element": "machine", "value": "ITER"},
            ...         {"element": "code.name", "value": "METIS"}
            ...     ]
            ... }
            >>> sim = Simulation.from_api_response(api_json)
            >>> print(sim.alias)
            100001/2
        """
        # Let Pydantic validators handle transformation
        return cls.model_validate(data)


QueryOperator = Literal["eq", "in", "gt", "ge", "lt", "le", "agt", "age", "alt", "ale"]


class QueryConstraint(pydantic.BaseModel):
    """SimDB query constraint with operator.

    Attributes:
        field: Metadata field to query (e.g., 'machine', 'code.name', 'status')
        operator: Comparison operator
        value: Value to compare against

    Operators:
        eq: Exact match (default)
        in: Contains (case-insensitive substring)
        gt, ge, lt, le: Numeric comparisons
        agt, age, alt, ale: Array element comparisons

    Examples:
        >>> constraint = QueryConstraint(field="machine", operator="eq", value="ITER")
        >>> print(f"{constraint.field}={constraint.operator}:{constraint.value}")
        machine=eq:ITER

        >>> constraint = QueryConstraint(field="code.name", operator="in", value="METIS")
        >>> print(f"{constraint.field}={constraint.operator}:{constraint.value}")
        code.name=in:METIS
    """

    field: str
    operator: QueryOperator = "eq"
    value: str | float | int
