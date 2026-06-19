"""
Public SQL agent entry point.

This module is intentionally thin.

The Streamlit app imports ask_database from this file.
This file delegates the question to the correct database-specific SQL agent
using the database router.

Architecture:
- agent_app.py calls ask_database()
- ask_database() calls the router
- the router selects PostgreSQL, Oracle, or SQL Server agent
- the selected database-specific agent answers the question
"""

import logging

from agent.sql_agents.router import get_database_agent


logger = logging.getLogger(__name__)


def ask_database(question: str) -> str:
    """
    Ask the configured database-specific SQL agent a natural language question.
    """

    logger.info("User question: %s", question)

    database_agent = get_database_agent()

    answer = database_agent.ask(question)

    logger.info("Agent answer: %s", answer)

    return answer