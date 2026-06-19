"""
Shared SQL agent utilities.

This module contains reusable logic used by all database-specific SQL agents.

The database-specific agents are responsible for choosing the correct prompt.
This base module is responsible for:
- Creating the LangChain SQL toolkit
- Cleaning SQL before execution
- Normalizing schema tool input
- Creating the SQL agent executor
"""

import logging

from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_core.tools import Tool

from agent.llm import get_llm
from agent.database import get_sql_database
from agent.config import ALLOWED_SCHEMA
from agent.safety import clean_sql_response


logger = logging.getLogger(__name__)


class CleanSQLDatabaseToolkit(SQLDatabaseToolkit):
    """
    Custom SQL toolkit that improves tool descriptions and cleans SQL.

    This is not fallback logic.
    It only makes the SQL tools clearer and more robust.

    Important distinction:
    - sql_db_schema expects bare table names, such as patients or billing.
    - sql_db_query expects executable SQL, where schema-qualified table names
      should be used, such as harmonized.patients.
    """

    def get_tools(self):
        """
        Return SQL tools with clearer descriptions and cleaned SQL execution.
        """

        tools = super().get_tools()
        cleaned_tools = []

        for tool in tools:
            if tool.name == "sql_db_query":
                cleaned_tools.append(
                    Tool(
                        name="sql_db_query",
                        description=(
                            "Input to this tool is a complete and correct SQL SELECT query. "
                            "This tool executes the SQL query against the database and returns the real result. "
                            "Use this tool to answer count, total, sum, average, grouping, ranking, top, bottom, "
                            "per, by, highest, and lowest questions. "
                            f"For executable SQL, use schema-qualified table names such as {ALLOWED_SCHEMA}.patients. "
                            "The input must be plain SQL only. Markdown code fences are automatically removed."
                        ),
                        func=self._run_clean_query,
                    )
                )

            elif tool.name == "sql_db_schema":
                cleaned_tools.append(
                    Tool(
                        name="sql_db_schema",
                        description=(
                            "Input to this tool is one or more bare table names separated by commas. "
                            "Use this tool only to inspect table columns and structure. "
                            "Do not use schema-qualified names here. "
                            "Correct inputs: patients, appointments, billing. "
                            f"Incorrect inputs: {ALLOWED_SCHEMA}.patients, {ALLOWED_SCHEMA}.appointments, {ALLOWED_SCHEMA}.billing. "
                            "This tool does not return real aggregate results and must not be used as the final answer."
                        ),
                        func=self._run_schema_tool(tool),
                    )
                )

            elif tool.name == "sql_db_query_checker":
                cleaned_tools.append(
                    Tool(
                        name="sql_db_query_checker",
                        description=(
                            "Checks whether a SQL query is valid. "
                            "Do not use this tool unless a SQL query failed and needs to be checked."
                        ),
                        func=self._run_clean_query_checker(tool),
                    )
                )

            else:
                cleaned_tools.append(tool)

        return cleaned_tools

    def _run_clean_query(self, query: str) -> str:
        """
        Clean and execute a SQL query.
        """

        cleaned_query = clean_sql_response(query)

        logger.info("SQL query executed by agent:\n%s", cleaned_query)

        return self.db.run_no_throw(cleaned_query)

    @staticmethod
    def _run_schema_tool(original_tool):
        """
        Run the schema inspection tool.

        The model should pass bare table names only.

        This helper also normalizes accidental schema-qualified names,
        for example:
            harmonized.appointments -> appointments

        This is not fallback logic. It is only tool-input cleanup.
        """

        def _schema(table_names: str) -> str:
            cleaned_table_names = normalize_schema_tool_input(table_names)

            logger.info(
                "SQL schema tool input normalized from '%s' to '%s'",
                table_names,
                cleaned_table_names,
            )

            return original_tool.run(cleaned_table_names)

        return _schema

    @staticmethod
    def _run_clean_query_checker(original_tool):
        """
        Clean SQL before sending it to the query checker.
        """

        def _checker(query: str) -> str:
            cleaned_query = clean_sql_response(query)
            return original_tool.run(cleaned_query)

        return _checker


def normalize_schema_tool_input(table_names: str) -> str:
    """
    Normalize table names passed to sql_db_schema.

    LangChain's sql_db_schema tool expects bare table names.
    This function removes accidental schema prefixes.

    Examples:
        harmonized.patients -> patients
        harmonized.patients, harmonized.billing -> patients, billing
    """

    if not table_names:
        return table_names

    normalized_items = []

    raw_items = (
        table_names
        .replace("\n", ",")
        .replace(";", ",")
        .split(",")
    )

    for raw_item in raw_items:
        item = raw_item.strip()

        if not item:
            continue

        item = item.strip("`")
        item = item.strip('"')
        item = item.strip("[")
        item = item.strip("]")

        schema_prefix = f"{ALLOWED_SCHEMA}."

        if item.lower().startswith(schema_prefix.lower()):
            item = item[len(schema_prefix):]

        item = item.strip()
        item = item.strip("`")
        item = item.strip('"')
        item = item.strip("[")
        item = item.strip("]")

        if item:
            normalized_items.append(item)

    return ", ".join(normalized_items)


def create_database_agent_executor(prefix: str):
    """
    Create a LangChain SQL agent executor using a database-specific prompt.

    The prompt is passed by each database-specific agent.
    """

    llm = get_llm()
    db = get_sql_database()

    toolkit = CleanSQLDatabaseToolkit(
        db=db,
        llm=llm,
    )

    return create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        verbose=True,
        top_k=20,
        prefix=prefix,
        max_iterations=10,
        agent_executor_kwargs={
            "handle_parsing_errors": True,
        },
    )