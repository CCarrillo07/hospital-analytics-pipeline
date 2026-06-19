"""
Database-specific SQL agents package.

Each database engine gets its own specialized SQL agent.
"""

from agent.sql_agents.router import get_database_agent

__all__ = [
    "get_database_agent",
]