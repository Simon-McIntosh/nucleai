"""DataFrame access for SimDB using local DuckDB.

Provides functions to query the local simulation database using SQL
and return results as pandas DataFrames.

Functions:
    query_sql: Execute SQL query and return DataFrame
"""

import pandas as pd


def query_sql(query: str) -> pd.DataFrame:
    """Execute SQL query against local SimDB cache.

    Requires running `nucleai build-db` first to populate the cache.

    Args:
        query: SQL query string

    Returns:
        pandas DataFrame with query results

    Examples:
        >>> df = query_sql("SELECT * FROM simulations WHERE machine='ITER'")
        >>> print(df.head())

        >>> # Query nested JSON metadata
        >>> df = query_sql("SELECT alias, json_extract(metadata, '$.composition.deuterium') as D FROM simulations")
    """
    from nucleai.db.manager import DuckDBManager

    manager = DuckDBManager()
    conn = manager.get_connection()

    try:
        return conn.execute(query).df()
    finally:
        conn.close()
