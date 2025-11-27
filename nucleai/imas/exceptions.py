"""IMAS-specific exceptions with recovery hints.

All exceptions inherit from nucleai.core.exceptions.NucleaiError and include
recovery hints for debugging and AI agent guidance.
"""

from nucleai.core.exceptions import NucleaiError


class ImasAccessError(NucleaiError):
    """Cannot access IMAS data.

    Raised when:
    - URI is invalid or cannot be parsed
    - imas_core not available for remote UDA access
    - Network connection to remote server fails
    - Authentication to remote server fails
    - Local file path does not exist

    Examples:
        >>> raise ImasAccessError(
        ...     "Cannot access UDA server at uda.iter.org",
        ...     recovery_hint="Install imas_core system package for remote UDA access, "
        ...                   "or use local HDF5/netCDF files if data is available locally"
        ... )
    """


class ImasDataError(NucleaiError):
    """Error reading or processing IDS data.

    Raised when:
    - Requested IDS name not found in data entry
    - IDS data structure is malformed or incomplete
    - Required fields are missing from IDS
    - Data type incompatible with requested operation

    Examples:
        >>> raise ImasDataError(
        ...     "IDS 'equilibrium' not found in data entry",
        ...     recovery_hint="Check available IDS types with loader.list_ids(). "
        ...                   "Available types may depend on simulation code used."
        ... )
    """


class ImasConversionError(NucleaiError):
    """Error converting IDS to xarray format.

    Raised when:
    - Invalid IDS path specified for conversion
    - Lazy-loaded IDS cannot be converted without explicit paths
    - Data structure incompatible with xarray
    - Coordinate mismatch in IDS data

    Examples:
        >>> raise ImasConversionError(
        ...     "Cannot convert lazy-loaded IDS without explicit paths",
        ...     recovery_hint="Specify paths list when converting: "
        ...                   "to_xarray(ids_name, paths=['time_slice/global_quantities/ip'])"
        ... )
    """
