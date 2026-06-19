"""
SQL Server-specific SQL agent.

This module owns the SQL Server SQL agent.
It uses only the SQL Server prompt and SQL Server SQL behavior.
"""

from functools import lru_cache
import logging

from agent.config import ALLOWED_SCHEMA, ALLOWED_TABLES
from agent.prompts.sqlserver import get_sqlserver_prompt
from agent.sql_agents.base import create_database_agent_executor


logger = logging.getLogger(__name__)


class SQLServerAgent:
    """
    SQL Server database agent.

    This class keeps SQL Server-specific SQL behavior isolated from
    PostgreSQL and Oracle behavior.
    """

    def ask(self, question: str) -> str:
        """
        Ask the SQL Server SQL agent a natural language question.
        """

        logger.info("SQL Server agent received question: %s", question)

        agent_executor = get_sqlserver_agent_executor()

        response = agent_executor.invoke(
            {
                "input": question,
            }
        )

        answer = response.get("output", str(response))

        logger.info("SQL Server agent answer: %s", answer)

        return answer


@lru_cache(maxsize=1)
def get_sqlserver_agent_executor():
    """
    Create and cache the SQL Server SQL agent executor.
    """

    prefix = get_sqlserver_prompt(
        schema=ALLOWED_SCHEMA,
        tables=ALLOWED_TABLES,
    )

    return create_database_agent_executor(prefix=prefix)


@lru_cache(maxsize=1)
def get_sqlserver_agent() -> SQLServerAgent:
    """
    Create and cache the SQL Server agent.
    """

    return SQLServerAgent()