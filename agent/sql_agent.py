"""
Controlled SQL pipeline entry point.

This module uses a deterministic pipeline:

1. Read database schema context.
2. Ask the LLM to generate one SQL SELECT query.
3. Validate the generated SQL in Python.
4. Execute the SQL in Python.
5. Ask the LLM to summarize the real SQL result.
6. Validate the final answer.

The code is intentionally domain-generic.
Project-specific guidance such as relationships or business rules should come
from environment variables, not hardcoded hospital, retail, or banking logic.
"""

import logging
from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from agent.config import (
    AI_DB_DIALECT_NAME,
    ALLOWED_SCHEMA,
    ALLOWED_TABLES,
    EXCLUDED_SCHEMAS,
    AI_DB_RELATIONSHIPS,
    AI_DB_BUSINESS_RULES,
)
from agent.database import get_engine
from agent.llm import get_llm
from agent.safety import clean_sql_response, is_safe_select_query


logger = logging.getLogger(__name__)


# ============================================================
# Public entry point
# ============================================================

def ask_database(question: str) -> str:
    """
    Answer a natural language question using a controlled SQL pipeline.

    The LLM generates SQL, but Python validates and executes it.
    The LLM does not control the database execution flow.
    """

    logger.info("User question: %s", question)
    logger.info("AI database dialect: %s", AI_DB_DIALECT_NAME)
    logger.info("Allowed schema: %s", ALLOWED_SCHEMA)

    schema_context = get_schema_context()

    sql_query = generate_sql(
        question=question,
        schema_context=schema_context,
    )

    logger.info("Generated SQL:\n%s", sql_query)

    if sql_query == "NO_SQL":
        return (
            "I could not create a safe SQL query for that question using the "
            "available tables."
        )

    if not is_safe_select_query(sql_query):
        logger.warning("Generated SQL failed safety validation:\n%s", sql_query)

        sql_query = retry_generate_sql(
            question=question,
            schema_context=schema_context,
            previous_sql=sql_query,
            error_message="The generated SQL failed safety validation.",
        )

        logger.info("Regenerated SQL after safety failure:\n%s", sql_query)

        if sql_query == "NO_SQL" or not is_safe_select_query(sql_query):
            return (
                "I could not generate a safe SQL query for that question. "
                "Please rephrase the question or ask about the available tables."
            )

    try:
        result_df = execute_sql(sql_query)

    except Exception as exc:
        logger.exception("SQL execution failed.")

        sql_query = retry_generate_sql(
            question=question,
            schema_context=schema_context,
            previous_sql=sql_query,
            error_message=str(exc),
        )

        logger.info("Regenerated SQL after execution failure:\n%s", sql_query)

        if sql_query == "NO_SQL" or not is_safe_select_query(sql_query):
            return (
                "I could not generate a valid SQL query after the first query failed."
            )

        try:
            result_df = execute_sql(sql_query)

        except Exception:
            logger.exception("Retried SQL execution failed.")
            return (
                "I generated a SQL query, but it failed when executed. "
                "Please check the table structure, database dialect, or rephrase the question."
            )

    answer = summarize_result(
        question=question,
        sql_query=sql_query,
        result_df=result_df,
    )

    if answer_looks_invalid(answer):
        logger.warning("LLM summary looked invalid. Returning deterministic fallback.")

        return build_fallback_answer(
            result_df=result_df,
        )

    logger.info("Final answer: %s", answer)

    return answer


# ============================================================
# Schema context
# ============================================================

def get_schema_context() -> str:
    """
    Read table and column metadata from information_schema.

    This gives the LLM the real available columns without using an
    autonomous SQL Agent schema tool.
    """

    engine = get_engine()

    query = text(
        """
        SELECT
            table_name,
            column_name,
            data_type,
            ordinal_position
        FROM information_schema.columns
        WHERE table_schema = :schema_name
        ORDER BY table_name, ordinal_position;
        """
    )

    with engine.connect() as conn:
        schema_df = pd.read_sql(
            query,
            conn,
            params={
                "schema_name": ALLOWED_SCHEMA,
            },
        )

    if ALLOWED_TABLES:
        allowed_tables_lower = {
            table.lower()
            for table in ALLOWED_TABLES
        }

        schema_df = schema_df[
            schema_df["table_name"].str.lower().isin(allowed_tables_lower)
        ]

    if schema_df.empty:
        raise ValueError(
            f"No schema metadata found for schema '{ALLOWED_SCHEMA}'."
        )

    lines = []

    for table_name, table_df in schema_df.groupby("table_name"):
        lines.append(f"Table: {ALLOWED_SCHEMA}.{table_name}")

        table_df = table_df.sort_values("ordinal_position")

        for _, row in table_df.iterrows():
            lines.append(
                f"- {row['column_name']} ({row['data_type']})"
            )

        lines.append("")

    domain_guidance = get_optional_domain_guidance_text()

    return "\n".join(lines).strip() + "\n\n" + domain_guidance


