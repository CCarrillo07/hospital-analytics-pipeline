"""
Configuration for the DB AI Assistant.

This file keeps the assistant reusable across different database domains,
such as hospital, retail, banking, logistics, education, or finance.

The values are loaded from the .env file located at the project root.
"""

from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# ============================================================
# Helper functions
# ============================================================

def parse_csv_env(value: str | None, default: list[str] | None = None) -> list[str]:
    """
    Parse a comma-separated environment variable into a list.

    Example:
        "customers,orders,products"
        becomes
        ["customers", "orders", "products"]
    """

    if default is None:
        default = []

    if value is None:
        return default

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


# ============================================================
# Ollama configuration
# ============================================================

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:14b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


# ============================================================
# AI database configuration
# ============================================================

AI_DB_DIALECT = os.getenv(
    "AI_DB_DIALECT",
    "postgresql+psycopg2",
)

AI_DB_DIALECT_NAME = os.getenv(
    "AI_DB_DIALECT_NAME",
    "PostgreSQL",
)

AI_DB_HOST = os.getenv("AI_DB_HOST", "localhost")
AI_DB_PORT = os.getenv("AI_DB_PORT", "5432")
AI_DB_NAME = os.getenv("AI_DB_NAME")
AI_DB_USER = os.getenv("AI_DB_USER")
AI_DB_PASSWORD = os.getenv("AI_DB_PASSWORD")


# ============================================================
# AI query scope
# ============================================================

ALLOWED_SCHEMA = os.getenv("AI_DB_SCHEMA", "public").strip()

# Leave AI_DB_ALLOWED_TABLES blank to allow all tables in ALLOWED_SCHEMA.
AI_DB_ALLOWED_TABLES_RAW = os.getenv("AI_DB_ALLOWED_TABLES")
ALLOWED_TABLES = parse_csv_env(AI_DB_ALLOWED_TABLES_RAW, default=[])

# Schemas the assistant should avoid.
AI_DB_EXCLUDED_SCHEMAS_RAW = os.getenv(
    "AI_DB_EXCLUDED_SCHEMAS",
    "raw,analytics,automation,information_schema",
)

EXCLUDED_SCHEMAS = parse_csv_env(
    AI_DB_EXCLUDED_SCHEMAS_RAW,
    default=[
        "raw",
        "analytics",
        "automation",
        "information_schema",
    ],
)


# ============================================================
# Optional AI assistant domain guidance
# ============================================================
# These are optional and should be configured per project/database.
#
# Example:
# AI_DB_RELATIONSHIPS=orders.customer_id = customers.customer_id; order_items.order_id = orders.order_id
# AI_DB_BUSINESS_RULES=When returning entities, include stable identifiers when available.

AI_DB_RELATIONSHIPS = os.getenv("AI_DB_RELATIONSHIPS", "").strip()
AI_DB_BUSINESS_RULES = os.getenv("AI_DB_BUSINESS_RULES", "").strip()