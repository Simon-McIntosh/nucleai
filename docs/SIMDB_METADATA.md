# SimDB Metadata Investigation Results

## Summary

The SimDB REST API provides **true metadata** (~11 reliably filled fields) and **scalar data fields** (235 physics parameters). Time series **data** (376 numpy arrays) should be fetched via IDS file download.

## Findings

### 1. Clear Distinction: Metadata vs Data

SimDB API provides **611 total fields**, categorized as:

- **~11 True Metadata fields** - Simulation provenance and IDS properties
  - 7 core fields (always present): uuid, alias, machine, code.name, code.version, status, description
  - 4 commonly filled (35-100%): datetime, ids_properties.creation_date, ids_properties.version_put.data_dictionary, ids_properties.homogeneous_time

- **~235 Scalar Data fields** (str/int/float) - Physics parameters, not metadata
  - composition.deuterium.value, simulation.time_begin/end, global_quantities.*.source, etc.

- **376 Time Series Data fields** (ndarray) - Evolution data, use IDS download

### 2. True Metadata Fields

#### Core Metadata (8 fields - always present, NO request needed) ✅
```python
# These are ALWAYS in the API response:
sim.uuid           # "1e23770776a811f0bd82d4f5ef75e918"
sim.alias          # "100001/2"
sim.machine        # "ITER"
sim.code.name      # "METIS4IMAS"
sim.code.version   # "6.1894"
sim.status         # "passed"
sim.description    # "reference_name:ITER-full-field-H..."
sim.model_extra['datetime']  # "2025-08-11T13:46:25.682813" (always in metadata array)
```

#### Reliably Filled (MUST request via include_metadata) ✅
```python
# Request: include_metadata=['uploaded_by']
sim.uploaded_by    # "Mireille.Schneider@iter.org" (100% METIS/JINTRAC/ASTRA, 0% SOLPS)
# Note: Extracted from metadata array by model validator
```

#### Commonly Filled (request via include_metadata, 14-100% population) ⚠️
```python
# Request: include_metadata=['ids_properties.creation_date', ...]
sim.model_extra['ids_properties.creation_date']              # 14-100%
sim.model_extra['ids_properties.version_put.data_dictionary'] # 43-100%
sim.model_extra['ids_properties.homogeneous_time']            # 82-100%
sim.model_extra['ids_properties.comment']                     # 0-100% (varies)
```

#### Rarely Filled (<1% population) ❌
```python
# Request: include_metadata=['code.commit', ...]
sim.model_extra['code.commit']       # 0%
sim.model_extra['code.repository']   # 0%
sim.model_extra['code.description']  # 0%
```

**Key Insight:** The API only includes fields in the response that are:
1. Core fields (always present)
2. Explicitly requested via `include_metadata` parameter

This explains the "0% to 100% jump" - `uploaded_by` is 0% when NOT requested, 100% when requested.

### 3. Scalar Data Fields (Physics Parameters, NOT Metadata) ⚠️

These 235 str/int/float fields are **physics parameters**, not simulation metadata:

```python
# These are SCALAR DATA, not metadata:
sim.model_extra['composition.deuterium.value']  # 0.00934 - plasma composition
sim.model_extra['simulation.time_begin']        # 1.5 - simulation start time
sim.model_extra['simulation.time_end']          # 647.4 - simulation end time
sim.model_extra['global_quantities.ip.source']  # "equilibrium" - data source
```

**These should be requested on-demand for specific analysis**, not as "metadata".

### 4. Time Series Data Fields (Use IDS Download) ❌

These 376 ndarray fields should be fetched via IDS file download, not metadata API:

```python
# DON'T REQUEST THESE:
'global_quantities.ip.value'  # ndarray - plasma current evolution
'global_quantities.b0.value'  # ndarray - magnetic field evolution  
'boundary.elongation.value'  # ndarray - elongation evolution
'heating_current_drive.*.power.value'  # ndarray - heating power evolution
```

**Why not request as metadata:**
- Returns base64-encoded numpy arrays (inefficient)
- Large data transfer over REST API
- Proper way: Download IDS files with simulation UUID
- IDS provides full data with proper structure

## Coverage Analysis

Tested across codes with `include_metadata` requesting various fields:

### METIS Simulations (26 total)
- ✅ 96-100% coverage for most physics quantities
- `global_quantities.ip.value`: 25/26 (96%)
- `global_quantities.b0.value`: 26/26 (100%)
- `composition.deuterium.value`: 26/26 (100%)
- `heating_current_drive.*.power.value`: 25/26 (96%)

### JINTRAC Simulations (62 total)
- ✅ 60-70% coverage for global quantities
- `global_quantities.ip.value`: 42/62 (68%)
- `heating_current_drive.*.power.value`: 37-40/62 (60-65%)

