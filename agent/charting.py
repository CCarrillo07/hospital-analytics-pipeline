"""
Chart generation helper for the DB AI Agent.

The SQL agent is good for natural language answers.
For charts, we separately ask the LLM to generate a chart-friendly SELECT query,
then we run that query and display the result with Plotly.
"""

import pandas as pd
import plotly.express as px
from sqlalchemy import text

from agent.llm import get_llm
from agent.database import get_engine
from agent.safety import clean_sql_response, is_safe_select_query
from agent.config import ALLOWED_SCHEMA, ALLOWED_TABLES


def generate_chart_sql(question: str) -> str:
    """
    Generate a chart-friendly SQL query from a natural language question.
    """

    llm = get_llm()

    prompt = f"""
You are a PostgreSQL expert.

Create one safe SELECT query for this user question:

{question}

Allowed schema:
{ALLOWED_SCHEMA}

Allowed tables:
{", ".join([f"{ALLOWED_SCHEMA}.{table}" for table in ALLOWED_TABLES])}

Rules:
- Return only SQL.
- Do not use markdown.
- Only use SELECT.
- Always use full table names with the schema prefix, for example {ALLOWED_SCHEMA}.appointments.
- Only query tables in the {ALLOWED_SCHEMA} schema.
- Do not use INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, or CALL.
- Use clear column aliases.
- For charts, return two columns when possible:
  1. A category or date column
  2. A numeric metric column
- Limit the result to 50 rows maximum.
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