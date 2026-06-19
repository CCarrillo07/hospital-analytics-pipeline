"""
Oracle-specific SQL agent.

This module owns the Oracle SQL agent.
It uses only the Oracle prompt and Oracle SQL behavior.
"""

from functools import lru_cache
import logging

from agent.config import ALLOWED_SCHEMA, ALLOWED_TABLES
from agent.prompts.oracle import get_oracle_prompt
from agent.sql_agents.base import create_database_agent_executor


logger = logging.getLogger(__name__)


class OracleAgent:
    """
    Oracle database agent.

    This class keeps Oracle-specific SQL behavior isolated from
    PostgreSQL and SQL Server behavior.
    """

    def ask(self, question: str) -> str:
        """
        Ask the Oracle SQL agent a natural language question.
        """

        logger.info("Oracle agent received question: %s", question)

        agent_executor = get_oracle_agent_executor()

        response = agent_executor.invoke(
            {
                "input": question,
            }
        )

        answer = response.get("output", str(response))

        logger.info("Oracle agent answer: %s", answer)

        return answer


@lru_cache(maxsize=1)
def get_oracle_agent_executor():
    """
    Create and cache the Oracle SQL agent executor.
    """

    prefix = get_oracle_prompt(
        schema=ALLOWED_SCHEMA,
        tables=ALLOWED_TABLES,
    )

    return create_database_agent_executor(prefix=prefix)


@lru_cache(maxsize=1)
def get_oracle_agent() -> OracleAgent:
    """
    Create and cache the Oracle agent.
    """

    return OracleAgent()