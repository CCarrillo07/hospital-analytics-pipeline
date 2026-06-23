"""
Database configuration for the DB AI Assistant.

This file creates a SQLAlchemy engine for the configured AI database.

Supported AI query databases:
- PostgreSQL
- Oracle
- SQL Server
"""

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from agent.config import (
    AI_DB_TYPE,
    AI_DB_DIALECT,
    AI_DB_HOST,
    AI_DB_PORT,
    AI_DB_NAME,
    AI_DB_USER,
    AI_DB_PASSWORD,
    AI_DB_DRIVER,
    AI_DB_ENCRYPT,
    AI_DB_TRUST_SERVER_CERTIFICATE,
)

from utils.db_url import build_database_url


def get_ai_database_url() -> str:
    """
    Build the database connection URL for the AI database assistant.
    """

    required_values = {
        "AI_DB_TYPE": AI_DB_TYPE,
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
        db_type=AI_DB_TYPE,
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
    Create and cache a SQLAlchemy engine for direct SQL execution.
    """

    return create_engine(get_ai_database_url())