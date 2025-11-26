"""Structured Pydantic models for SimDB metadata.

This module provides typed models for all metadata categories instead of
using the generic model_extra pattern. These models enable:
- Type-safe access to metadata fields
- IDE autocomplete
- Schema validation
- Clear documentation of available fields

Classes:
    CompositionMetadata: Plasma composition fractions
    IDSPropertiesMetadata: IDS file properties and provenance
    GlobalQuantitiesMetadata: Global plasma parameters (scalar values only)
    HeatingCurrentDriveMetadata: Heating and current drive metadata
    BoundaryMetadata: Plasma boundary metadata
    CodeMetadata: Extended code information
    SimulationMetadata: Complete metadata container

Examples:
    >>> from nucleai.simdb.metadata import SimulationMetadata
    >>> # Discover available fields
    >>> print(SimulationMetadata.model_json_schema())
    >>>
    >>> # Access metadata with type safety
    >>> metadata = SimulationMetadata(
    ...     composition=CompositionMetadata(deuterium=0.00934, helium_4=0.02),
    ...     ids_properties=IDSPropertiesMetadata(
    ...         creation_date="2021-05-04 09:25:46",
    ...         homogeneous_time=1
    ...     )
    ... )
    >>> print(metadata.composition.deuterium)  # IDE autocomplete!
    0.00934
"""

import pydantic


class CompositionMetadata(pydantic.BaseModel):
    """Plasma composition fractions (scalars only).

    All values are fractions (0.0 to 1.0) representing species concentration.

    Examples:
        >>> comp = CompositionMetadata(deuterium=0.00934, helium_4=0.02)
        >>> print(comp.deuterium)
        0.00934
    """

    argon: float | None = None
    beryllium: float | None = None
    carbon: float | None = None
    deuterium: float | None = None
    deuterium_tritium: float | None = None
    helium_3: float | None = None
    helium_4: float | None = None
    hydrogen: float | None = None
    krypton: float | None = None
    neon: float | None = None
    nitrogen: float | None = None
    oxygen: float | None = None
    tritium: float | None = None
    tungsten: float | None = None
    xenon: float | None = None
    z_effective: float | None = None


class IDSPropertiesMetadata(pydantic.BaseModel):
    """IDS file properties and provenance metadata.

    Examples:
        >>> ids_props = IDSPropertiesMetadata(
        ...     creation_date="2021-05-04 09:25:46",
        ...     homogeneous_time=1,
        ...     comment="IMAS implementation of METIS"
        ... )
        >>> print(ids_props.creation_date)
        2021-05-04 09:25:46
    """

    comment: str | None = None
    creation_date: str | None = None
    homogeneous_time: int | None = None
    provider: str | None = None
    version_put_data_dictionary: str | None = None
    version_put_access_layer: str | None = None
    version_put_access_layer_language: str | None = None
    provenance_node_reference_name: str | None = None


class GlobalQuantitiesMetadata(pydantic.BaseModel):
    """Global plasma parameters metadata (scalar values and sources only).

    Note: This contains METADATA about the quantities (sources, descriptions),
    not the time series data itself. Time series should be fetched via IDS files.

    Examples:
        >>> gq = GlobalQuantitiesMetadata(
        ...     ip_source="equilibrium",
        ...     b0_source="equilibrium"
        ... )
        >>> print(gq.ip_source)
        equilibrium
    """

    # Source annotations (which IDS provides this data)
    b0_source: str | None = None
    beta_pol_source: str | None = None
    beta_tor_source: str | None = None
    beta_tor_norm_source: str | None = None
    current_bootstrap_source: str | None = None
    current_non_inductive_source: str | None = None
    energy_diamagnetic_source: str | None = None
    energy_thermal_source: str | None = None
    h_factor_source: str | None = None
    ip_source: str | None = None
    li_source: str | None = None
    power_radiated_inside_separatrix_source: str | None = None
    power_radiated_total_source: str | None = None
    q_95_source: str | None = None
    r0_source: str | None = None
    tau_energy_source: str | None = None
    v_loop_source: str | None = None


class HeatingCurrentDriveMetadata(pydantic.BaseModel):
    """Heating and current drive metadata (scalars only).

    Examples:
        >>> heating = HeatingCurrentDriveMetadata(
        ...     nbi_0_angle=45.0,
        ...     nbi_0_direction=1
        ... )
        >>> print(heating.nbi_0_angle)
        45.0
    """

    # Electron cyclotron
    ec_0_power_source: str | None = None

    # Ion cyclotron
    ic_0_power_source: str | None = None

    # Neutral beam injection
    nbi_0_angle: float | None = None
    nbi_0_direction: int | None = None
    nbi_0_power_source: str | None = None
    nbi_0_voltage: float | None = None
    nbi_1_angle: float | None = None
    nbi_1_direction: int | None = None
    nbi_1_power_source: str | None = None
    nbi_1_voltage: float | None = None

    # Lower hybrid
    lh_0_power_source: str | None = None


class BoundaryMetadata(pydantic.BaseModel):
    """Plasma boundary metadata (scalars only).

    Examples:
        >>> boundary = BoundaryMetadata(
        ...     type_source="equilibrium",
        ...     strike_point_inner_r_source="equilibrium"
        ... )
        >>> print(boundary.type_source)
        equilibrium
    """

    strike_point_inner_r_source: str | None = None
    strike_point_inner_z_source: str | None = None
    strike_point_outer_r_source: str | None = None
    strike_point_outer_z_source: str | None = None
    type_source: str | None = None
    x_point_source: str | None = None


