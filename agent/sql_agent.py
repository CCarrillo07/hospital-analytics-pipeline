"""
LangChain SQL Agent for natural language questions over PostgreSQL.
"""

from functools import lru_cache
import logging

from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_core.tools import Tool

from agent.llm import get_llm
from agent.database import get_sql_database
from agent.config import ALLOWED_SCHEMA, ALLOWED_TABLES
from agent.safety import clean_sql_response


logger = logging.getLogger(__name__)


class CleanSQLDatabaseToolkit(SQLDatabaseToolkit):
    """
    Custom SQL toolkit that cleans SQL before execution.

    Some local models return SQL inside markdown fences, for example:

    ```sql
    SELECT ...
    ```

    PostgreSQL cannot execute those backticks.
    This toolkit removes that formatting before running the SQL.
    """

    def get_tools(self):
        """
        Return SQL tools, replacing sql_db_query with a safer cleaned version.
        """

        tools = super().get_tools()
        cleaned_tools = []

        for tool in tools:
            if tool.name == "sql_db_query":
                cleaned_tools.append(
                    Tool(
                        name="sql_db_query",
                        description=(
                            "Input to this tool is a detailed and correct SQL query. "
                            "This tool executes the SQL query against the database and returns the result. "
                            "The input must be plain SQL only. Markdown code fences are automatically removed."
                        ),
                        func=self._run_clean_query,
                    )
                )

            elif tool.name == "sql_db_query_checker":
                cleaned_tools.append(
                    Tool(
                        name="sql_db_query_checker",
                        description=tool.description,
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
    def _run_clean_query_checker(original_tool):
        """
        Clean SQL before sending it to the query checker.
        """

        def _checker(query: str) -> str:
            cleaned_query = clean_sql_response(query)
            return original_tool.run(cleaned_query)

        return _checker


@lru_cache(maxsize=1)
def get_agent_executor():
    """
    Create the LangChain SQL agent executor.

    The agent can inspect table schemas, generate SQL, run SELECT queries,
    and return a natural language answer.
    """

    llm = get_llm()
    db = get_sql_database()

    toolkit = CleanSQLDatabaseToolkit(
        db=db,
        llm=llm
    )

    prefix = f"""
You are a data analytics assistant for a hospital analytics database.

You answer business questions by using SQL tools over this PostgreSQL schema:

{ALLOWED_SCHEMA}

Available tables:

{", ".join(ALLOWED_TABLES)}

General rules:
- Only use SELECT queries.
- Always use full table names with the schema prefix, for example {ALLOWED_SCHEMA}.appointments.
- Only query tables inside the {ALLOWED_SCHEMA} schema.
- Do not query raw tables.
- Do not query automation tables.
- Do not insert, update, delete, drop, truncate, alter, create, grant, revoke, call, or copy anything.
- Never modify the database.
- Be concise and business-friendly in the final answer.

Schema and sample row rules:
- The sample rows shown by sql_db_schema are only examples.
- Use sample rows only to understand column names and table structure.
- Never calculate totals, counts, averages, rankings, or final business answers from sample rows.
- Do not answer the user's question using only the sample rows.
- If a question requires a count, total, average, sum, ranking, grouping, comparison, top N, or bottom N, you must execute a SQL query.

Join rules:
- If the question requires data from more than one table, inspect the schema of all relevant tables before writing the SQL query.
- Never guess join keys.
- Never guess column names such as id, name, cost, treatment_name, patient_name, doctor_name, or appointment_name.
- Use only column names that appear in sql_db_schema.
- If a SQL query requires a JOIN, first call sql_db_schema for all tables involved in the JOIN.
- If you are unsure about a column name, call sql_db_schema before writing SQL.

Known table relationships:
- harmonized.appointments.patient_id joins to harmonized.patients.patient_id.
- harmonized.appointments.doctor_id joins to harmonized.doctors.doctor_id.
- harmonized.treatments.appointment_id joins to harmonized.appointments.appointment_id.
- harmonized.billing.patient_id joins to harmonized.patients.patient_id.
- harmonized.billing.treatment_id joins to harmonized.treatments.treatment_id.

Known important columns:
- Treatment type is stored in harmonized.treatments.treatment_type.
- Treatment cost or billing amount is stored in harmonized.billing.amount.
- Insurance provider is stored in harmonized.patients.insurance_provider.
- Doctor specialization is stored in harmonized.doctors.specialization.
- Appointment status is stored in harmonized.appointments.status.
- Payment status is stored in harmonized.billing.payment_status.
- Hospital branch is stored in harmonized.doctors.hospital_branch.

Treatment cost query rules:
- For treatment cost questions, use harmonized.treatments and harmonized.billing.
- Join them using treatment_id.
- Use harmonized.treatments.treatment_type for the treatment category.
- Use harmonized.billing.amount for the cost.
- Do not use treatment_name.
- Do not use cost.
- Do not use t.id.
- Do not use b.cost.

SQL execution rules:
- Use sql_db_query to execute SQL and get real database results.
- Do not use sql_db_query_checker for simple SELECT, COUNT, SUM, AVG, GROUP BY, ORDER BY, or LIMIT queries.
- Use sql_db_query_checker only if the query is complex or if a previous query failed.
- If you use sql_db_query_checker, you must still execute the query afterward using sql_db_query.
- Never give a Final Answer after only using sql_db_query_checker.
- If you know the SQL query needed, execute it immediately using sql_db_query.
- Do not explain the SQL before running it.
- For aggregation questions, use GROUP BY when needed.
- Use clear aliases for calculated columns.
- Use ORDER BY when ranking results.
- Use LIMIT when the user asks for top or bottom results.
- Return the actual database result, not only the SQL query.
- If a query fails, do not assume or invent the result.
- If a query fails because of formatting, retry with plain SQL only.

Agent formatting rules:
- Do not return a Final Answer until after you have executed the SQL query and seen the Observation.
- Never return Final Answer and Action in the same response.
- Do not wrap SQL in markdown code fences.
- Action Input must be plain SQL text only.
- A checked SQL query is not a database result.
- The final answer must be based on the Observation returned by sql_db_query.
- If a SQL query fails, read the error, inspect the relevant schema, fix the query, and run it again.

Final answer rules:
- Answer using only the SQL result.
- Do not invent data.
- Mention the key numbers clearly.
- Keep the answer short and easy to understand.
"""

    return create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        verbose=True,
        top_k=20,
        prefix=prefix,
        max_iterations=10,
        agent_executor_kwargs={
            "handle_parsing_errors": True
        }
    )


def ask_database(question: str) -> str:
    """
    Ask the SQL agent a natural language question.
    """

    logger.info("User question: %s", question)

    agent_executor = get_agent_executor()

    response = agent_executor.invoke(
        {
            "input": question
        }
    )

    answer = response.get("output", str(response))

    logger.info("Agent answer: %s", answer)

    return answer