### ASTRA Simulations (225 total)
- ⚠️ Lower coverage (9-10%)
- `global_quantities.ip.value`: 22/225 (10%)
- Coverage varies by upload/processing method

## Recommended Usage

### 1. **Request Only Scalar Metadata**

Filter fields by type when requesting metadata:

```python
from nucleai.simdb import query, discover_available_fields

# Get field definitions
all_fields = await discover_available_fields()

# Filter for metadata (exclude ndarrays)
metadata_fields = [
    f['name'] for f in all_fields 
    if f['type'] in ['str', 'int', 'float']
]

# Request only metadata
results = await query(
    {'machine': 'ITER'},
    include_metadata=[
        'simulation.time_begin',
        'simulation.time_end',
        'composition.deuterium.value',
        'global_quantities.ip.source',  # source annotation - OK
        # NOT: 'global_quantities.ip.value'  # ndarray - use IDS download
    ]
)

# Access scalar metadata
for sim in results:
    time_begin = sim.model_extra.get('simulation.time_begin')
    deuterium = sim.model_extra.get('composition.deuterium.value')
    print(f"{sim.alias}: t={time_begin}s, D={deuterium}")
```

### 2. **Use IDS Download for Time Series**

For time series data (not yet implemented):

```python
# 1. Use metadata for discovery
results = await query(
    {'machine': 'ITER', 'code': 'JINTRAC'},
    include_metadata=['global_quantities.ip.source']  # scalar only
)

# 2. Get IDS file URI from simulation
sim = results[0]
ids_uri = sim.ids_uri  # or whatever field provides download link

# 3. Download IDS file (TODO: implement)
ids_data = await download_ids_file(ids_uri)
ip_evolution = ids_data['global_quantities']['ip']['value']  # numpy array

import matplotlib.pyplot as plt
plt.plot(ip_evolution)
plt.ylabel('Plasma Current (A)')
plt.show()
```

### 3. **Field Categories by Type**

Based on 611 total fields:

**Metadata (235 fields):**
- `composition.*` (scalars: fractions, Z_effective)
- `*.source` (all source annotations)
- `*.description` (all descriptions)
- `ids_properties.*` (IDS structure metadata)
- `code.*` (commit, version, library info)
- `datetime` (simulation timestamp)
- `simulation.time_begin/end/step` (timing scalars)

**Data (376 fields):**
- `global_quantities.*.value` (time series: ip, b0, energy, etc.)
- `boundary.*.value` (shape evolution)
- `heating_current_drive.*.power.value` (heating profiles)
- `core_profiles.profiles_1d[*].*` (radial profiles at time slices)

## Implementation Notes

### Current Model Behavior

The `Simulation` Pydantic model stores all metadata in `model_extra`:

```python
# After query with include_metadata
sim = results[0]

# Core fields (always present)
sim.uuid           # UUID string
sim.alias          # "ITER-001"
sim.machine        # "ITER"
sim.code           # CodeInfo(name="JINTRAC", version="1.0")
sim.status         # "passed"

# Requested metadata in model_extra
sim.model_extra['simulation.time_begin']  # 1.5
sim.model_extra['composition.deuterium.value']  # 0.00934
```

### Validator Behavior

The `@model_validator` in `Simulation` automatically flattens the API's metadata array structure:

```python
# API returns:
{
    "uuid": "123...",
    "metadata": [
        {"element": "simulation.time_begin", "value": 1.5},
        {"element": "composition.deuterium.value", "value": 0.00934}
    ]
}

# Validator transforms to:
{
    "uuid": "123...",
    "simulation.time_begin": 1.5,
    "composition.deuterium.value": 0.00934
}

# Pydantic stores in model_extra because ConfigDict(extra="allow")
```

### Why NOT Decode Arrays

If you accidentally request ndarray fields, they arrive as:

```python
sim.model_extra['global_quantities.ip.value'] = {
    '_type': 'numpy.ndarray',
    'bytes': 'AAAAAABqCMH/////...',  # base64 encoded
    'dtype': 'float64'
}
```

**We deliberately DO NOT auto-decode these** because:
1. Inefficient: Large data over REST API
2. Wrong pattern: Should use IDS file download
3. Performance: Decoding all arrays on every query is slow
4. Architecture: Metadata API is for discovery, not data transfer

## Next Steps

1. ✅ Understand metadata vs data distinction (DONE)
2. ⬜ Update `discover_available_fields()` documentation to explain type filtering
3. ⬜ Add example of filtering fields by type in docstring
4. ⬜ Implement IDS file download client for time series data
5. ⬜ Document metadata-only access pattern in user guide
6. ⬜ Consider adding warning if ndarray fields detected in model_extra
