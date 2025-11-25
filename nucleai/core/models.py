"""Pydantic data models for nucleai.

This module defines all core data structures using Pydantic for validation
and JSON schema generation. These models enable AI agents to understand data
formats through `help()` and `.model_json_schema()`.

Classes:
    CodeInfo: Simulation code metadata
    Simulation: ITER SimDB simulation metadata with structured metadata
    QueryConstraint: SimDB query constraint with operator
    SearchResult: Search result with similarity score
    FeatureMetadata: Feature extraction metadata

Examples:
    >>> from nucleai.core.models import Simulation
    >>> # Discover available fields
    >>> print(Simulation.model_json_schema()['properties'].keys())
    >>>
    >>> # Basic simulation from query
    >>> sim = Simulation(
    ...     uuid="123e4567-e89b-12d3-a456-426614174000",
    ...     alias="ITER-001",
    ...     machine="ITER",
    ...     code=CodeInfo(name="METIS", version="1.0.0"),
    ...     description="Baseline scenario",
    ...     status="passed"
    ... )
    >>>
    >>> # Extended simulation with metadata
    >>> detail = Simulation(
    ...     uuid="123...",
    ...     alias="ITER-001",
    ...     machine="ITER",
    ...     code=CodeInfo(name="METIS", version="1.0"),
    ...     description="Baseline",
    ...     status="passed",
    ...     uploaded_by="user@iter.org",
    ...     metadata=SimulationMetadata(
    ...         composition=CompositionMetadata(deuterium=0.00934)
    ...     )
    ... )
"""

from typing import Literal

import pydantic

from nucleai.core.metadata import SimulationMetadata


class CodeInfo(pydantic.BaseModel):
    """Simulation code information.

    Attributes:
        name: Code name (e.g., METIS, JETTO, ASTRA)
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
    """ITER SimDB simulation metadata with structured metadata.

    Single model for both query results and detailed info. Basic fields
    (uuid, alias, machine, code, description, status) always present.
    Extended fields (uploaded_by, metadata) optional, populated when
    requested via include_metadata parameter.

    Attributes:
        uuid: Unique simulation identifier (UUID format)
        alias: Human-readable alias (e.g., "ITER-001" or "100001/2")
        machine: Machine name (e.g., "ITER")
        code: Simulation code information
        description: Detailed simulation description
        status: Validation status (passed, failed, pending)
        uploaded_by: Email address(es) of uploader (must request via include_metadata)
        ids: Available IDS types (e.g., ['core_profiles', 'equilibrium'])
        metadata: Structured metadata (composition, ids_properties, etc.)

    Examples:
        >>> from nucleai.core.models import CodeInfo, Simulation
        >>> from nucleai.core.metadata import SimulationMetadata, CompositionMetadata
        >>>
        >>> # Basic from query (always present fields)
        >>> sim = Simulation(
        ...     uuid="123e4567-e89b-12d3-a456-426614174000",
        ...     alias="100001/2",
        ...     machine="ITER",
        ...     code=CodeInfo(name="METIS", version="6.1894"),
        ...     description="Baseline ITER scenario",
        ...     status="passed"
        ... )
        >>>
        >>> # With metadata (when requested)
        >>> detail = Simulation(
        ...     uuid="123...",
        ...     alias="100001/2",
        ...     machine="ITER",
        ...     code=CodeInfo(name="METIS", version="6.1894"),
        ...     description="Baseline",
        ...     status="passed",
        ...     uploaded_by="user@iter.org",
        ...     metadata=SimulationMetadata(
        ...         composition=CompositionMetadata(deuterium=0.00934, helium_4=0.02),
        ...         datetime="2025-08-11T13:46:25.682813"
        ...     )
        ... )
        >>> print(detail.metadata.composition.deuterium)  # Type-safe access!
        0.00934
        >>>
        >>> # Parse from REST API JSON
        >>> api_data = {"uuid": "123", "alias": "100001/2", "metadata": [...]}
        >>> sim = Simulation.from_api_response(api_data)
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
