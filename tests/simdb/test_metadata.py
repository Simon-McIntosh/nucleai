"""Tests for simdb.metadata module."""

from nucleai.simdb.metadata import (
    BoundaryMetadata,
    CodeMetadata,
    CompositionMetadata,
    GlobalQuantitiesMetadata,
    HeatingCurrentDriveMetadata,
    IDSPropertiesMetadata,
    SimulationMetadata,
)


class TestCompositionMetadata:
    """Tests for CompositionMetadata model."""

    def test_composition_creation_with_values(self):
        """Test creating composition metadata with values."""
        comp = CompositionMetadata(
            deuterium=0.00934,
            helium_4=0.02,
            argon=0.001,
        )
        assert comp.deuterium == 0.00934
        assert comp.helium_4 == 0.02
        assert comp.argon == 0.001

    def test_composition_all_fields_optional(self):
        """Test that all composition fields are optional."""
        comp = CompositionMetadata()
        assert comp.deuterium is None
        assert comp.helium_4 is None
        assert comp.hydrogen is None

    def test_composition_all_species(self):
        """Test all available species fields."""
        comp = CompositionMetadata(
            argon=0.001,
            beryllium=0.002,
            carbon=0.003,
            deuterium=0.004,
            deuterium_tritium=0.005,
            helium_3=0.006,
            helium_4=0.007,
            hydrogen=0.008,
            krypton=0.009,
            neon=0.010,
            nitrogen=0.011,
            oxygen=0.012,
            tritium=0.013,
            tungsten=0.014,
            xenon=0.015,
            z_effective=0.016,
        )
        assert comp.argon == 0.001
        assert comp.beryllium == 0.002
        assert comp.carbon == 0.003
        assert comp.deuterium == 0.004
        assert comp.deuterium_tritium == 0.005
        assert comp.helium_3 == 0.006
        assert comp.helium_4 == 0.007
        assert comp.hydrogen == 0.008
        assert comp.krypton == 0.009
        assert comp.neon == 0.010
        assert comp.nitrogen == 0.011
        assert comp.oxygen == 0.012
        assert comp.tritium == 0.013
        assert comp.tungsten == 0.014
        assert comp.xenon == 0.015
        assert comp.z_effective == 0.016


class TestIDSPropertiesMetadata:
    """Tests for IDSPropertiesMetadata model."""

    def test_ids_properties_creation(self):
        """Test creating IDS properties metadata."""
        ids_props = IDSPropertiesMetadata(
            creation_date="2021-05-04 09:25:46",
            homogeneous_time=1,
            comment="IMAS implementation of METIS",
        )
        assert ids_props.creation_date == "2021-05-04 09:25:46"
        assert ids_props.homogeneous_time == 1
        assert ids_props.comment == "IMAS implementation of METIS"

    def test_ids_properties_all_fields(self):
        """Test all IDS properties fields."""
        ids_props = IDSPropertiesMetadata(
            comment="Test comment",
            creation_date="2021-05-04 09:25:46",
            homogeneous_time=1,
            provider="test_provider",
            version_put_data_dictionary="3.39.0",
            version_put_access_layer="4.7.3",
            version_put_access_layer_language="python",
            provenance_node_reference_name="test_node",
        )
        assert ids_props.comment == "Test comment"
        assert ids_props.creation_date == "2021-05-04 09:25:46"
        assert ids_props.homogeneous_time == 1
        assert ids_props.provider == "test_provider"
        assert ids_props.version_put_data_dictionary == "3.39.0"
        assert ids_props.version_put_access_layer == "4.7.3"
        assert ids_props.version_put_access_layer_language == "python"
        assert ids_props.provenance_node_reference_name == "test_node"


