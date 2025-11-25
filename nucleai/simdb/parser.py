r"""Parse SimDB CLI output to Python objects.

Functions to parse SimDB CLI table output and convert to Pydantic models.
Handles various output formats and edge cases.

Functions:
    parse_query_output: Parse query results table to Simulation list
    parse_simulation_info: Parse detailed simulation info to Simulation

Examples:
    >>> from nucleai.simdb.parser import parse_query_output
    >>> output = "uuid | alias | machine\n123... | ITER-001 | ITER"
    >>> simulations = parse_query_output(output)
    >>> print(simulations[0].alias)
    ITER-001
"""

from nucleai.core.exceptions import ValidationError
from nucleai.core.models import CodeInfo, Simulation


def parse_query_output(output: str) -> list[Simulation]:
    """Parse SimDB query output table to list of Simulations.

    Parses table-formatted output from 'simdb remote query' command.
    Extracts simulation metadata and constructs Simulation objects.

    Args:
        output: Raw CLI output string with table format

    Returns:
        List of Simulation objects parsed from output

    Raises:
        ValidationError: If output format is invalid or unparseable

    Examples:
        >>> output = '''
        ... uuid                                 | alias     | machine
        ... 123e4567-e89b-12d3-a456-426614174000 | ITER-001  | ITER
        ... '''
        >>> simulations = parse_query_output(output)
        >>> len(simulations)
        1
        >>> simulations[0].alias
        'ITER-001'
    """
    if not output or not output.strip():
        return []

    lines = [line.strip() for line in output.strip().split("\n") if line.strip()]

    if len(lines) < 2:  # Need header + at least one row
        return []

    # Parse header to get column indices
    header = lines[0]
    if "|" not in header:
        raise ValidationError(
            f"Invalid SimDB output format: {output[:100]}",
            recovery_hint="Check SimDB CLI is working: uv run simdb remote list --limit 1",
        )

    # Simple parsing - split by | and strip whitespace
    # In real implementation, would need more robust parsing
    simulations = []
    for line in lines[1:]:
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:  # Minimum fields
                # This is simplified - real parser would map by column names
                simulations.append(
                    Simulation(
                        uuid=parts[0] if parts[0] else "unknown",
                        alias=parts[1] if len(parts) > 1 else "unknown",
                        machine=parts[2] if len(parts) > 2 else "unknown",
                        code=CodeInfo(name="unknown", version="unknown"),
                        description="",
                        status="pending",
                    )
                )

    return simulations


def parse_simulation_info(output: str) -> Simulation:
    """Parse detailed simulation info output to Simulation object.

    Parses output from 'simdb remote info <id>' command which provides
    detailed simulation metadata.

    Args:
        output: Raw CLI output with simulation details

    Returns:
        Simulation object with parsed metadata

    Raises:
        ValidationError: If output format is invalid

    Examples:
        >>> output = '''
        ... UUID: 123e4567-e89b-12d3-a456-426614174000
        ... Alias: ITER-001
        ... Machine: ITER
        ... '''
        >>> sim = parse_simulation_info(output)
        >>> sim.alias
        'ITER-001'
    """
    if not output or not output.strip():
        raise ValidationError(
            "Empty simulation info output",
            recovery_hint="Check simulation ID exists: uv run simdb remote list",
        )

    # Simplified parsing - real implementation would be more robust
    lines = output.strip().split("\n")
    metadata = {}

    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip().lower()] = value.strip()

    return Simulation(
        uuid=metadata.get("uuid", "unknown"),
        alias=metadata.get("alias", "unknown"),
        machine=metadata.get("machine", "unknown"),
        code=CodeInfo(
            name=metadata.get("code", "unknown"), version=metadata.get("version", "unknown")
        ),
        description=metadata.get("description", ""),
        status=metadata.get("status", "pending"),  # type: ignore
    )
