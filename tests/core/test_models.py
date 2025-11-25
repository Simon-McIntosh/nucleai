"""Tests for core.models module."""

import pytest
from pydantic import ValidationError as PydanticValidationError

from nucleai.core.models import SearchResult
from nucleai.simdb.models import CodeInfo, QueryConstraint, Simulation


def test_code_info_creation():
    """Test CodeInfo model creation."""
    code = CodeInfo(name="METIS", version="1.0.0")
    assert code.name == "METIS"
    assert code.version == "1.0.0"


def test_code_info_model_dump():
    """Test CodeInfo model serialization."""
    code = CodeInfo(name="METIS", version="1.0.0")
    data = code.model_dump()
    assert data == {"name": "METIS", "version": "1.0.0"}


def test_simulation_creation(sample_simulation_data):
    """Test Simulation model creation."""
    sim = Simulation(
        uuid=sample_simulation_data["uuid"],
        alias=sample_simulation_data["alias"],
        machine=sample_simulation_data["machine"],
        code=CodeInfo(
            name=sample_simulation_data["code_name"],
            version=sample_simulation_data["code_version"],
        ),
        description=sample_simulation_data["description"],
        status="passed",
    )
    assert sim.uuid == sample_simulation_data["uuid"]
    assert sim.alias == sample_simulation_data["alias"]
    assert sim.code.name == sample_simulation_data["code_name"]


def test_simulation_status_validation():
    """Test Simulation status field validation."""
    with pytest.raises(PydanticValidationError):
        Simulation(
            uuid="123",
            alias="test",
            machine="ITER",
            code=CodeInfo(name="METIS", version="1.0"),
            description="test",
            status="invalid_status",
        )


def test_query_constraint_default_operator():
    """Test QueryConstraint default operator."""
    constraint = QueryConstraint(field="machine", value="ITER")
    assert constraint.operator == "eq"


def test_query_constraint_with_operator():
    """Test QueryConstraint with explicit operator."""
    constraint = QueryConstraint(field="code.name", operator="in", value="METIS")
    assert constraint.field == "code.name"
    assert constraint.operator == "in"
    assert constraint.value == "METIS"


def test_search_result_creation():
    """Test SearchResult model creation."""
    result = SearchResult(
        id="sim-001", content="Test simulation", similarity=0.92, metadata={"machine": "ITER"}
    )
    assert result.id == "sim-001"
    assert result.similarity == 0.92
    assert result.metadata["machine"] == "ITER"


def test_search_result_default_metadata():
    """Test SearchResult with default empty metadata."""
    result = SearchResult(id="sim-001", content="Test", similarity=0.5)
    assert result.metadata == {}


def test_simulation_json_schema():
    """Test Simulation JSON schema generation."""
    schema = Simulation.model_json_schema()
    assert "properties" in schema
    assert "uuid" in schema["properties"]
    assert "alias" in schema["properties"]
    assert "machine" in schema["properties"]
