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
from pydantic import Field

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


class SimulationSummary(pydantic.BaseModel):
    """Lightweight simulation from query() - for search and filtering.

    Contains core metadata without file lists or IMAS URI. Optimized for
    fast queries over large result sets. Use fetch_simulation() to get
    complete Simulation with file data and IMAS access.

    All fields are automatically populated by query() and list_simulations().
    Model schema = API contract: if a field is defined here, it's always fetched.

    Returned by:
        - query(): Search simulations with filters
        - list_simulations(): List recent simulations

    Attributes:
        uuid: Unique simulation identifier (UUID format)
        alias: Human-readable simulation identifier (e.g., "100001/2" or "koechlf/jetto/iter/53298/oct1118/seq-1")
        machine: Tokamak device name (e.g., "ITER", "JET")
        code: Simulation code information
        description: Detailed simulation description
        status: Validation status (passed, failed, pending)
        author_email: Email address(es) of uploader (e.g., 'Xavier.Bonnin@iter.org'). Use to filter simulations by user.
        ids_types: Available IDS data types (e.g., ['core_profiles', 'equilibrium']). Check this to see what physics data exists.
        metadata: Structured metadata (datetime, composition, etc.)

    Examples:
        >>> from nucleai.simdb import query, fetch_simulation
        >>>
        >>> # Query returns summaries (fast, lightweight)
        >>> summaries = await query({'machine': 'ITER'}, limit=100)
        >>> summary = summaries[0]
        >>>
        >>> # Access metadata
        >>> print(summary.alias, summary.code.name)
        >>> print(summary.author)
        >>> print(summary.metadata.datetime)
        >>>
        >>> # Find user's simulations by email
        >>> all_sims = await query(filters=None, limit=200)
        >>> user_sims = [s for s in all_sims if s.author_email and 'Florian.Koechl' in s.author_email]
        >>> for sim in user_sims[:5]:
        ...     print(f"{sim.alias}: {sim.code.name} ({sim.metadata.datetime})")
        >>>
        >>> # Get complete simulation with IMAS URI
        >>> if user_sims:
        ...     complete = await fetch_simulation(user_sims[0].uuid)
        ...     print(f"IMAS URI: {complete.imas_uri}")
    """

    uuid: str = pydantic.Field(description="Unique simulation identifier (UUID format)")
    alias: str = pydantic.Field(
        description="Human-readable simulation identifier (e.g., '100001/2' or 'koechlf/jetto/iter/53298/oct1118/seq-1')"
    )
    machine: str = pydantic.Field(description="Tokamak device name (e.g., 'ITER', 'JET')")
    code: CodeInfo = pydantic.Field(description="Simulation code information (name, version)")
    description: str = pydantic.Field(description="Detailed simulation description")
    status: Literal["passed", "failed", "pending"] = pydantic.Field(
        description="Validation status of simulation"
    )
    author_email: str | None = Field(
        None,
        description="Email address of person who uploaded simulation (e.g., 'Xavier.Bonnin@iter.org'). May be comma-separated for multiple authors. Use to filter simulations by user.",
    )
    ids_types: list[str] | None = pydantic.Field(
        None,
        description="Available IDS data types (e.g., ['core_profiles', 'equilibrium']). Check this to see what physics data exists.",
    )
    metadata: SimulationMetadata | None = pydantic.Field(
        None, description="Structured metadata (datetime, composition, etc.)"
    )

    @pydantic.field_validator("ids_types", mode="before")
    @classmethod
    def parse_ids_string(cls, value):
        """Parse ids_types field from string representation to list.

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

        # Map simple optional fields (API field name → model field name)
        field_mapping = {
            "status": "status",
            "description": "description",
            "uploaded_by": "author_email",  # API returns 'uploaded_by', we expose as 'author_email'
            "ids": "ids_types",  # API returns 'ids', we expose as 'ids_types' for clarity
        }
        for api_field, model_field in field_mapping.items():
            if api_field in metadata_dict:
                transformed[model_field] = metadata_dict[api_field]

        # Parse structured metadata
        transformed["metadata"] = SimulationMetadata.from_metadata_dict(metadata_dict)

        # Preserve inputs/outputs if present (for Simulation subclass)
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
    def from_api_response(cls, data: dict) -> "SimulationSummary":
        """Create SimulationSummary from SimDB REST API JSON response.

        Handles API field mapping and nested structures. The API returns:
        - uuid as {"_type": "uuid.UUID", "hex": "..."}
        - metadata as array: [{"element": "field", "value": "val"}, ...]

        Transforms this into the SimulationSummary model schema using Pydantic validators.

        Args:
            data: JSON dict from SimDB REST API

        Returns:
            SimulationSummary instance with validated fields

        Examples:
            >>> api_json = {
            ...     "uuid": {"_type": "uuid.UUID", "hex": "abc123"},
            ...     "alias": "100001/2",
            ...     "metadata": [
            ...         {"element": "machine", "value": "ITER"},
            ...         {"element": "code.name", "value": "METIS"}
            ...     ]
            ... }
            >>> sim = SimulationSummary.from_api_response(api_json)
            >>> print(sim.alias)
            100001/2
        """
        # Let Pydantic validators handle transformation
        return cls.model_validate(data)


class Simulation(SimulationSummary):
    """Complete simulation from fetch_simulation() - full details with files.

    Extends SimulationSummary with file data and IMAS URI. All file-related
    fields are guaranteed present (never None). Use for accessing IDS data,
    verifying checksums, or downloading simulation artifacts.

    Returned by:
        - fetch_simulation(): Get complete details by UUID/alias

    Attributes (in addition to SimulationSummary):
        imas_uri: Primary IMAS data URI (empty string if no IMAS data exists)
        inputs: All input data objects (FILE + IMAS) with checksums and timestamps
        outputs: All output data objects (FILE + IMAS) with checksums and timestamps

    Data Access Patterns:
        1. Simple IMAS access (most common):
            >>> sim.imas_uri  # Direct URI string
            'imas://uda.iter.org/uda?path=/work/imas/...&backend=hdf5'
            >>>
            >>> # Use with imas-python
            >>> import imas
            >>> with imas.DBEntry(sim.imas_uri, "r") as entry:
            ...     equilibrium = entry.get("equilibrium")

        2. Rich IMAS access (parsed structure):
            >>> sim.imas.uri.backend  # 'hdf5'
            >>> sim.imas.uri.server   # 'uda.iter.org'
            >>> sim.imas.uri.path     # File system path
            >>> sim.imas.outputs      # List of all IMAS URIs

        3. Complete file access (all simulation artifacts):
            >>> for obj in sim.outputs:
            ...     print(f"{obj.type}: {obj.uri}")
            ...     print(f"  Checksum: {obj.checksum}")
            ...     print(f"  Uploaded: {obj.datetime}")
            FILE: file://.../jetto.in
            FILE: file://.../jetto.out
            IMAS: imas://uda.iter.org/uda?path=...

    Examples:
        >>> from nucleai.simdb import query, fetch_simulation
        >>>
        >>> # Step 1: Fast search (returns summaries)
        >>> summaries = await query({'code.name': 'in:JINTRAC'}, limit=100)
        >>> latest = max(summaries, key=lambda s: s.metadata.datetime or '')
        >>>
        >>> # Step 2: Get complete details
        >>> sim = await fetch_simulation(latest.uuid)
        >>>
        >>> # Now access IMAS data
        >>> if sim.imas_uri:
        ...     import imas
        ...     with imas.DBEntry(sim.imas_uri, "r") as entry:
        ...         core_profiles = entry.get("core_profiles")
        >>>
        >>> # Access all files
        >>> print(f"Total outputs: {len(sim.outputs)}")
        >>> files = [o for o in sim.outputs if o.type == 'FILE']
        >>> print(f"Simulation artifact files: {len(files)}")
    """

    imas_uri: str = ""
    inputs: list[DataObject] = []
    outputs: list[DataObject] = []

    @pydantic.model_validator(mode="after")
    def extract_imas_uri(self) -> "Simulation":
        """Extract primary IMAS URI from outputs for schema visibility.

        Extracts the first IMAS URI from outputs list and stores in imas_uri field.
        This provides direct access while preserving complete outputs list.
        """
        if not self.imas_uri and self.outputs:
            for obj in self.outputs:
                if obj.type == "IMAS":
                    self.imas_uri = obj.uri
                    break
        return self

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
