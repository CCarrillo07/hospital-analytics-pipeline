"""
Run PostgreSQL transformation stored procedures.

This file calls the stored procedures that transform data from the raw schema
into the harmonized schema.
"""

import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from db_connection import get_engine


# ============================================================
# Logging configuration
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# Database connection
# ============================================================

engine = get_engine()


# ============================================================
# Transformation logic
# ============================================================

def run_transformations() -> None:
    """
    Run all transformation stored procedures.

    This function calls the master stored procedure:

        automation.sp_transform_all()

    The master procedure is responsible for refreshing all harmonized tables.
    """

    logger.info("Starting transformation process...")

    query = text("CALL automation.sp_transform_all();")

    with engine.begin() as conn:
        conn.execute(query)

    logger.info("Transformation process completed successfully.")


# ============================================================
# Script entry point
# ============================================================

if __name__ == "__main__":
    try:
        run_transformations()

    except SQLAlchemyError:
        logger.exception("Database error occurred while running transformations.")

    except Exception:
        logger.exception("Unexpected error occurred while running transformations.")