def get_optional_domain_guidance_text() -> str:
    """
    Return optional database-specific guidance from environment variables.

    This keeps the assistant reusable across domains such as:
    - hospital
    - retail
    - banking
    - logistics
    - finance
    - education

    The code stays generic.
    The .env file provides optional project-specific context.
    """

    sections = []

    if AI_DB_RELATIONSHIPS:
        relationships = format_semicolon_list(AI_DB_RELATIONSHIPS)

        sections.append(
            "Known relationships:\n"
            f"{relationships}\n\n"
            "Relationship guidance:\n"
            "- If relationships use unqualified table names, treat them as tables in the allowed schema.\n"
            "- Do not invent relationships that are not supported by the schema or the provided guidance."
        )

    if AI_DB_BUSINESS_RULES:
        business_rules = format_semicolon_list(AI_DB_BUSINESS_RULES)

        sections.append(
            "Business rules:\n"
            f"{business_rules}"
        )

    if not sections:
        return (
            "Optional domain guidance:\n"
            "- No additional business rules or relationships were provided.\n"
            "- Use only the available schema and columns to infer safe SQL.\n"
            "- Do not invent relationships."
        )

    return "\n\n".join(sections)


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


def get_allowed_tables_text() -> str:
    """
    Return a human-readable description of allowed tables.
    """

    if ALLOWED_TABLES:
        return ", ".join(
            f"{ALLOWED_SCHEMA}.{table}"
            for table in ALLOWED_TABLES
        )

    return f"All tables in the {ALLOWED_SCHEMA} schema"


def get_excluded_schemas_text() -> str:
    """
    Return a human-readable description of schemas the assistant should avoid.
    """

    if not EXCLUDED_SCHEMAS:
        return "No additional schemas are excluded."

    return ", ".join(EXCLUDED_SCHEMAS)


# ============================================================
# SQL generation
# ============================================================

def generate_sql(
    question: str,
    schema_context: str,
) -> str:
    """
    Ask the LLM to generate one SQL SELECT query.
    """

    llm = get_llm()

    prompt = build_sql_generation_prompt(
        question=question,
        schema_context=schema_context,
    )

    response = llm.invoke(prompt)

    sql_query = clean_sql_response(response.content)

    return normalize_generated_sql(sql_query)


def retry_generate_sql(
    question: str,
    schema_context: str,
    previous_sql: str,
    error_message: str,
) -> str:
    """
    Ask the LLM to regenerate SQL after validation or execution failed.
    """

    llm = get_llm()

    prompt = f"""
You previously generated a SQL query that failed.

User question:
{question}

Previous SQL:
{previous_sql}

Error or validation problem:
{error_message}

Database dialect:
{AI_DB_DIALECT_NAME}

Available schema:
{schema_context}

Regenerate one corrected SQL query.

Rules:
- Return only SQL.
- Do not use markdown.
- Do not explain the query.
- Only use SELECT.
- Use {AI_DB_DIALECT_NAME} syntax.
- Always use schema-qualified table names.
- Only query tables in the allowed schema: {ALLOWED_SCHEMA}.
- Allowed tables: {get_allowed_tables_text()}.
- Do not query these schemas: {get_excluded_schemas_text()}.
- Do not query system, catalog, or metadata tables.
- Do not use INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, MERGE, EXEC, CALL, COPY, GRANT, REVOKE, DECLARE, BEGIN, COMMIT, or ROLLBACK.
- Do not return placeholders.
- When returning entities, include stable identifiers when they are available.
- When returning descriptive names, include the related stable identifier when it helps avoid merging different records with the same name.
- Do not assume specific column names exist. Use only columns listed in the schema context.
- Do not invent relationships. Use explicit relationships from the optional guidance when provided.
- If the question cannot be answered with the available schema, return exactly: NO_SQL
"""

    response = llm.invoke(prompt)

    sql_query = clean_sql_response(response.content)

    return normalize_generated_sql(sql_query)


