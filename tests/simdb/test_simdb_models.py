"""Unit tests for SimDB models.

Tests for Simulation model validation and data object handling.
"""

from nucleai.core.models import ImasUri
from nucleai.simdb.models import (
    CodeInfo,
    DataObject,
    Simulation,
)


class TestSimulationImasUri:
    """Tests for Simulation.imas_uri field."""

    def test_simulation_without_imas_data(self):
        """Test simulation with no IMAS inputs or outputs."""
        sim = Simulation(
            uuid="123e4567-e89b-12d3-a456-426614174000",
            alias="test/1",
            machine="ITER",
            code=CodeInfo(name="TEST", version="1.0"),
            description="Test simulation",
            status="passed",
        )

        assert sim.imas_uri is None

    def test_simulation_with_imas_output(self):
        """Test simulation with IMAS output - auto-extracted to imas_uri."""
        uri_str = (
            "imas://uda.iter.org/uda?path=/work/imas/shared/imasdb/ITER/3/100001/2&backend=hdf5"
        )
        sim = Simulation(
            uuid="123e4567-e89b-12d3-a456-426614174000",
            alias="100001/2",
            machine="ITER",
            code=CodeInfo(name="METIS", version="1.0"),
            description="Test simulation",
            status="passed",
            outputs=[
                DataObject(
                    uuid="output-1",
                    uri=uri_str,
                    type="IMAS",
                )
            ],
        )

        assert sim.imas_uri is not None
        assert sim.imas_uri.backend == "hdf5"
        assert sim.imas_uri.is_remote is True
        assert sim.imas_uri.original == uri_str  # Check original, not optimized str()

    def test_simulation_with_file_output(self):
        """Test simulation with non-IMAS file output."""
        sim = Simulation(
            uuid="123e4567-e89b-12d3-a456-426614174000",
            alias="test/1",
            machine="ITER",
            code=CodeInfo(name="TEST", version="1.0"),
            description="Test simulation",
            status="passed",
            outputs=[DataObject(uuid="file-1", uri="file:///work/data/test.h5", type="FILE")],
        )

        assert sim.imas_uri is None

    def test_simulation_with_mixed_outputs(self):
        """Test simulation with both IMAS and file outputs."""
        uri_str = "imas:hdf5?path=/work/imas/data"
        sim = Simulation(
            uuid="123e4567-e89b-12d3-a456-426614174000",
            alias="test/1",
            machine="ITER",
            code=CodeInfo(name="TEST", version="1.0"),
            description="Test simulation",
            status="passed",
            outputs=[
                DataObject(uuid="file-1", uri="file:///work/data/test.h5", type="FILE"),
                DataObject(
                    uuid="imas-1",
                    uri=uri_str,
                    type="IMAS",
                ),
            ],
        )

        assert sim.imas_uri is not None
        assert sim.imas_uri.backend == "hdf5"
        assert str(sim.imas_uri) == uri_str

    def test_simulation_with_multiple_imas_outputs(self):
        """Test simulation with multiple IMAS outputs - first is used."""
        sim = Simulation(
            uuid="123e4567-e89b-12d3-a456-426614174000",
            alias="test/1",
            machine="ITER",
            code=CodeInfo(name="TEST", version="1.0"),
            description="Test simulation",
            status="passed",
            outputs=[
                DataObject(
                    uuid="imas-1",
                    uri="imas:hdf5?path=/work/imas/output1",
                    type="IMAS",
                ),
                DataObject(
                    uuid="imas-2",
                    uri="imas:hdf5?path=/work/imas/output2",
                    type="IMAS",
                ),
            ],
        )

        assert sim.imas_uri is not None
        assert sim.imas_uri.path == "/work/imas/output1"  # First output

    def test_imas_uri_str_for_dbentry(self):
        """Test that str(sim.imas_uri) returns optimal URI for imas.DBEntry()."""
        uri_str = (
            "imas://uda.iter.org/uda?path=/work/imas/shared/imasdb/ITER/3/100001/2&backend=hdf5"
        )
        sim = Simulation(
            uuid="123e4567-e89b-12d3-a456-426614174000",
            alias="100001/2",
            machine="ITER",
            code=CodeInfo(name="METIS", version="1.0"),
            description="Test simulation",
            status="passed",
            outputs=[DataObject(uuid="imas-1", uri=uri_str, type="IMAS")],
        )

        # str(uri) returns optimal (local if exists, original if not)
        # Check that original is preserved
        assert sim.imas_uri.original == uri_str

    def test_imas_uri_is_imasuri_object(self):
        """Test that imas_uri is an ImasUri object, not a string."""
        uri_str = "imas:hdf5?path=/work/imas/data"
        sim = Simulation(
            uuid="123e4567-e89b-12d3-a456-426614174000",
            alias="test/1",
            machine="ITER",
            code=CodeInfo(name="TEST", version="1.0"),
            description="Test simulation",
            status="passed",
            outputs=[DataObject(uuid="imas-1", uri=uri_str, type="IMAS")],
        )

        assert isinstance(sim.imas_uri, ImasUri)
        assert sim.imas_uri.backend == "hdf5"
        assert sim.imas_uri.path == "/work/imas/data"


class TestDataObject:
    """Tests for DataObject model."""

    def test_dataobject_with_imas_uri(self):
        """Test DataObject with IMAS URI."""
        obj = DataObject(
            uuid="abc123",
            uri="imas://uda.iter.org/uda?path=/work/imas/shared/imasdb/ITER/3/100001/2&backend=hdf5",
            type="IMAS",
        )

        assert obj.uuid == "abc123"
        assert obj.type == "IMAS"
        assert "imas://" in obj.uri

    def test_dataobject_with_file_uri(self):
        """Test DataObject with file URI."""
        obj = DataObject(uuid="file123", uri="file:///work/data/test.h5", type="FILE")

        assert obj.uuid == "file123"
        assert obj.type == "FILE"

    def test_dataobject_uuid_parsing(self):
        """Test DataObject parses UUID from dict format."""
        obj = DataObject(
            uuid={"_type": "uuid.UUID", "hex": "abc123"},
            uri="file:///work/data/test.h5",
            type="FILE",
        )

        assert obj.uuid == "abc123"


