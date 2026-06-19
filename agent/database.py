"""
Database configuration for the DB AI Agent.
"""

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from langchain_community.utilities import SQLDatabase

from agent.config import (
    AI_DB_HOST,
    AI_DB_PORT,
    AI_DB_NAME,
    AI_DB_USER,
    AI_DB_PASSWORD,
    ALLOWED_SCHEMA,
    ALLOWED_TABLES,
)


def get_ai_database_url() -> str:
    """
    Build the PostgreSQL connection URL for the AI agent.
    """

    if not AI_DB_NAME or not AI_DB_USER or not AI_DB_PASSWORD:
        raise ValueError(
            "Missing AI database environment variables. "
            "Please check AI_DB_NAME, AI_DB_USER, and AI_DB_PASSWORD."
        )

    return (
        f"postgresql+psycopg2://{AI_DB_USER}:{AI_DB_PASSWORD}"
        f"@{AI_DB_HOST}:{AI_DB_PORT}/{AI_DB_NAME}"
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

    The SQL agent only receives access to the harmonized schema tables.
    """

    return SQLDatabase.from_uri(
        get_ai_database_url(),
        schema=ALLOWED_SCHEMA,
        include_tables=ALLOWED_TABLES,
        sample_rows_in_table_info=0
    )