"""
Hospital DB AI Agent Streamlit app.

This app allows users to ask natural language questions about the
harmonized hospital data using a local Ollama model.
"""

import logging

import streamlit as st

from agent.sql_agent import ask_database
from agent.charting import generate_chart_sql, run_chart_sql, create_chart


# ============================================================
# Logging configuration
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# Streamlit configuration
# ============================================================

st.set_page_config(
    page_title="Hospital DB AI Agent",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# UI
# ============================================================

st.title("Hospital DB AI Agent")
st.caption("Ask natural language questions about the harmonized hospital data.")

with st.form("question_form"):
    question = st.text_input(
        "Ask a question",
        placeholder="Example: How many appointments are there by status?"
    )

    create_chart_option = st.checkbox(
        "Create chart if possible",
        value=True
    )

    submitted = st.form_submit_button("Ask")


if submitted:
    if not question.strip():
        st.warning("Please enter a question.")

    else:
        try:
            # --------------------------------------------
            # 1. Ask SQL agent
            # --------------------------------------------

            with st.spinner("Asking the database..."):
                answer = ask_database(question)

            st.subheader("Answer")
            st.write(answer)

            # --------------------------------------------
            # 2. Generate chart if requested
            # --------------------------------------------

            if create_chart_option:
                st.subheader("Chart")

                with st.spinner("Generating chart..."):
                    chart_sql = generate_chart_sql(question)

                st.caption("SQL used for the chart:")
                st.code(chart_sql, language="sql")

                try:
                    chart_df = run_chart_sql(chart_sql)

                    st.dataframe(
                        chart_df,
                        width="stretch"
                    )

                    fig = create_chart(chart_df)

                    if fig is not None:
                        st.plotly_chart(
                            fig,
                            width="stretch"
                        )
                    else:
                        st.info("The result is not suitable for an automatic chart.")

                except Exception as chart_error:
                    logger.exception("Chart generation failed.")
                    st.warning(f"Could not generate chart: {chart_error}")

        except Exception as e:
            logger.exception("DB AI Agent failed.")
            st.error(f"An error occurred: {e}")