"""Pydantic models for SimDB data structures.

This module defines data models for ITER SimDB simulations using Pydantic
for validation and JSON schema generation.

Note: Import Simulation from nucleai.simdb.models, not nucleai.core.models.

Classes:
    CodeInfo: Simulation code metadata
    Simulation: SimDB simulation record with metadata
    QueryConstraint: SimDB query constraint with operator

Examples:
    >>> from nucleai.simdb.models import Simulation, CodeInfo
    >>> # Discover available fields
    >>> print(Simulation.model_json_schema()['properties'].keys())
    >>>
    >>> # Basic simulation from query
    >>> sim = Simulation(
    ...     uuid="123e4567-e89b-12d3-a456-426614174000",
    ...     alias="100001/2",
    ...     machine="ITER",
    ...     code=CodeInfo(name="METIS", version="6.1894"),
    ...     description="Baseline ITER scenario",
    ...     status="passed"
    ... )
"""

from typing import Literal

import pydantic

from nucleai.simdb.metadata import SimulationMetadata


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