class TestCodeInfo:
    """Tests for CodeInfo model."""

    def test_codeinfo_with_version(self):
        """Test CodeInfo with version."""
        code = CodeInfo(name="METIS", version="6.1894")

        assert code.name == "METIS"
        assert code.version == "6.1894"

    def test_codeinfo_without_version(self):
        """Test CodeInfo without version."""
        code = CodeInfo(name="JINTRAC")

        assert code.name == "JINTRAC"
        assert code.version is None


class TestSimulationValidators:
    """Tests for Simulation model validators and transformations."""

    def test_parse_ids_string_with_brackets(self):
        """Test parsing ids_types field from string with brackets."""
        sim = Simulation(
            uuid="123e4567-e89b-12d3-a456-426614174000",
            alias="test/1",
            machine="ITER",
            code=CodeInfo(name="TEST"),
            description="Test",
            status="passed",
            ids_types="[core_profiles, equilibrium, summary]",
        )

        assert sim.ids_types == ["core_profiles", "equilibrium", "summary"]

    def test_parse_ids_string_without_brackets(self):
        """Test parsing ids_types field from string without brackets."""
        sim = Simulation(
            uuid="123e4567-e89b-12d3-a456-426614174000",
            alias="test/1",
            machine="ITER",
            code=CodeInfo(name="TEST"),
            description="Test",
            status="passed",
            ids_types="core_profiles, equilibrium",
        )

        assert sim.ids_types == ["core_profiles", "equilibrium"]

    def test_parse_ids_empty_string(self):
        """Test parsing empty ids_types string."""
        sim = Simulation(
            uuid="123e4567-e89b-12d3-a456-426614174000",
            alias="test/1",
            machine="ITER",
            code=CodeInfo(name="TEST"),
            description="Test",
            status="passed",
            ids_types="[]",
        )

        assert sim.ids_types is None

    def test_parse_ids_list(self):
        """Test that ids_types list is passed through unchanged."""
        sim = Simulation(
            uuid="123e4567-e89b-12d3-a456-426614174000",
            alias="test/1",
            machine="ITER",
            code=CodeInfo(name="TEST"),
            description="Test",
            status="passed",
            ids_types=["core_profiles", "equilibrium"],
        )

        assert sim.ids_types == ["core_profiles", "equilibrium"]

    def test_parse_uuid_from_dict(self):
        """Test parsing UUID from API dict format."""
        sim = Simulation(
            uuid={"_type": "uuid.UUID", "hex": "abc123def456"},
            alias="test/1",
            machine="ITER",
            code=CodeInfo(name="TEST"),
            description="Test",
            status="passed",
        )

        assert sim.uuid == "abc123def456"

    def test_parse_uuid_string(self):
        """Test that UUID string is passed through."""
        sim = Simulation(
            uuid="123e4567-e89b-12d3-a456-426614174000",
            alias="test/1",
            machine="ITER",
            code=CodeInfo(name="TEST"),
            description="Test",
            status="passed",
        )

        assert sim.uuid == "123e4567-e89b-12d3-a456-426614174000"

    def test_from_api_response(self):
        """Test creating Simulation from API response format."""
        api_data = {
            "uuid": {"_type": "uuid.UUID", "hex": "abc123"},
            "alias": "100001/2",
            "metadata": [
                {"element": "machine", "value": "ITER"},
                {"element": "code.name", "value": "METIS"},
                {"element": "code.version", "value": "6.1894"},
                {"element": "status", "value": "passed"},
                {"element": "description", "value": "Test simulation"},
                {"element": "ids", "value": "[core_profiles, equilibrium]"},
            ],
        }

        sim = Simulation.from_api_response(api_data)

        assert sim.uuid == "abc123"
        assert sim.alias == "100001/2"
        assert sim.machine == "ITER"
        assert sim.code.name == "METIS"
        assert sim.code.version == "6.1894"
        assert sim.status == "passed"
        assert sim.description == "Test simulation"
        assert sim.ids_types == ["core_profiles", "equilibrium"]

    def test_transform_api_response_with_outputs(self):
        """Test API response transformation with outputs."""
        api_data = {
            "uuid": {"_type": "uuid.UUID", "hex": "test123"},
            "alias": "test/1",
            "metadata": [
                {"element": "machine", "value": "ITER"},
                {"element": "code.name", "value": "TEST"},
                {"element": "status", "value": "passed"},
                {"element": "description", "value": "Test"},
            ],
            "outputs": [
                {
                    "uuid": {"hex": "output123"},
                    "uri": "imas:hdf5?path=/work/imas/data",
                    "type": "IMAS",
                }
            ],
        }

        sim = Simulation.from_api_response(api_data)

        assert sim.outputs is not None
        assert len(sim.outputs) == 1
        assert sim.outputs[0].type == "IMAS"

    def test_transform_api_response_defaults(self):
        """Test that missing required fields get defaults."""
        api_data = {
            "uuid": {"_type": "uuid.UUID", "hex": "test123"},
            "alias": "test/1",
            "metadata": [],  # Empty metadata
        }

        sim = Simulation.from_api_response(api_data)

        assert sim.machine == ""
        assert sim.code.name == ""
        assert sim.description == ""
        assert sim.status == "pending"
