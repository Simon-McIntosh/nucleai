"""Pydantic data models for nucleai.

This module defines all core data structures using Pydantic for validation
and JSON schema generation. These models enable AI agents to understand data
formats through `help()` and `.model_json_schema()`.

Classes:
    CodeInfo: Simulation code metadata
    Simulation: ITER SimDB simulation metadata (basic from query, extended from info)
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
    >>> # Extended simulation from info (optional fields populated)
    >>> detail = Simulation(
    ...     uuid="123...",
    ...     alias="ITER-001",
    ...     machine="ITER",
    ...     code=CodeInfo(name="METIS", version="1.0"),
    ...     description="Baseline",
    ...     status="passed",
    ...     uploaded_by="user@iter.org",
    ...     global_quantities={"ip": -15e6, "beta_tor_norm": 0.26}
    ... )
"""

from typing import Literal

import pydantic


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
    """ITER SimDB simulation metadata.

    Single model for both query results and detailed info. Basic fields
    (uuid, alias, machine, code, description, status) always present.
    Extended fields (uploaded_by, physics quantities) optional, populated
    from REST API /simulation/<id> endpoint.

    Attributes:
        uuid: Unique simulation identifier (UUID format)
        alias: Human-readable alias (e.g., "ITER-001" or "username/code/machine/...")
        machine: Machine name (e.g., "ITER")
        code: Simulation code information
        description: Detailed simulation description
        status: Validation status (passed, failed, pending)
        uploaded_by: Email address(es) of uploader (from API)
        ids: Available IDS types (from API, e.g., ['core_profiles', 'equilibrium'])
        time_begin: Simulation start time (from API)
        time_end: Simulation end time (from API)
        time_step: Time step size (from API)
        creation_date: IDS creation timestamp (from API)
        global_quantities: Physics quantities like ip, energy, beta (from API)
        composition: Plasma composition fractions (from API)
        heating: Heating and current drive powers (from API)

    Examples:
        >>> from nucleai.core.models import CodeInfo, Simulation
        >>> # Basic from query
        >>> sim = Simulation(
        ...     uuid="123e4567-e89b-12d3-a456-426614174000",
        ...     alias="ITER-001",
        ...     machine="ITER",
        ...     code=CodeInfo(name="METIS", version="1.0.0"),
        ...     description="Baseline ITER scenario",
        ...     status="passed"
        ... )
        >>>
        >>> # Extended from API response
        >>> detail = Simulation(
        ...     uuid="123...",
        ...     alias="ITER-001",
        ...     machine="ITER",
        ...     code=CodeInfo(name="METIS", version="1.0"),
        ...     description="Baseline",
        ...     status="passed",
        ...     uploaded_by="user@iter.org",
        ...     global_quantities={"ip": -15e6, "beta_tor_norm": 0.26}
        ... )
        >>> print(detail.global_quantities["ip"])
        -15000000.0
        >>>
        >>> # Parse from REST API JSON
        >>> api_data = {"uuid": "123", "alias": "ITER-001", ...}
        >>> sim = Simulation.from_api_response(api_data)
    """

    model_config = pydantic.ConfigDict(extra="allow")

    uuid: str
    alias: str
    machine: str
    code: CodeInfo
    description: str
    status: Literal["passed", "failed", "pending"]
    uploaded_by: str | None = None
    ids: list[str] | None = None
    time_begin: float | None = None
    time_end: float | None = None
    time_step: float | None = None
    creation_date: str | None = None
    global_quantities: dict[str, float | list[float]] = pydantic.Field(default_factory=dict)
    composition: dict[str, float] = pydantic.Field(default_factory=dict)
    heating: dict[str, float] = pydantic.Field(default_factory=dict)

    @classmethod
    def from_api_response(cls, data: dict) -> "Simulation":
        """Create Simulation from SimDB REST API JSON response.

        Handles API field mapping and nested structures. The API returns:
        - uuid as {"_type": "uuid.UUID", "hex": "..."}
        - metadata as array: [{"element": "field", "value": "val"}, ...]

        Transforms this into the Simulation model schema.

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
        # Transform API format to model format
        transformed = {}

        # Handle UUID
        if "uuid" in data:
            if isinstance(data["uuid"], dict) and "hex" in data["uuid"]:
                transformed["uuid"] = data["uuid"]["hex"]
            else:
                transformed["uuid"] = data["uuid"]

        # Copy simple fields
        if "alias" in data:
            transformed["alias"] = data["alias"]
        if "datetime" in data:
            transformed["datetime"] = data["datetime"]

        # Parse metadata array into flat structure
        if "metadata" in data:
            metadata_dict = {}
            for item in data["metadata"]:
                element = item.get("element", "")
                value = item.get("value")
                if element and value is not None:
                    metadata_dict[element] = value

            # Map common metadata fields
            if "machine" in metadata_dict:
                transformed["machine"] = metadata_dict["machine"]

            if "code.name" in metadata_dict:
                code_info = {"name": metadata_dict["code.name"]}
                if "code.version" in metadata_dict:
                    code_info["version"] = metadata_dict["code.version"]
                if "code.commit" in metadata_dict:
                    code_info["commit"] = metadata_dict["code.commit"]
                if "code.repository" in metadata_dict:
                    code_info["repository"] = metadata_dict["code.repository"]
                transformed["code"] = code_info

            if "status" in metadata_dict:
                transformed["status"] = metadata_dict["status"]
            if "description" in metadata_dict:
                transformed["description"] = metadata_dict["description"]
            if "uploaded_by" in metadata_dict:
                transformed["uploaded_by"] = metadata_dict["uploaded_by"]

            # Store remaining metadata as extra fields
            for key, value in metadata_dict.items():
                if key not in [
                    "machine",
                    "code.name",
                    "code.version",
                    "code.commit",
                    "code.repository",
                    "status",
                    "description",
                    "uploaded_by",
                ]:
                    transformed[key] = value

        # Set defaults for required fields if missing
        if "machine" not in transformed:
            transformed["machine"] = ""
        if "code" not in transformed:
            transformed["code"] = {"name": ""}
        if "description" not in transformed:
            transformed["description"] = ""
        if "status" not in transformed:
            transformed["status"] = "pending"  # Use valid literal value

        return cls.model_validate(transformed)


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
