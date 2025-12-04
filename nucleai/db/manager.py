"""DuckDB manager for local simulation cache.

Handles connection to local DuckDB file and provides methods to sync
SimDB data to a local SQL table for advanced querying.

Classes:
    DuckDBManager: Manages DuckDB connection and operations

Functions:
    init_db: Initialize database schema
    upsert_simulations: Insert or update simulation records
    get_schema: Get table schema for introspection
"""

import duckdb

from nucleai.core.config import get_settings
from nucleai.simdb.models import SimulationSummary


class DuckDBManager:
    """Manages connection to local DuckDB database.

    Attributes:
        db_path: Path to DuckDB file
    """

    def __init__(self) -> None:
        """Initialize DuckDB manager."""
        settings = get_settings()
        self.db_path = settings.duckdb_path

        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get DuckDB connection.

        Returns:
            DuckDB connection object
        """
        return duckdb.connect(str(self.db_path))


def init_db() -> None:
    """Initialize database schema.

    Creates 'simulations' table if it doesn't exist.
    """
    manager = DuckDBManager()
    conn = manager.get_connection()

    try:
        # Create table with JSON support for nested metadata
        conn.execute("""
            CREATE TABLE IF NOT EXISTS simulations (
                uuid VARCHAR PRIMARY KEY,
                alias VARCHAR,
                machine VARCHAR,
                code_name VARCHAR,
                code_version VARCHAR,
                description VARCHAR,
                status VARCHAR,
                author_email VARCHAR,
                datetime TIMESTAMP,
                metadata JSON
            )
        """)
    finally:
        conn.close()


def upsert_simulations(sims: list[SimulationSummary]) -> None:
    """Insert or update simulation records.

    Args:
        sims: List of SimulationSummary objects to upsert
    """
    if not sims:
        return

    manager = DuckDBManager()
    conn = manager.get_connection()

    try:
        # Convert to list of tuples for bulk insertion
        data = []
        for sim in sims:
            # Serialize metadata to JSON string
            metadata_json = sim.metadata.model_dump_json() if sim.metadata else "{}"

            data.append(
                (
                    sim.uuid,
                    sim.alias,
                    sim.machine,
                    sim.code.name,
                    sim.code.version,
                    sim.description,
                    sim.status,
                    sim.author_email,
                    sim.metadata.datetime if sim.metadata else None,
                    metadata_json,
                )
            )

        # Create temporary table for upsert
        conn.execute("""
            CREATE TEMPORARY TABLE IF NOT EXISTS temp_sims (
                uuid VARCHAR,
                alias VARCHAR,
                machine VARCHAR,
                code_name VARCHAR,
                code_version VARCHAR,
                description VARCHAR,
                status VARCHAR,
                author_email VARCHAR,
                datetime TIMESTAMP,
                metadata JSON
            )
        """)

        # Insert into temp table
        conn.executemany("INSERT INTO temp_sims VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)

        # Upsert from temp table to main table
        conn.execute("""
            INSERT INTO simulations
            SELECT * FROM temp_sims
            ON CONFLICT (uuid) DO UPDATE SET
                alias = EXCLUDED.alias,
                machine = EXCLUDED.machine,
                code_name = EXCLUDED.code_name,
                code_version = EXCLUDED.code_version,
                description = EXCLUDED.description,
                status = EXCLUDED.status,
                author_email = EXCLUDED.author_email,
                datetime = EXCLUDED.datetime,
                metadata = EXCLUDED.metadata
        """)

        # Clean up
        conn.execute("DROP TABLE temp_sims")

    finally:
        conn.close()


def get_schema() -> dict[str, str]:
    """Get table schema for introspection.

    Returns:
        Dictionary mapping column names to types
    """
    manager = DuckDBManager()
    conn = manager.get_connection()

    try:
        # Check if table exists
        tables = conn.execute("SHOW TABLES").fetchall()
        if not tables or ("simulations",) not in tables:
            return {}

        # Get schema info
        schema_info = conn.execute("DESCRIBE simulations").fetchall()
        return {row[0]: row[1] for row in schema_info}

    finally:
        conn.close()
