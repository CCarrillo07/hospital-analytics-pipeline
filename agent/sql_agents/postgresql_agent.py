"""
PostgreSQL-specific SQL agent.

This module owns the PostgreSQL SQL agent.
It uses only the PostgreSQL prompt and PostgreSQL SQL behavior.
"""

from functools import lru_cache
import logging

from agent.config import ALLOWED_SCHEMA, ALLOWED_TABLES
from agent.prompts.postgresql import get_postgresql_prompt
from agent.sql_agents.base import create_database_agent_executor


logger = logging.getLogger(__name__)


class PostgreSQLAgent:
    """
    PostgreSQL database agent.

    This class keeps PostgreSQL-specific SQL behavior isolated from
    Oracle and SQL Server behavior.
    """

    def ask(self, question: str) -> str:
        """
        Ask the PostgreSQL SQL agent a natural language question.
        """

        logger.info("PostgreSQL agent received question: %s", question)

        agent_executor = get_postgresql_agent_executor()

        response = agent_executor.invoke(
            {
                "input": question,
            }
        )

        answer = response.get("output", str(response))

        logger.info("PostgreSQL agent answer: %s", answer)

        return answer


@lru_cache(maxsize=1)
def get_postgresql_agent_executor():
    """
    Create and cache the PostgreSQL SQL agent executor.
    """

    prefix = get_postgresql_prompt(
        schema=ALLOWED_SCHEMA,
        tables=ALLOWED_TABLES,
    )

    return create_database_agent_executor(prefix=prefix)


@lru_cache(maxsize=1)
def get_postgresql_agent() -> PostgreSQLAgent:
    """
    Create and cache the PostgreSQL agent.
    """

    return PostgreSQLAgent()