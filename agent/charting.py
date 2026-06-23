"""
Chart generation helper for the DB AI Assistant.

For charts, we separately ask the LLM to generate a chart-friendly SELECT query,
then we run that query and display the result with Plotly.

Supported AI query databases:
- PostgreSQL
- Oracle
- SQL Server
"""

import pandas as pd
import plotly.express as px
from sqlalchemy import text

from agent.llm import get_llm
from agent.database import get_engine
from agent.safety import clean_sql_response, is_safe_select_query
from agent.config import (
    AI_DB_TYPE,
    AI_DB_DIALECT_NAME,
    ALLOWED_SCHEMA,
    ALLOWED_TABLES,
)
from agent.sql_dialects import get_dialect_config


DIALECT_CONFIG = get_dialect_config(
    db_type=AI_DB_TYPE,
    display_name=AI_DB_DIALECT_NAME,
)


def table_ref(table_name: str) -> str:
    """
    Build a schema-qualified table reference for the active dialect.
    """

    return DIALECT_CONFIG.format_table_reference(
        ALLOWED_SCHEMA,
        table_name,
    )


def get_allowed_tables_text() -> str:
    """
    Return a human-readable description of the tables available to the chart SQL generator.
    """

    if ALLOWED_TABLES:
        return ", ".join(
            table_ref(table)
            for table in ALLOWED_TABLES
        )

    return (
        f"All tables available in the "
        f"{DIALECT_CONFIG.format_schema_name(ALLOWED_SCHEMA)} schema"
    )


def generate_chart_sql(question: str) -> str:
    """
    Generate a chart-friendly SQL query from a natural language question.
    """

    llm = get_llm()

    allowed_tables_text = get_allowed_tables_text()

    prompt = f"""
You are a {DIALECT_CONFIG.display_name} expert.

Create one safe SELECT query for this user question:

{question}

Allowed schema:
{DIALECT_CONFIG.format_schema_name(ALLOWED_SCHEMA)}

Allowed tables:
{allowed_tables_text}

Rules:
- Return only SQL.
- Do not use markdown.
- Only use SELECT.
- Generate SQL using {DIALECT_CONFIG.display_name} syntax.
- Always use full table names with the schema prefix, for example {DIALECT_CONFIG.table_reference_example}.
- Only query tables in the configured allowed schema.
- Do not query raw tables.
- Do not query automation tables.
- Do not query analytics tables.
- Do not query system, catalog, or metadata tables.
- Do not use INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, MERGE, EXEC, CALL, COPY, GRANT, REVOKE, DECLARE, BEGIN, COMMIT, or ROLLBACK.
- Use clear column aliases.
- For charts, return two columns when possible:
  1. A category or date column
  2. A numeric metric column
- Limit the result to 50 rows maximum.
- {DIALECT_CONFIG.row_limit_instruction}
- {DIALECT_CONFIG.concat_instruction}
"""

    response = llm.invoke(prompt)

    return clean_sql_response(response.content)


def run_chart_sql(sql_query: str) -> pd.DataFrame:
    """
    Run a safe SQL query and return the result as a DataFrame.
    """

    if not is_safe_select_query(sql_query):
        raise ValueError("The generated SQL did not pass safety checks.")

    engine = get_engine()

    with engine.connect() as conn:
        return pd.read_sql(text(sql_query), conn)


def create_chart(df: pd.DataFrame):
    """
    Create a simple Plotly chart from a DataFrame.

    This function assumes the first column is the category/date
    and the second column is the numeric metric.
    """

    if df.empty:
        return None

    if len(df.columns) < 2:
        return None

    x_column = df.columns[0]
    y_column = df.columns[1]

    if not pd.api.types.is_numeric_dtype(df[y_column]):
        return None

    fig = px.bar(
        df,
        x=x_column,
        y=y_column,
        text=y_column,
        title=f"{y_column.replace('_', ' ').title()} by {x_column.replace('_', ' ').title()}"
    )

    fig.update_layout(
        xaxis_title=x_column.replace("_", " ").title(),
        yaxis_title=y_column.replace("_", " ").title()
    )

    return fig