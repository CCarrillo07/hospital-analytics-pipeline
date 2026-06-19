"""
Database agent router.

This module selects the correct database-specific SQL agent based on AI_DB_TYPE.

The router does not write SQL.
The router does not inspect schemas.
The router only decides which specialized SQL agent should handle the question.
"""

from agent.config import AI_DB_TYPE
from agent.sql_agents.postgresql_agent import get_postgresql_agent
from agent.sql_agents.oracle_agent import get_oracle_agent
from agent.sql_agents.sqlserver_agent import get_sqlserver_agent


def get_database_agent():
    """
    Return the correct database-specific SQL agent.

    Supported AI_DB_TYPE values:
    - postgresql
    - oracle
    - sqlserver
    - mssql
    - sql_server
    """

    normalized_db_type = AI_DB_TYPE.lower().strip()

    if normalized_db_type == "postgresql":
        return get_postgresql_agent()

    if normalized_db_type == "oracle":
        return get_oracle_agent()

    if normalized_db_type in ("sqlserver", "mssql", "sql_server"):
        return get_sqlserver_agent()

    raise ValueError(
        f"Unsupported AI_DB_TYPE: {AI_DB_TYPE}. "
        "Supported values are: postgresql, oracle, sqlserver."
    )