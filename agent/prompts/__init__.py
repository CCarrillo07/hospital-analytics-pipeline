"""
Prompt router for the SQL Agent.

This module selects one full prompt based on the configured database type.

Important:
- We do not build the final prompt by mixing a generic base prompt
  with a small dialect prompt.
- Each database engine gets its own full prompt.
"""

from agent.prompts.postgresql import get_postgresql_prompt
from agent.prompts.oracle import get_oracle_prompt
from agent.prompts.sqlserver import get_sqlserver_prompt


def get_sql_agent_prefix(
    db_type: str,
    dialect_name: str,
    schema: str,
    tables: list[str],
) -> str:
    """
    Return the full SQL agent prompt for the configured database type.
    """

    normalized_db_type = db_type.lower().strip()

    if normalized_db_type == "postgresql":
        return get_postgresql_prompt(
            schema=schema,
            tables=tables,
        )

    if normalized_db_type == "oracle":
        return get_oracle_prompt(
            schema=schema,
            tables=tables,
        )

    if normalized_db_type in ("sqlserver", "mssql", "sql_server"):
        return get_sqlserver_prompt(
            schema=schema,
            tables=tables,
        )

    raise ValueError(
        f"Unsupported AI_DB_TYPE: {db_type}. "
        f"Supported values are: postgresql, oracle, sqlserver. "
        f"Received dialect name: {dialect_name}"
    )