class CodeMetadata(pydantic.BaseModel):
    """Extended code metadata.

    Examples:
        >>> code = CodeMetadata(
        ...     commit="abc123def456",
        ...     repository="https://github.com/iter/metis"
        ... )
        >>> print(code.commit)
        abc123def456
    """

    commit: str | None = None
    description: str | None = None
    repository: str | None = None
    # Library dependencies
    library_0_commit: str | None = None
    library_0_name: str | None = None
    library_0_repository: str | None = None
    library_0_version: str | None = None
    library_1_commit: str | None = None
    library_1_name: str | None = None
    library_1_repository: str | None = None
    library_1_version: str | None = None


class SimulationMetadata(pydantic.BaseModel):
    """Complete structured metadata for a simulation.

    Replaces the generic model_extra pattern with typed fields organized
    by category. All fields are optional - only populate what's available.

    Access pattern: sim.metadata.datetime, sim.metadata.composition.deuterium, etc.

    Examples:
        >>> from nucleai.simdb import query
        >>>
        >>> # Metadata auto-fetched by query
        >>> results = await query({'machine': 'ITER'}, limit=1)
        >>> sim = results[0]
        >>>
        >>> # Access metadata fields
        >>> print(sim.metadata.datetime)  # Upload timestamp
        >>> print(sim.metadata.ids_properties.creation_date)  # IDS creation
        >>> if sim.metadata.composition:
        ...     print(sim.metadata.composition.deuterium)
    """

    # Always present
    datetime: str | None = None

    # Commonly filled categories
    composition: CompositionMetadata | None = None
    ids_properties: IDSPropertiesMetadata | None = None
    global_quantities: GlobalQuantitiesMetadata | None = None

    # Less commonly filled
    heating_current_drive: HeatingCurrentDriveMetadata | None = None
    boundary: BoundaryMetadata | None = None
    code: CodeMetadata | None = None

    # Simple scalar fields
    configuration_source: str | None = None
    configuration_value: str | None = None

    @classmethod
    def from_metadata_dict(cls, metadata_dict: dict[str, any]) -> "SimulationMetadata":
        """Parse flat metadata dictionary into structured model.

        Args:
            metadata_dict: Flat dict with dotted keys like 'composition.deuterium.value'

        Returns:
            SimulationMetadata with nested structure

        Examples:
            >>> flat = {
            ...     'datetime': '2025-08-11T13:46:25.682813',
            ...     'composition.deuterium.value': 0.00934,
            ...     'ids_properties.creation_date': '2021-05-04 09:25:46'
            ... }
            >>> metadata = SimulationMetadata.from_metadata_dict(flat)
            >>> print(metadata.composition.deuterium)
            0.00934
        """
        # Extract datetime
        result = {}
        if "datetime" in metadata_dict:
            result["datetime"] = metadata_dict["datetime"]

        # Parse composition
        composition_data = {}
        for key, value in metadata_dict.items():
            if key.startswith("composition.") and key.endswith(".value"):
                species = key.split(".")[1]
                composition_data[species] = value
        if composition_data:
            result["composition"] = CompositionMetadata(**composition_data)

        # Parse ids_properties
        ids_props_data = {}
        for key, value in metadata_dict.items():
            if key.startswith("ids_properties."):
                field_name = key.replace("ids_properties.", "").replace(".", "_")
                ids_props_data[field_name] = value
        if ids_props_data:
            result["ids_properties"] = IDSPropertiesMetadata(**ids_props_data)

        # Parse global_quantities sources
        gq_data = {}
        for key, value in metadata_dict.items():
            if key.startswith("global_quantities.") and key.endswith(".source"):
                param = key.split(".")[1]
                gq_data[f"{param}_source"] = value
        if gq_data:
            result["global_quantities"] = GlobalQuantitiesMetadata(**gq_data)

        # Parse heating_current_drive
        heating_data = {}
        for key, value in metadata_dict.items():
            if key.startswith("heating_current_drive."):
                # e.g., 'heating_current_drive.nbi[0].angle.value' -> 'nbi_0_angle'
                parts = key.replace("heating_current_drive.", "").split(".")
                if "[" in parts[0]:
                    device = parts[0].split("[")[0]
                    index = parts[0].split("[")[1].split("]")[0]
                    field = parts[1] if len(parts) > 1 else "power"
                    if field == "source":
                        field_name = f"{device}_{index}_power_source"
                    else:
                        field_name = f"{device}_{index}_{field}"
                    heating_data[field_name] = value
        if heating_data:
            result["heating_current_drive"] = HeatingCurrentDriveMetadata(**heating_data)

        # Parse boundary
        boundary_data = {}
        for key, value in metadata_dict.items():
            if key.startswith("boundary.") and key.endswith(".source"):
                field = key.replace("boundary.", "").replace(".source", "").replace(".", "_")
                boundary_data[f"{field}_source"] = value
        if boundary_data:
            result["boundary"] = BoundaryMetadata(**boundary_data)

        # Parse code
        code_data = {}
        for key, value in metadata_dict.items():
            if key.startswith("code.") and key not in ["code.name", "code.version"]:
                field = (
                    key.replace("code.", "").replace("[", "_").replace("]", "").replace(".", "_")
                )
                code_data[field] = value
        if code_data:
            result["code"] = CodeMetadata(**code_data)

        # Simple fields
        if "configuration.source" in metadata_dict:
            result["configuration_source"] = metadata_dict["configuration.source"]
        if "configuration.value" in metadata_dict:
            result["configuration_value"] = metadata_dict["configuration.value"]

        return cls(**result)
