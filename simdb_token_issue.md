# Exploring ITER SimDB

## Quick Start Guide

### Setup (One-time)

```bash
# Configure ITER remote
uv run simdb remote config new iter https://simdb.iter.org/scenarios/api --default
uv run simdb remote config set-option iter firewall F5

# Test connection
uv run simdb remote test

# Check server version
uv run simdb remote version
```

### Searching & Exploring

**List simulations:**
```bash
uv run simdb remote list --limit 10
```

**Get detailed info:**
```bash
uv run simdb remote info 100001/2
```

**Search by metadata:**
```bash
# Find ITER simulations
uv run simdb remote query machine=ITER --limit 5

# Search by code name (contains)
uv run simdb remote query code.name=in:METIS --limit 5

# Multiple constraints (AND logic)
uv run simdb remote query machine=ITER status=passed --limit 5

# Show additional metadata columns
uv run simdb remote query machine=ITER -m code.name -m code.version --limit 5
```

**Query modifiers:**
- `eq:` - Exact match (default)
- `in:` - Contains (case-insensitive)
- `gt:`, `ge:`, `lt:`, `le:` - Numeric comparisons
- `agt:`, `age:`, `alt:`, `ale:` - Array element comparisons

**Examples:**
```bash
# Power greater than 20 MW
uv run simdb remote query heating_current_drive.power_additional.value=gt:20000000

# Alias contains "100"
uv run simdb remote query alias=in:100

# Include UUID in output
uv run simdb remote query machine=ITER --uuid --limit 5
```

### Available Metadata Fields

From the simulations, you can query:
- `machine` - Machine name (e.g., ITER)
- `code.name` - Simulation code name
- `code.version` - Code version
- `status` - Validation status
- `description` - Simulation description
- `alias` - Simulation alias/ID
- `ids` - IDS data structures present
- `global_quantities.*` - Plasma parameters
- `heating_current_drive.*` - Heating system data
- `composition.*` - Plasma composition

---

## Known Issue: Token Authentication

**Problem:** The `simdb remote token new` command fails with HTTP 500 (server-side error).

**Workaround:** Commands will prompt for credentials. Enter your ITER username and password when asked.

**Status:** Reported to SimDB maintainers (2025-11-25)
