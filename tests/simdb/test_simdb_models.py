"""Unit tests for SimDB models.

Tests for ImasUri parsing, ImasDataCollection, and Simulation model validation.
"""

from nucleai.simdb.models import (
    CodeInfo,
    DataObject,
    ImasDataCollection,
    ImasUri,
    Simulation,
)


class TestImasUri:
    """Tests for ImasUri parsing and properties."""

    def test_parse_remote_uri(self):
        """Test parsing remote UDA URI."""
        uri_str = "imas://uda.iter.org:56565/uda?path=/work/imas/shared/imasdb/ITER/3/100001/2&backend=hdf5"
        uri = ImasUri.parse(uri_str)

        assert uri.raw == uri_str
        assert uri.backend == "hdf5"
        assert uri.is_remote is True
        assert uri.server == "uda.iter.org"
        assert uri.port == 56565
        assert uri.path == "/work/imas/shared/imasdb/ITER/3/100001/2"
        assert uri.shot is None
        assert uri.run is None

    def test_parse_remote_uri_no_port(self):
        """Test parsing remote URI without explicit port."""
        uri_str = (
            "imas://uda.iter.org/uda?path=/work/imas/shared/imasdb/ITER/3/100001/2&backend=hdf5"
        )
        uri = ImasUri.parse(uri_str)

        assert uri.backend == "hdf5"
        assert uri.is_remote is True
        assert uri.server == "uda.iter.org"
        assert uri.port is None
        assert uri.path == "/work/imas/shared/imasdb/ITER/3/100001/2"

    def test_parse_local_uri(self):
        """Test parsing local file path URI."""
        uri_str = "imas:hdf5?path=/work/imas/shared/imasdb/test"
        uri = ImasUri.parse(uri_str)

        assert uri.raw == uri_str
        assert uri.backend == "hdf5"
        assert uri.is_remote is False
        assert uri.server is None
        assert uri.port is None
        assert uri.path == "/work/imas/shared/imasdb/test"

    def test_parse_legacy_uri(self):
        """Test parsing legacy format URI."""
        uri_str = "imas:?shot=100001&run=2&user=public&database=ITER&version=3&backend=hdf5"
        uri = ImasUri.parse(uri_str)

        assert uri.raw == uri_str
        assert uri.backend == "hdf5"
        assert uri.is_remote is False
        assert uri.shot == 100001
        assert uri.run == 2
        assert uri.user == "public"
        assert uri.database == "ITER"
        assert uri.version == "3"
        assert uri.path is None

    def test_parse_legacy_uri_numeric_conversion(self):
        """Test that shot and run are converted to integers."""
        uri_str = "imas:?shot=12345&run=67&backend=hdf5"
        uri = ImasUri.parse(uri_str)

        assert uri.shot == 12345
        assert uri.run == 67
        assert isinstance(uri.shot, int)
        assert isinstance(uri.run, int)

    def test_parse_mdsplus_backend(self):
        """Test parsing URI with mdsplus backend."""
        uri_str = "imas:mdsplus?path=/work/imas/data"
        uri = ImasUri.parse(uri_str)

        assert uri.backend == "mdsplus"
        assert uri.is_remote is False

    def test_str_returns_raw_uri(self):
        """Test that str() returns the raw URI string."""
        uri_str = (
            "imas://uda.iter.org/uda?path=/work/imas/shared/imasdb/ITER/3/100001/2&backend=hdf5"
        )
        uri = ImasUri.parse(uri_str)

        assert str(uri) == uri_str

    def test_parse_uri_with_missing_backend(self):
        """Test parsing URI when backend is not in query params."""
        uri_str = "imas:hdf5?path=/work/imas/data"
        uri = ImasUri.parse(uri_str)

        assert uri.backend == "hdf5"


class TestImasDataCollection:
    """Tests for ImasDataCollection functionality."""

    def test_empty_collection(self):
        """Test empty IMAS data collection."""
        collection = ImasDataCollection()

        assert collection.inputs == []
        assert collection.outputs == []
        assert collection.uri is None
        assert not collection  # __bool__ returns False

    def test_collection_with_output(self):
        """Test collection with one output URI."""
        uri = ImasUri.parse(
            "imas://uda.iter.org/uda?path=/work/imas/shared/imasdb/ITER/3/100001/2&backend=hdf5"
        )
        collection = ImasDataCollection(outputs=[uri])

        assert len(collection.outputs) == 1
        assert len(collection.inputs) == 0
        assert collection.uri == uri
        assert collection  # __bool__ returns True

    def test_collection_with_input(self):
        """Test collection with one input URI."""
        uri = ImasUri.parse("imas:hdf5?path=/work/imas/input")
        collection = ImasDataCollection(inputs=[uri])

        assert len(collection.inputs) == 1
        assert len(collection.outputs) == 0
        assert collection.uri == uri  # Falls back to input
        assert collection

    def test_uri_property_prefers_output(self):
        """Test that uri property prefers output over input."""
        input_uri = ImasUri.parse("imas:hdf5?path=/work/imas/input")
        output_uri = ImasUri.parse("imas:hdf5?path=/work/imas/output")
        collection = ImasDataCollection(inputs=[input_uri], outputs=[output_uri])

        assert collection.uri == output_uri

    def test_collection_with_multiple_outputs(self):
        """Test collection with multiple output URIs."""
        uri1 = ImasUri.parse("imas:hdf5?path=/work/imas/output1")
        uri2 = ImasUri.parse("imas:hdf5?path=/work/imas/output2")
        collection = ImasDataCollection(outputs=[uri1, uri2])

        assert len(collection.outputs) == 2
        assert collection.uri == uri1  # Returns first output

    def test_bool_with_outputs(self):
        """Test __bool__ returns True when outputs exist."""
        uri = ImasUri.parse("imas:hdf5?path=/work/imas/output")
        collection = ImasDataCollection(outputs=[uri])

        assert bool(collection) is True

    def test_bool_with_inputs(self):
        """Test __bool__ returns True when inputs exist."""
        uri = ImasUri.parse("imas:hdf5?path=/work/imas/input")
        collection = ImasDataCollection(inputs=[uri])

        assert bool(collection) is True

    def test_bool_empty(self):
        """Test __bool__ returns False when no URIs exist."""
        collection = ImasDataCollection()

        assert bool(collection) is False


