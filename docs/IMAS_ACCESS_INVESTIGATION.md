# IMAS Data Access Investigation

**Date**: November 27, 2025  
**Status**: ✓ Feasibility Confirmed

## Executive Summary

We can access IDS data via imas-python and convert to xarray format for lazy-loaded datasets. The architecture is feasible for building a natural language interface to fusion simulation data.

## Current Environment

- **imas-python**: 2.0.1 (installed)
- **xarray**: 2025.11.0 (installed)
- **imas-data-dictionaries**: 4.1.0 (installed)
- **imas_core**: Not available (requires system installation, not on PyPI)

## What Works

### ✓ IDS Creation and Manipulation
```python
import imas

factory = imas.IDSFactory()
eq = factory.equilibrium()

# Set time data
eq.time = np.array([0.0, 0.1, 0.2])

# Add time slices
eq.time_slice.resize(1)
eq.time_slice[0].time = 0.0
eq.time_slice[0].global_quantities.ip = 15.0e6  # 15 MA
```

### ✓ xarray Conversion
```python
import imas.util

# Convert specific paths to xarray Dataset
ds = imas.util.to_xarray(
    eq,
    "time_slice/global_quantities/ip"
)

# Result:
# <xarray.Dataset>
# Dimensions:                          (time_slice.time: 1)
# Coordinates:
#   * time_slice.time                  (time_slice.time) float64 0.0
# Data variables:
#     time_slice.global_quantities.ip  (time_slice.time) float64 1.5e+07
```

### ✓ IDS Structure Introspection
```python
# Access metadata
eq.metadata  # <IDSMetadata for 'equilibrium'>
eq.time_slice[0].global_quantities.ip.metadata  # <IDSMetadata for 'ip'>

# Check coordinates
eq.time_slice[0].global_quantities.ip.coordinates

# List structure
import imas.util
imas.util.inspect(eq, hide_empty_nodes=True)
```

### ✓ SimDB Integration
```python
from nucleai.simdb import fetch_simulation

sim = await fetch_simulation(uuid)
imas_uri = sim.imas_uri
# Example: imas://uda.iter.org/uda?path=/work/imas/shared/imasdb/ITER/3/100001/2&backend=hdf5
```

## What Doesn't Work (Without imas_core)

### ✗ Remote UDA Backend Access
```python
# This fails without imas_core:
entry = imas.DBEntry("imas://uda.iter.org/uda?path=...&backend=hdf5", "r")
# Error: The IMAS Core library is not available
```

**Workaround**: 
- Use local HDF5 or netCDF files
- System installation of imas_core required for UDA/network access
- imas_core not available on PyPI (only placeholder version 0.0.0 on test.pypi)

## Key IDS Paths Discovered

### Equilibrium IDS
- **Plasma current**: `time_slice/global_quantities/ip` (Amperes)
- **Poloidal flux**: `time_slice/profiles_2d/psi`
- **Magnetic axis R**: `time_slice/global_quantities/magnetic_axis/r`
- **Magnetic axis Z**: `time_slice/global_quantities/magnetic_axis/z`

### Path Syntax Rules
- No indices in paths: `"time_slice/global_quantities/ip"` not `"time_slice[0]/..."`
- Use `/` or `.` as separator: `"time_slice.global_quantities.ip"` also works
- Coordinates automatically included in xarray conversion

### Time Modes (from IMAS docs)
- **Homogeneous time** (`ids_properties.homogeneous_time = 1`): Single time coordinate
- **Heterogeneous time** (`ids_properties.homogeneous_time = 0`): Multiple time dimensions
- Path: `global_quantities/ip` uses `time` coordinate in homogeneous mode

## Recommended Architecture

### Module Structure: `nucleai/imas/`

```
nucleai/imas/
├── __init__.py           # Public API exports
├── dataset.py            # IMASDataset class
├── paths.py              # Common IDS path definitions
├── introspect.py         # Discovery helpers
└── exceptions.py         # IMAS-specific exceptions
```

### Core Classes

#### IMASDataset
```python
class IMASDataset:
    """Wrapper for IMAS data access with lazy loading and xarray conversion."""
    
    @classmethod
    async def from_uri(cls, uri: str) -> IMASDataset:
        """Open from IMAS URI (requires imas_core for remote access)."""
        
    @classmethod
    async def from_file(cls, path: str) -> IMASDataset:
        """Open from local HDF5 or netCDF file."""
        
    @classmethod
    async def from_simulation(cls, sim: Simulation) -> IMASDataset:
        """Open from SimDB simulation metadata."""
        
    async def get(self, ids_name: str, lazy: bool = True) -> IDSToplevel:
        """Get IDS with optional lazy loading."""
        
    async def to_xarray(
        self, 
        ids_name: str, 
        paths: list[str] | None = None
    ) -> xr.Dataset:
        """Convert IDS paths to xarray Dataset."""
        
    async def list_ids(self) -> list[str]:
        """List available IDSs in this entry."""
```

