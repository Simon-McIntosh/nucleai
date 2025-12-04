"""Local DuckDB database management."""

from nucleai.db.manager import DuckDBManager, get_schema, init_db, upsert_simulations

__all__ = ["DuckDBManager", "get_schema", "init_db", "upsert_simulations"]

__agent_exposed__ = True