class TestSimulationImasProperty:
    """Tests for Simulation.imas property."""

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

        assert not sim.imas
        assert sim.imas.uri is None
        assert len(sim.imas.outputs) == 0
        assert len(sim.imas.inputs) == 0

    def test_simulation_with_imas_output(self):
        """Test simulation with IMAS output."""
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
                    uri="imas://uda.iter.org/uda?path=/work/imas/shared/imasdb/ITER/3/100001/2&backend=hdf5",
                    type="IMAS",
                )
            ],
        )

        assert sim.imas
        assert sim.imas.uri is not None
        assert len(sim.imas.outputs) == 1
        assert sim.imas.uri.backend == "hdf5"
        assert sim.imas.uri.is_remote is True

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

        assert not sim.imas  # No IMAS data
        assert sim.imas.uri is None

    def test_simulation_with_mixed_outputs(self):
        """Test simulation with both IMAS and file outputs."""
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
                    uri="imas:hdf5?path=/work/imas/data",
                    type="IMAS",
                ),
            ],
        )

        assert sim.imas
        assert len(sim.imas.outputs) == 1
        assert sim.imas.uri.backend == "hdf5"

    def test_simulation_with_multiple_imas_outputs(self):
        """Test simulation with multiple IMAS outputs."""
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

        assert sim.imas
        assert len(sim.imas.outputs) == 2
        assert sim.imas.uri.path == "/work/imas/output1"  # First output

    def test_simulation_with_imas_input(self):
        """Test simulation with IMAS input."""
        sim = Simulation(
            uuid="123e4567-e89b-12d3-a456-426614174000",
            alias="test/1",
            machine="ITER",
            code=CodeInfo(name="TEST", version="1.0"),
            description="Test simulation",
            status="passed",
            inputs=[
                DataObject(
                    uuid="imas-1",
                    uri="imas:hdf5?path=/work/imas/input",
                    type="IMAS",
                )
            ],
        )

        assert sim.imas
        assert len(sim.imas.inputs) == 1
        assert sim.imas.uri.path == "/work/imas/input"

    def test_imas_uri_str_for_dbentry(self):
        """Test that str(sim.imas.uri) works for imas.DBEntry()."""
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

        assert str(sim.imas.uri) == uri_str


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

    def test_transform_api_response_non_dict(self):
        """Test that non-dict data passes through unchanged (line 390)."""
        # Test string pass-through
        result = Simulation.transform_api_response("not a dict")
        assert result == "not a dict"

        # Test None pass-through
        result = Simulation.transform_api_response(None)
        assert result is None

    def test_transform_api_response_with_datetime(self):
        """Test datetime field is copied to metadata_dict (line 414)."""
        api_data = {
            "uuid": {"_type": "uuid.UUID", "hex": "test123"},
            "alias": "test/1",
            "datetime": "2025-08-11T13:46:25.682813",
            "metadata": [
                {"element": "machine", "value": "ITER"},
                {"element": "code.name", "value": "METIS"},
            ],
        }

        sim = Simulation.from_api_response(api_data)

        # Datetime should be in metadata
        assert sim.metadata.datetime == "2025-08-11T13:46:25.682813"

    def test_transform_api_response_with_inputs_only(self):
        """Test inputs field is preserved (line 437)."""
        api_data = {
            "uuid": {"_type": "uuid.UUID", "hex": "test123"},
            "alias": "test/1",
            "metadata": [
                {"element": "machine", "value": "ITER"},
                {"element": "code.name", "value": "METIS"},
            ],
            "inputs": [
                {
                    "uuid": {"_type": "uuid.UUID", "hex": "input123"},
                    "uri": "imas:iter/3/12345/1",
                    "type": "IMAS",
                }
            ],
        }

        sim = Simulation.from_api_response(api_data)

        assert sim.inputs is not None
        assert len(sim.inputs) == 1
        assert sim.inputs[0].type == "IMAS"
