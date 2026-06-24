"""
Chart generation helper for the DB AI Assistant.

For charts, we separately ask the LLM to generate a chart-friendly SELECT query,
then we run that query and display the result with Plotly.

This file is domain-generic.
Project-specific context should come from environment variables, not hardcoded
hospital, retail, or banking logic.
"""

import pandas as pd
import plotly.express as px
from sqlalchemy import text

from agent.llm import get_llm
from agent.database import get_engine
from agent.safety import clean_sql_response, is_safe_select_query
from agent.config import (
    AI_DB_DIALECT_NAME,
    ALLOWED_SCHEMA,
    ALLOWED_TABLES,
    EXCLUDED_SCHEMAS,
    AI_DB_RELATIONSHIPS,
    AI_DB_BUSINESS_RULES,
)


def get_allowed_tables_text() -> str:
    """
    Return a human-readable description of the tables available to the chart SQL generator.

    If ALLOWED_TABLES has values, the prompt lists those specific tables.
    If ALLOWED_TABLES is empty, the prompt tells the model that all tables
    in the configured schema are available.
    """

    if ALLOWED_TABLES:
        return ", ".join(
            f"{ALLOWED_SCHEMA}.{table}"
            for table in ALLOWED_TABLES
        )

    return f"All tables available in the {ALLOWED_SCHEMA} schema"


def get_excluded_schemas_text() -> str:
    """
    Return a human-readable description of schemas the assistant should avoid.
    """

    if not EXCLUDED_SCHEMAS:
        return "No additional schemas are excluded."

    return ", ".join(EXCLUDED_SCHEMAS)


def format_semicolon_list(value: str) -> str:
    """
    Convert a semicolon-separated string into a bullet list.
    """

    items = [
        item.strip()
        for item in value.split(";")
        if item.strip()
    ]

    return "\n".join(
        f"- {item}"
        for item in items
    )


def get_optional_domain_guidance_text() -> str:
    """
    Return optional database-specific guidance from environment variables.
    """

    sections = []

    if AI_DB_RELATIONSHIPS:
        sections.append(
            "Known relationships:\n"
            f"{format_semicolon_list(AI_DB_RELATIONSHIPS)}"
        )

    if AI_DB_BUSINESS_RULES:
        sections.append(
            "Business rules:\n"
            f"{format_semicolon_list(AI_DB_BUSINESS_RULES)}"
        )

    if not sections:
        return (
            "No additional business rules or relationships were provided. "
            "Use only the available schema and columns."
        )

    return "\n\n".join(sections)


def generate_chart_sql(question: str) -> str:
    """
    Generate a chart-friendly SQL query from a natural language question.
    """

    llm = get_llm()

    allowed_tables_text = get_allowed_tables_text()
    excluded_schemas_text = get_excluded_schemas_text()
    domain_guidance_text = get_optional_domain_guidance_text()

    prompt = f"""
You are a {AI_DB_DIALECT_NAME} expert.

Create one safe SELECT query for this user question:

{question}

Allowed schema:
{ALLOWED_SCHEMA}

Allowed tables:
{allowed_tables_text}

Excluded schemas:
{excluded_schemas_text}

Optional domain guidance:
{domain_guidance_text}

Rules:
- Return only SQL.
- Do not use markdown.
- Only use SELECT.
- Generate SQL using {AI_DB_DIALECT_NAME} syntax.
- Always use full table names with the schema prefix, for example {ALLOWED_SCHEMA}.table_name.
- Only query tables in the allowed schema: {ALLOWED_SCHEMA}.
- Do not query excluded schemas.
- Do not query system, catalog, or metadata tables.
- Do not use INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, MERGE, EXEC, CALL, COPY, GRANT, REVOKE, DECLARE, BEGIN, COMMIT, or ROLLBACK.
- Use clear column aliases.
- For charts, return two columns when possible:
  1. A category, label, or date column
  2. A numeric metric column
- Limit the result to 50 rows maximum using the correct row-limiting syntax for {AI_DB_DIALECT_NAME}.
- Do not assume specific column names exist.
- Do not invent relationships. Use explicit relationships from the optional guidance when provided.
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
        title=f"{y_column.replace('_', ' ').title()} by {x_column.replace('_', ' ').title()}",
    )

    fig.update_layout(
        xaxis_title=x_column.replace("_", " ").title(),
        yaxis_title=y_column.replace("_", " ").title(),
    )

    return fig