class TestGlobalQuantitiesMetadata:
    """Tests for GlobalQuantitiesMetadata model."""

    def test_global_quantities_sources(self):
        """Test global quantities metadata with sources."""
        gq = GlobalQuantitiesMetadata(
            ip_source="equilibrium",
            b0_source="equilibrium",
            beta_pol_source="equilibrium",
        )
        assert gq.ip_source == "equilibrium"
        assert gq.b0_source == "equilibrium"
        assert gq.beta_pol_source == "equilibrium"

    def test_global_quantities_all_sources(self):
        """Test all global quantities source fields."""
        gq = GlobalQuantitiesMetadata(
            b0_source="equilibrium",
            beta_pol_source="equilibrium",
            beta_tor_source="equilibrium",
            beta_tor_norm_source="equilibrium",
            current_bootstrap_source="equilibrium",
            current_non_inductive_source="equilibrium",
            energy_diamagnetic_source="equilibrium",
            energy_thermal_source="core_profiles",
            h_factor_source="summary",
            ip_source="equilibrium",
            li_source="equilibrium",
            power_radiated_inside_separatrix_source="core_profiles",
            power_radiated_total_source="summary",
            q_95_source="equilibrium",
            r0_source="equilibrium",
            tau_energy_source="summary",
            v_loop_source="equilibrium",
        )
        assert gq.b0_source == "equilibrium"
        assert gq.energy_thermal_source == "core_profiles"
        assert gq.h_factor_source == "summary"


class TestHeatingCurrentDriveMetadata:
    """Tests for HeatingCurrentDriveMetadata model."""

    def test_heating_nbi_configuration(self):
        """Test NBI heating configuration."""
        heating = HeatingCurrentDriveMetadata(
            nbi_0_angle=45.0,
            nbi_0_direction=1,
            nbi_0_voltage=1000.0,
            nbi_0_power_source="nbi",
        )
        assert heating.nbi_0_angle == 45.0
        assert heating.nbi_0_direction == 1
        assert heating.nbi_0_voltage == 1000.0
        assert heating.nbi_0_power_source == "nbi"

    def test_heating_multiple_systems(self):
        """Test multiple heating systems."""
        heating = HeatingCurrentDriveMetadata(
            ec_0_power_source="ec",
            ic_0_power_source="ic",
            nbi_0_angle=45.0,
            nbi_1_angle=60.0,
            lh_0_power_source="lh",
        )
        assert heating.ec_0_power_source == "ec"
        assert heating.ic_0_power_source == "ic"
        assert heating.nbi_0_angle == 45.0
        assert heating.nbi_1_angle == 60.0
        assert heating.lh_0_power_source == "lh"


class TestBoundaryMetadata:
    """Tests for BoundaryMetadata model."""

    def test_boundary_sources(self):
        """Test boundary metadata sources."""
        boundary = BoundaryMetadata(
            type_source="equilibrium",
            x_point_source="equilibrium",
        )
        assert boundary.type_source == "equilibrium"
        assert boundary.x_point_source == "equilibrium"

    def test_boundary_strike_points(self):
        """Test boundary strike point sources."""
        boundary = BoundaryMetadata(
            strike_point_inner_r_source="equilibrium",
            strike_point_inner_z_source="equilibrium",
            strike_point_outer_r_source="equilibrium",
            strike_point_outer_z_source="equilibrium",
        )
        assert boundary.strike_point_inner_r_source == "equilibrium"
        assert boundary.strike_point_inner_z_source == "equilibrium"
        assert boundary.strike_point_outer_r_source == "equilibrium"
        assert boundary.strike_point_outer_z_source == "equilibrium"


class TestCodeMetadata:
    """Tests for CodeMetadata model."""

    def test_code_basic_fields(self):
        """Test basic code metadata fields."""
        code = CodeMetadata(
            commit="abc123def456",
            repository="https://github.com/iter/metis",
            description="METIS 1D integrated modeling code",
        )
        assert code.commit == "abc123def456"
        assert code.repository == "https://github.com/iter/metis"
        assert code.description == "METIS 1D integrated modeling code"

    def test_code_with_libraries(self):
        """Test code metadata with library dependencies."""
        code = CodeMetadata(
            commit="abc123",
            library_0_name="imas",
            library_0_version="4.7.3",
            library_0_commit="def456",
            library_0_repository="https://github.com/iter/imas",
            library_1_name="numpy",
            library_1_version="1.24.0",
        )
        assert code.library_0_name == "imas"
        assert code.library_0_version == "4.7.3"
        assert code.library_0_commit == "def456"
        assert code.library_0_repository == "https://github.com/iter/imas"
        assert code.library_1_name == "numpy"
        assert code.library_1_version == "1.24.0"