#### IDSPaths (Constants)
```python
class IDSPaths:
    """Common IDS path definitions."""
    
    # Equilibrium
    EQUILIBRIUM_IP = "time_slice/global_quantities/ip"
    EQUILIBRIUM_PSI = "time_slice/profiles_2d/psi"
    EQUILIBRIUM_B_FIELD_R = "time_slice/profiles_2d/b_field_r"
    EQUILIBRIUM_B_FIELD_Z = "time_slice/profiles_2d/b_field_z"
    
    # Core Profiles
    CORE_PROFILES_TE = "profiles_1d/electrons/temperature"
    CORE_PROFILES_NE = "profiles_1d/electrons/density"
    CORE_PROFILES_TI = "profiles_1d/ion/temperature"
```

### Example Usage

```python
from nucleai.imas import IMASDataset, IDSPaths
from nucleai.simdb import fetch_simulation

# Get simulation from SimDB
sim = await fetch_simulation("1e23770776a811f0bd82d4f5ef75e918")

# Open IMAS data
ds = await IMASDataset.from_simulation(sim)

# Lazy load equilibrium
eq = await ds.get("equilibrium", lazy=True)

# Convert plasma current to xarray
ip_data = await ds.to_xarray("equilibrium", paths=[IDSPaths.EQUILIBRIUM_IP])

# Access as xarray DataArray
ip_series = ip_data["time_slice.global_quantities.ip"]
print(f"Plasma current range: {ip_series.values.min()/1e6:.2f} - {ip_series.values.max()/1e6:.2f} MA")

# Plot with xarray/matplotlib integration
ip_series.plot()
```

## Implementation Plan

### Phase 1: Core Infrastructure
- [ ] Create `nucleai/imas/` module structure
- [ ] Implement `IMASDataset` class with local file support
- [ ] Add `IDSPaths` constants for common paths
- [ ] Write unit tests with mock IDS data

### Phase 2: SimDB Integration
- [ ] Add `from_simulation()` class method
- [ ] Handle missing `imas_uri` gracefully
- [ ] Add caching for opened entries
- [ ] Document imas_core requirements

### Phase 3: Enhanced Features
- [ ] Add `find_paths()` helper for IDS exploration
- [ ] Implement path validation
- [ ] Add type hints for common IDS structures
- [ ] Support batch loading multiple IDSs

### Phase 4: Documentation
- [ ] Document common IDS paths and structures
- [ ] Add examples for each IDS type
- [ ] Create tutorial notebook
- [ ] Document imas_core installation for remote access

## Testing Strategy

### Unit Tests
```python
# Mock IDS creation for tests
@pytest.fixture
def mock_equilibrium():
    factory = imas.IDSFactory()
    eq = factory.equilibrium()
    eq.time = np.array([0.0, 0.1, 0.2])
    eq.time_slice.resize(3)
    for i, t in enumerate(eq.time):
        eq.time_slice[i].time = t
        eq.time_slice[i].global_quantities.ip = (15.0 + i * 0.5) * 1e6
    return eq

async def test_to_xarray_conversion(mock_equilibrium):
    ds = await IMASDataset.to_xarray(mock_equilibrium, paths=[IDSPaths.EQUILIBRIUM_IP])
    assert "time_slice.global_quantities.ip" in ds
    assert ds["time_slice.global_quantities.ip"].shape == (3,)
```

### Integration Tests
- Test with IMAS training data (if available)
- Test lazy loading behavior
- Test error handling for missing paths
- Test with real SimDB URIs (may require imas_core)

## Known Limitations

1. **Remote Access**: Requires system imas_core installation (not available on PyPI)
2. **Network Paths**: Cannot access ITER network paths without imas_core
3. **Backend Support**: Limited to in-memory and local file backends without imas_core
4. **Full IDS Conversion**: Lazy loaded IDSs cannot be fully converted to xarray (must specify paths)

## References

- IMAS-Python Documentation: https://imas-python.readthedocs.io/
- IMAS Data Dictionary: https://imas-data-dictionary.readthedocs.io/
- xarray Documentation: https://docs.xarray.dev/
- SimDB Repository: https://github.com/iterorganization/SimDB

## Next Steps

1. Review this document with team
2. Get approval for proposed architecture
3. Begin Phase 1 implementation
4. Coordinate with IT for imas_core installation requirements