def build_sql_generation_prompt(
    question: str,
    schema_context: str,
) -> str:
    """
    Build the prompt used to generate SQL.
    """

    return f"""
You are a careful {AI_DB_DIALECT_NAME} SQL generator.

Your task is to create one SQL SELECT query that answers the user's question.

User question:
{question}

Available schema, columns, and optional guidance:
{schema_context}

Allowed schema:
{ALLOWED_SCHEMA}

Allowed tables:
{get_allowed_tables_text()}

Excluded schemas:
{get_excluded_schemas_text()}

Rules:
- Return only SQL.
- Do not use markdown.
- Do not explain the query.
- Only use SELECT.
- Use {AI_DB_DIALECT_NAME} syntax.
- Always use schema-qualified table names, for example {ALLOWED_SCHEMA}.table_name.
- Only query tables in the allowed schema: {ALLOWED_SCHEMA}.
- Do not query excluded schemas.
- Do not query system, catalog, or metadata tables.
- Do not use INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, MERGE, EXEC, CALL, COPY, GRANT, REVOKE, DECLARE, BEGIN, COMMIT, or ROLLBACK.
- Do not return placeholders.
- Use clear column aliases.
- For top, highest, bottom, or lowest questions, use ORDER BY and the correct row-limiting syntax for {AI_DB_DIALECT_NAME}.
- For count, total, sum, average, per, by, highest, lowest, top, or bottom questions, generate a query that returns the actual result.
- When returning entities, include stable identifiers when they are available.
- When returning descriptive names, include the related stable identifier when it helps avoid merging different records with the same name.
- Do not assume specific column names exist. Use only columns listed in the schema context.
- Do not invent relationships. Use explicit relationships from the optional guidance when provided.
- If the question cannot be answered with the available schema, return exactly: NO_SQL
"""


def normalize_generated_sql(sql_query: str) -> str:
    """
    Normalize the generated SQL text.
    """

    cleaned = sql_query.strip()

    if cleaned.upper() == "NO_SQL":
        return "NO_SQL"

    # Some local models return text before or after the query.
    # Keep only the SELECT query if possible.
    lower_cleaned = cleaned.lower()

    select_position = lower_cleaned.find("select")

    if select_position > 0:
        cleaned = cleaned[select_position:].strip()

    # Remove one final semicolon because the safety layer does not allow
    # multiple statements.
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()

    return cleaned


# ============================================================
# SQL execution
# ============================================================

def execute_sql(sql_query: str) -> pd.DataFrame:
    """
    Execute validated SQL and return a DataFrame.
    """

    if not is_safe_select_query(sql_query):
        raise ValueError("SQL query did not pass safety validation.")

    engine = get_engine()

    logger.info("Executing SQL:\n%s", sql_query)

    try:
        with engine.connect() as conn:
            return pd.read_sql(
                text(sql_query),
                conn,
            )

    except SQLAlchemyError as exc:
        raise RuntimeError(f"Database execution error: {exc}") from exc


# ============================================================
# Result summarization
# ============================================================

def summarize_result(
    question: str,
    sql_query: str,
    result_df: pd.DataFrame,
) -> str:
    """
    Ask the LLM to summarize the actual SQL result.
    """

    if result_df.empty:
        return "The query returned no rows."

    llm = get_llm()

    result_text = dataframe_to_text(result_df)

    prompt = f"""
You are a business-friendly data analyst.

Answer the user's question using only the SQL result provided below.

User question:
{question}

Database dialect:
{AI_DB_DIALECT_NAME}

SQL executed:
{sql_query}

SQL result:
{result_text}

Rules:
- Do not mention SQL unless it helps clarify the answer.
- Do not invent data.
- Do not use placeholders.
- Do not say what the query would return.
- Use only the values shown in the SQL result.
- Keep the answer concise and easy to read.
"""

    response = llm.invoke(prompt)

    return response.content.strip()


def dataframe_to_text(
    result_df: pd.DataFrame,
    max_rows: int = 20,
) -> str:
    """
    Convert a DataFrame to plain text for the LLM.
    """

    if result_df.empty:
        return "No rows returned."

    display_df = result_df.head(max_rows).copy()

    for column in display_df.columns:
        display_df[column] = display_df[column].map(format_value)

    result_text = display_df.to_string(index=False)

    if len(result_df) > max_rows:
        result_text += (
            f"\n\nOnly the first {max_rows} rows are shown. "
            f"Total rows returned: {len(result_df)}."
        )

    return result_text


def format_value(value: Any) -> str:
    """
    Format values for readable LLM input.
    """

    if pd.isna(value):
        return ""

    return str(value)


# ============================================================
# Final answer validation
# ============================================================

def answer_looks_invalid(answer: str) -> bool:
    """
    Detect answers that look like model failures.

    Keep this generic.
    Do not block domain-specific phrases such as patient, customer,
    account, invoice, balance, order, or payment.
    """

    normalized_answer = answer.lower().strip()

    invalid_patterns = [
        "```sql",
        "select ",
        " from ",
        " where ",
        "placeholder",
        "this query",
        "the query would",
        "would return",
        "you can use",
        "i don't have access",
        "i cannot access",
    ]

    return any(
        pattern in normalized_answer
        for pattern in invalid_patterns
    )


def build_fallback_answer(
    result_df: pd.DataFrame,
) -> str:
    """
    Return a deterministic answer if the LLM summary looks invalid.
    """

    if result_df.empty:
        return "The query returned no rows."

    result_text = dataframe_to_text(result_df)

    return (
        "I ran the query successfully, but the model summary looked unreliable. "
        "Here is the SQL result:\n\n"
        f"{result_text}"
    )