class TestSimulationMetadata:
    """Tests for SimulationMetadata model."""

    def test_simulation_metadata_empty(self):
        """Test creating empty simulation metadata."""
        metadata = SimulationMetadata()
        assert metadata.datetime is None
        assert metadata.composition is None
        assert metadata.ids_properties is None

    def test_simulation_metadata_with_categories(self):
        """Test simulation metadata with nested categories."""
        metadata = SimulationMetadata(
            datetime="2025-08-11T13:46:25.682813",
            composition=CompositionMetadata(deuterium=0.00934),
            ids_properties=IDSPropertiesMetadata(creation_date="2021-05-04 09:25:46"),
        )
        assert metadata.datetime == "2025-08-11T13:46:25.682813"
        assert metadata.composition.deuterium == 0.00934
        assert metadata.ids_properties.creation_date == "2021-05-04 09:25:46"

    def test_simulation_metadata_all_categories(self):
        """Test simulation metadata with all category types."""
        metadata = SimulationMetadata(
            datetime="2025-08-11T13:46:25.682813",
            composition=CompositionMetadata(deuterium=0.00934),
            ids_properties=IDSPropertiesMetadata(homogeneous_time=1),
            global_quantities=GlobalQuantitiesMetadata(ip_source="equilibrium"),
            heating_current_drive=HeatingCurrentDriveMetadata(nbi_0_angle=45.0),
            boundary=BoundaryMetadata(type_source="equilibrium"),
            code=CodeMetadata(commit="abc123"),
            configuration_source="test",
            configuration_value="double_null",
        )
        assert metadata.datetime == "2025-08-11T13:46:25.682813"
        assert metadata.composition.deuterium == 0.00934
        assert metadata.ids_properties.homogeneous_time == 1
        assert metadata.global_quantities.ip_source == "equilibrium"
        assert metadata.heating_current_drive.nbi_0_angle == 45.0
        assert metadata.boundary.type_source == "equilibrium"
        assert metadata.code.commit == "abc123"
        assert metadata.configuration_source == "test"
        assert metadata.configuration_value == "double_null"


