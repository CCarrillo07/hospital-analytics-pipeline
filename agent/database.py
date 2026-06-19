"""
Database configuration for the DB AI Agent.
"""

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from langchain_community.utilities import SQLDatabase

from agent.config import (
    AI_DB_DIALECT,
    AI_DB_HOST,
    AI_DB_PORT,
    AI_DB_NAME,
    AI_DB_USER,
    AI_DB_PASSWORD,
    AI_DB_DRIVER,
    AI_DB_ENCRYPT,
    AI_DB_TRUST_SERVER_CERTIFICATE,
    ALLOWED_SCHEMA,
    ALLOWED_TABLES,
)

from utils.db_url import build_database_url


def get_ai_database_url() -> str:
    """
    Build the database connection URL for the AI agent.
    """

    required_values = {
        "AI_DB_DIALECT": AI_DB_DIALECT,
        "AI_DB_HOST": AI_DB_HOST,
        "AI_DB_PORT": AI_DB_PORT,
        "AI_DB_NAME": AI_DB_NAME,
        "AI_DB_USER": AI_DB_USER,
        "AI_DB_PASSWORD": AI_DB_PASSWORD,
    }

    missing_values = [
        key for key, value in required_values.items()
        if not value
    ]

    if missing_values:
        raise ValueError(
            "Missing AI database environment variables: "
            + ", ".join(missing_values)
        )

    return build_database_url(
        dialect=AI_DB_DIALECT,
        user=AI_DB_USER,
        password=AI_DB_PASSWORD,
        host=AI_DB_HOST,
        port=AI_DB_PORT,
        database=AI_DB_NAME,
        driver=AI_DB_DRIVER,
        encrypt=AI_DB_ENCRYPT,
        trust_server_certificate=AI_DB_TRUST_SERVER_CERTIFICATE,
    )


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """
    Create a SQLAlchemy engine for direct SQL execution.
    """

    return create_engine(get_ai_database_url())


@lru_cache(maxsize=1)
def get_sql_database() -> SQLDatabase:
    """
    Create the LangChain SQLDatabase object.

    If ALLOWED_TABLES is populated, the SQL agent only receives access
    to those configured tables.

    If ALLOWED_TABLES is empty, the SQL agent receives access to all
    tables in the configured schema.

    Important:
    sample_rows_in_table_info is set to 0 because local models may confuse
    sample rows with complete table results and answer aggregation questions
    without running SQL.
    """

    return SQLDatabase.from_uri(
        get_ai_database_url(),
        schema=ALLOWED_SCHEMA,
        include_tables=ALLOWED_TABLES if ALLOWED_TABLES else None,
        sample_rows_in_table_info=0
    )