"""
PostgreSQL database configuration for the DB AI Assistant.
"""

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from agent.config import (
    AI_DB_DIALECT,
    AI_DB_HOST,
    AI_DB_PORT,
    AI_DB_NAME,
    AI_DB_USER,
    AI_DB_PASSWORD,
)

from utils.db_url import build_database_url


def get_ai_database_url() -> str:
    """
    Build the PostgreSQL connection URL for the AI database assistant.
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
    )


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """
    Create and cache a SQLAlchemy engine for direct PostgreSQL execution.
    """

    return create_engine(get_ai_database_url())