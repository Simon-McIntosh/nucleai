"""Pydantic data models for nucleai.

This module defines all core data structures using Pydantic for validation
and JSON schema generation. These models enable AI agents to understand data
formats through `help()` and `.model_json_schema()`.

Classes:
    CodeInfo: Simulation code metadata
    Simulation: ITER SimDB simulation record
    QueryConstraint: SimDB query constraint with operator
    SearchResult: Search result with similarity score
    FeatureMetadata: Feature extraction metadata

Examples:
    >>> from nucleai.core.models import Simulation
    >>> help(Simulation)
    >>> print(Simulation.model_json_schema())
    >>> sim = Simulation(
    ...     uuid="123e4567-e89b-12d3-a456-426614174000",
    ...     alias="ITER-001",
    ...     machine="ITER",
    ...     code=CodeInfo(name="METIS", version="1.0.0"),
    ...     description="Baseline scenario",
    ...     status="passed"
    ... )
"""

from typing import Literal

import pydantic


class CodeInfo(pydantic.BaseModel):
    """Simulation code information.

    Attributes:
        name: Code name (e.g., METIS, JETTO, ASTRA)
        version: Code version string (e.g., "1.2.3")

    Examples:
        >>> code = CodeInfo(name="METIS", version="1.0.0")
        >>> print(code.name)
        METIS
        >>> print(code.model_dump())
        {'name': 'METIS', 'version': '1.0.0'}
    """

    name: str
    version: str


class Simulation(pydantic.BaseModel):
    """ITER SimDB simulation metadata.

    Attributes:
        uuid: Unique simulation identifier (UUID format)
        alias: Human-readable alias (e.g., "ITER-001")
        machine: Machine name (e.g., "ITER")
        code: Simulation code information
        description: Detailed simulation description
        status: Validation status (passed, failed, pending)

    Examples:
        >>> from nucleai.core.models import CodeInfo, Simulation
        >>> sim = Simulation(
        ...     uuid="123e4567-e89b-12d3-a456-426614174000",
        ...     alias="ITER-001",
        ...     machine="ITER",
        ...     code=CodeInfo(name="METIS", version="1.0.0"),
        ...     description="Baseline ITER scenario with 15MA plasma current",
        ...     status="passed"
        ... )
        >>> print(sim.alias)
        ITER-001
        >>> print(sim.code.name)
        METIS
    """

    uuid: str
    alias: str
    machine: str
    code: CodeInfo
    description: str
    status: Literal["passed", "failed", "pending"]


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
