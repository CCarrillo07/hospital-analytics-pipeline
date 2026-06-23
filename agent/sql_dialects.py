"""
SQL dialect helpers for the controlled AI Database Assistant.

This module isolates differences between PostgreSQL, Oracle, and SQL Server.

The goal is to keep agent/sql_agent.py focused on the controlled pipeline,
while this file handles database-specific syntax and metadata queries.
"""

from dataclasses import dataclass
from sqlalchemy import text


@dataclass(frozen=True)
class SQLDialectConfig:
    """
    Database-specific SQL behavior used by the AI Database Assistant.
    """

    db_type: str
    display_name: str
    row_limit_instruction: str
    concat_instruction: str
    table_reference_example: str
    metadata_table_case: str

    def format_schema_name(self, schema_name: str) -> str:
        """
        Format schema name for prompts and SQL generation.
        """

        if self.db_type == "oracle":
            return schema_name.upper()

        return schema_name

    def format_table_name(self, table_name: str) -> str:
        """
        Format table name for prompts and SQL generation.
        """

        if self.db_type == "oracle":
            return table_name.upper()

        return table_name

    def format_table_reference(
        self,
        schema_name: str,
        table_name: str,
    ) -> str:
        """
        Build a schema-qualified table reference.
        """

        return (
            f"{self.format_schema_name(schema_name)}."
            f"{self.format_table_name(table_name)}"
        )


def normalize_db_type(db_type: str) -> str:
    """
    Normalize database type aliases into supported internal names.
    """

    normalized = db_type.strip().lower()

    aliases = {
        "postgres": "postgresql",
        "postgresql": "postgresql",
        "pg": "postgresql",
        "oracle": "oracle",
        "oracledb": "oracle",
        "sqlserver": "sqlserver",
        "mssql": "sqlserver",
        "sql_server": "sqlserver",
        "microsoft_sql_server": "sqlserver",
    }

    if normalized not in aliases:
        raise ValueError(
            f"Unsupported AI_DB_TYPE '{db_type}'. "
            "Supported values are: postgresql, oracle, sqlserver."
        )

    return aliases[normalized]


def get_dialect_config(
    db_type: str,
    display_name: str,
) -> SQLDialectConfig:
    """
    Return the SQL dialect configuration for the selected database.
    """

    normalized_db_type = normalize_db_type(db_type)

    if normalized_db_type == "postgresql":
        return SQLDialectConfig(
            db_type="postgresql",
            display_name=display_name or "PostgreSQL",
            row_limit_instruction=(
                "Use LIMIT n at the end of the query when limiting rows."
            ),
            concat_instruction=(
                "Use first_name || ' ' || last_name to concatenate names."
            ),
            table_reference_example="harmonized.patients",
            metadata_table_case="lower",
        )

    if normalized_db_type == "oracle":
        return SQLDialectConfig(
            db_type="oracle",
            display_name=display_name or "Oracle",
            row_limit_instruction=(
                "Use FETCH FIRST n ROWS ONLY at the end of the query when limiting rows."
            ),
            concat_instruction=(
                "Use first_name || ' ' || last_name to concatenate names."
            ),
            table_reference_example="HARMONIZED.PATIENTS",
            metadata_table_case="upper",
        )

    if normalized_db_type == "sqlserver":
        return SQLDialectConfig(
            db_type="sqlserver",
            display_name=display_name or "SQL Server",
            row_limit_instruction=(
                "Use TOP (n) immediately after SELECT when limiting rows."
            ),
            concat_instruction=(
                "Use CONCAT(first_name, ' ', last_name) to concatenate names."
            ),
            table_reference_example="harmonized.patients",
            metadata_table_case="lower",
        )

    raise ValueError(
        f"Unsupported database type: {db_type}"
    )


def get_schema_metadata_query(db_type: str):
    """
    Return a SQLAlchemy text query that reads table and column metadata.

    The returned query must output:
    - table_name
    - column_name
    - data_type
    - ordinal_position
    """

    normalized_db_type = normalize_db_type(db_type)

    if normalized_db_type in {"postgresql", "sqlserver"}:
        return text(
            """
            SELECT
                table_name AS table_name,
                column_name AS column_name,
                data_type AS data_type,
                ordinal_position AS ordinal_position
            FROM information_schema.columns
            WHERE table_schema = :schema_name
            ORDER BY table_name, ordinal_position
            """
        )

    if normalized_db_type == "oracle":
        return text(
            """
            SELECT
                table_name AS table_name,
                column_name AS column_name,
                data_type AS data_type,
                column_id AS ordinal_position
            FROM all_tab_columns
            WHERE owner = UPPER(:schema_name)
            ORDER BY table_name, column_id
            """
        )

    raise ValueError(
        f"Unsupported database type: {db_type}"
    )