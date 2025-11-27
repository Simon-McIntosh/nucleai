"""Pydantic models for SimDB data structures.

This module defines data models for ITER SimDB simulations using Pydantic
for validation and JSON schema generation.

Note: Import Simulation from nucleai.simdb.models, not nucleai.core.models.

Classes:
    DataObject: SimDB data object (file or IMAS data)
    CodeInfo: Simulation code metadata
    Simulation: SimDB simulation record with metadata
    QueryConstraint: SimDB query constraint with operator

Examples:
    >>> from nucleai.simdb import fetch_simulation
    >>>
    >>> # Get simulation with IMAS data
    >>> sim = await fetch_simulation("100001/2")
    >>> print(sim.alias, sim.machine, sim.code.name)
    >>>
    >>> # Access IMAS data (type-safe with ImasUri)
    >>> if sim.imas_uri:
    ...     print(f"Backend: {sim.imas_uri.backend}")
    ...     print(f"Remote: {sim.imas_uri.is_remote}")
    ...
    ...     # Use with IdsLoader
    ...     from nucleai.imas import IdsLoader
    ...     loader = IdsLoader.from_simulation(sim)
    ...     async with loader:
    ...         equilibrium = await loader.get("equilibrium", lazy=True)
"""

from typing import Literal

import pydantic
from pydantic import Field

from nucleai.core.models import ImasUri
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
        imas_uri: Primary IMAS URI as ImasUri object (None if no IMAS data)
        inputs: All input data objects (FILE + IMAS) with checksums and timestamps
        outputs: All output data objects (FILE + IMAS) with checksums and timestamps

    Data Access Patterns:
        1. Direct IDS loading (recommended):
            >>> from nucleai.imas import IdsLoader
            >>> loader = IdsLoader.from_simulation(sim)
            >>> async with loader:
            ...     equilibrium = await loader.get("equilibrium", lazy=True)

        2. Direct imas-python usage:
            >>> import imas
            >>> with imas.DBEntry(str(sim.imas_uri), "r") as entry:
            ...     equilibrium = entry.get("equilibrium")

        3. URI inspection:
            >>> if sim.imas_uri:
            ...     print(f"Backend: {sim.imas_uri.backend}")
            ...     print(f"Remote: {sim.imas_uri.is_remote}")
            ...     print(f"Path: {sim.imas_uri.path}")

        4. Complete file access (all simulation artifacts):
            >>> for obj in sim.outputs:
            ...     print(f"{obj.type}: {obj.uri}")
            ...     print(f"  Checksum: {obj.checksum}")
            ...     print(f"  Uploaded: {obj.datetime}")

    Examples:
        >>> from nucleai.simdb import query, fetch_simulation
        >>> from nucleai.imas import IdsLoader
        >>>
        >>> # Step 1: Fast search (returns summaries)
        >>> summaries = await query({'code.name': 'in:JINTRAC'}, limit=100)
        >>> latest = max(summaries, key=lambda s: s.metadata.datetime or '')
        >>>
        >>> # Step 2: Get complete details with type-safe IMAS URI
        >>> sim = await fetch_simulation(latest.uuid)
        >>>
        >>> # Step 3: Load IDS data with automatic optimization
        >>> if sim.imas_uri:
        ...     loader = IdsLoader.from_simulation(sim)
        ...     async with loader:
        ...         core_profiles = await loader.get("core_profiles", lazy=True)
        >>>
        >>> # Access all files
        >>> print(f"Total outputs: {len(sim.outputs)}")
        >>> files = [o for o in sim.outputs if o.type == 'FILE']
        >>> print(f"Simulation artifact files: {len(files)}")
    """

    imas_uri: ImasUri | None = None
    inputs: list[DataObject] = []
    outputs: list[DataObject] = []

    @pydantic.field_validator("imas_uri", mode="before")
    @classmethod
    def parse_imas_uri(cls, value):
        """Parse IMAS URI string to ImasUri object."""
        if value is None or isinstance(value, str) and not value:
            return None
        if isinstance(value, str):
            return ImasUri.from_string(value)
        return value

    @pydantic.model_validator(mode="after")
    def extract_imas_uri(self) -> "Simulation":
        """Extract primary IMAS URI from outputs for schema visibility.

        Extracts the first IMAS URI from outputs list and stores in imas_uri field.
        This provides direct access while preserving complete outputs list.
        """
        if not self.imas_uri and self.outputs:
            for obj in self.outputs:
                if obj.type == "IMAS":
                    self.imas_uri = ImasUri.from_string(obj.uri)
                    break
        return self

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