class TestSimulationMetadataFromDict:
    """Tests for SimulationMetadata.from_metadata_dict() parser."""

    def test_parse_datetime(self):
        """Test parsing datetime field."""
        flat = {"datetime": "2025-08-11T13:46:25.682813"}
        metadata = SimulationMetadata.from_metadata_dict(flat)
        assert metadata.datetime == "2025-08-11T13:46:25.682813"

    def test_parse_composition(self):
        """Test parsing composition with dotted keys."""
        flat = {
            "composition.deuterium.value": 0.00934,
            "composition.helium_4.value": 0.02,
            "composition.z_effective.value": 1.8,
        }
        metadata = SimulationMetadata.from_metadata_dict(flat)
        assert metadata.composition.deuterium == 0.00934
        assert metadata.composition.helium_4 == 0.02
        assert metadata.composition.z_effective == 1.8

    def test_parse_ids_properties(self):
        """Test parsing IDS properties with dotted keys."""
        flat = {
            "ids_properties.creation_date": "2021-05-04 09:25:46",
            "ids_properties.homogeneous_time": 1,
            "ids_properties.comment": "Test comment",
        }
        metadata = SimulationMetadata.from_metadata_dict(flat)
        assert metadata.ids_properties.creation_date == "2021-05-04 09:25:46"
        assert metadata.ids_properties.homogeneous_time == 1
        assert metadata.ids_properties.comment == "Test comment"

    def test_parse_global_quantities_sources(self):
        """Test parsing global quantities sources."""
        flat = {
            "global_quantities.ip.source": "equilibrium",
            "global_quantities.b0.source": "equilibrium",
            "global_quantities.tau_energy.source": "summary",
        }
        metadata = SimulationMetadata.from_metadata_dict(flat)
        assert metadata.global_quantities.ip_source == "equilibrium"
        assert metadata.global_quantities.b0_source == "equilibrium"
        assert metadata.global_quantities.tau_energy_source == "summary"

    def test_parse_heating_current_drive(self):
        """Test parsing heating and current drive with indexed arrays."""
        flat = {
            "heating_current_drive.nbi[0].angle.value": 45.0,
            "heating_current_drive.nbi[0].direction.value": 1,
            "heating_current_drive.nbi[0].voltage.value": 1000.0,
            "heating_current_drive.nbi[1].angle.value": 60.0,
            "heating_current_drive.ec[0].source": "ec_system",
        }
        metadata = SimulationMetadata.from_metadata_dict(flat)
        assert metadata.heating_current_drive.nbi_0_angle == 45.0
        assert metadata.heating_current_drive.nbi_0_direction == 1
        assert metadata.heating_current_drive.nbi_0_voltage == 1000.0
        assert metadata.heating_current_drive.nbi_1_angle == 60.0
        assert metadata.heating_current_drive.ec_0_power_source == "ec_system"

    def test_parse_boundary_sources(self):
        """Test parsing boundary metadata sources."""
        flat = {
            "boundary.type.source": "equilibrium",
            "boundary.x_point.source": "equilibrium",
            "boundary.strike_point.inner.r.source": "equilibrium",
        }
        metadata = SimulationMetadata.from_metadata_dict(flat)
        assert metadata.boundary.type_source == "equilibrium"
        assert metadata.boundary.x_point_source == "equilibrium"
        assert metadata.boundary.strike_point_inner_r_source == "equilibrium"

    def test_parse_code_metadata(self):
        """Test parsing code metadata with libraries."""
        flat = {
            "code.commit": "abc123",
            "code.repository": "https://github.com/iter/metis",
            "code.library[0].name": "imas",
            "code.library[0].version": "4.7.3",
            "code.library[1].name": "numpy",
        }
        metadata = SimulationMetadata.from_metadata_dict(flat)
        assert metadata.code.commit == "abc123"
        assert metadata.code.repository == "https://github.com/iter/metis"
        assert metadata.code.library_0_name == "imas"
        assert metadata.code.library_0_version == "4.7.3"
        assert metadata.code.library_1_name == "numpy"

    def test_parse_configuration_fields(self):
        """Test parsing simple configuration fields."""
        flat = {
            "configuration.source": "test",
            "configuration.value": "double_null",
        }
        metadata = SimulationMetadata.from_metadata_dict(flat)
        assert metadata.configuration_source == "test"
        assert metadata.configuration_value == "double_null"

    def test_parse_complete_metadata(self):
        """Test parsing complete metadata with all categories."""
        flat = {
            "datetime": "2025-08-11T13:46:25.682813",
            "composition.deuterium.value": 0.00934,
            "composition.helium_4.value": 0.02,
            "ids_properties.creation_date": "2021-05-04 09:25:46",
            "ids_properties.homogeneous_time": 1,
            "global_quantities.ip.source": "equilibrium",
            "heating_current_drive.nbi[0].angle.value": 45.0,
            "boundary.type.source": "equilibrium",
            "code.commit": "abc123",
            "configuration.value": "double_null",
        }
        metadata = SimulationMetadata.from_metadata_dict(flat)
        assert metadata.datetime == "2025-08-11T13:46:25.682813"
        assert metadata.composition.deuterium == 0.00934
        assert metadata.ids_properties.creation_date == "2021-05-04 09:25:46"
        assert metadata.global_quantities.ip_source == "equilibrium"
        assert metadata.heating_current_drive.nbi_0_angle == 45.0
        assert metadata.boundary.type_source == "equilibrium"
        assert metadata.code.commit == "abc123"
        assert metadata.configuration_value == "double_null"

    def test_parse_empty_dict(self):
        """Test parsing empty metadata dictionary."""
        metadata = SimulationMetadata.from_metadata_dict({})
        assert metadata.datetime is None
        assert metadata.composition is None
        assert metadata.ids_properties is None
