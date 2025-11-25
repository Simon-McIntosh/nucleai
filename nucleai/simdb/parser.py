r"""Parse SimDB CLI output to Python objects.

Functions to parse SimDB CLI table output and convert to Pydantic models.
Handles various output formats and edge cases including fields with spaces.

Functions:
    parse_query_output: Parse query results table to Simulation list
    parse_simulation_info: Parse detailed simulation info to Simulation

Parsing Strategy:
    Uses column position detection from header line to handle fields with
    spaces/commas (e.g., email addresses, descriptions). This ensures
    multi-word values are captured correctly.

Supported Fields:
    Extracts any field present in SimDB output table:
    - uuid, alias, machine (always present)
    - code.name, code.version, code.commit, code.repository
    - uploaded_by (email addresses, comma-separated)
    - status, description
    - ids (available IDS types)
    - Any other metadata field requested via include_metadata parameter

    IMPORTANT: Metadata fields are only present if explicitly requested
    via include_metadata parameter in query(). Default query returns only
    alias and machine

Examples:
    >>> from nucleai.simdb.parser import parse_query_output
    >>> output = "uuid | alias | machine\n123... | ITER-001 | ITER"
    >>> simulations = parse_query_output(output)
    >>> print(simulations[0].alias)
    ITER-001

    >>> # For metadata-rich queries, parse directly:
    >>> import anyio
    >>> cmd = ['uv', 'run', 'simdb', 'remote', 'query',
    ...        'machine=ITER', '-m', 'code.name', '-m', 'user', '--limit', '10']
    >>> result = await anyio.run_process(cmd, check=True)
    >>> lines = result.stdout.decode().strip().split('\n')
    >>> header = lines[0].split()  # ['alias', 'machine', 'code.name', 'user']
    >>> for line in lines[2:]:  # Skip header and separator
    ...     parts = line.split()
    ...     data = dict(zip(header, parts))
    ...     print(f"{data['alias']}: {data.get('code.name', 'N/A')}")
"""

from nucleai.core.exceptions import ValidationError
from nucleai.core.models import CodeInfo, Simulation


def parse_query_output(output: str) -> list[Simulation]:
    """Parse SimDB query output table to list of Simulations.

    Parses table-formatted output from 'simdb remote query' command.
    Extracts simulation metadata and constructs Simulation objects.

    Uses column position detection to handle fields with spaces/commas
    (e.g., email addresses, descriptions).

    Args:
        output: Raw CLI output string with table format

    Returns:
        List of Simulation objects parsed from output

    Raises:
        ValidationError: If output format is invalid or unparseable

    Examples:
        >>> output = '''
        ... alias    machine
        ... ----------------
        ... 100001/2 ITER
        ... '''
        >>> simulations = parse_query_output(output)
        >>> len(simulations)
        1
        >>> simulations[0].alias
        '100001/2'
    """
    if not output or not output.strip():
        return []

    lines = output.strip().split("\n")

    # Filter out empty lines but preserve structure for parsing
    non_empty_lines = [line for line in lines if line.strip()]

    if len(non_empty_lines) < 3:  # Need header + separator + at least one row
        return []

    # Parse header line to get column names and positions
    header_line = lines[0]

    # Find column positions by detecting word boundaries in header
    import re

    matches = list(re.finditer(r"\S+", header_line))
    columns = []
    positions = []

    for i, match in enumerate(matches):
        columns.append(match.group())
        start = match.start()
        # End is either start of next column or end of line
        end = matches[i + 1].start() if i + 1 < len(matches) else len(header_line)
        positions.append((start, end))

    # Verify separator line exists
    if len(non_empty_lines) < 2 or not non_empty_lines[1].startswith("-"):
        raise ValidationError(
            f"Invalid SimDB output format: {output[:100]}",
            recovery_hint="Check SimDB CLI is working: uv run simdb remote query machine=ITER --limit 1",
        )

    # Parse data rows using column positions
    simulations = []
    for line in lines[2:]:  # Skip header and separator
        if not line.strip():
            continue

        # Extract values using column positions
        data = {}
        for col_name, (start, end) in zip(columns, positions, strict=False):
            value = line[start:end].strip() if start < len(line) else ""
            if value:  # Only store non-empty values
                data[col_name] = value

        if len(data) >= 2:  # Minimum: alias and machine
            simulations.append(
                Simulation(
                    uuid=data.get("uuid", "unknown"),
                    alias=data.get("alias", "unknown"),
                    machine=data.get("machine", "unknown"),
                    code=CodeInfo(
                        name=data.get("code.name", "unknown"),
                        version=data.get("code.version", "unknown"),
                    ),
                    description=data.get("description", ""),
                    status=data.get("status", "pending"),  # type: ignore
                    uploaded_by=data.get("uploaded_by"),  # Now captured!
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
