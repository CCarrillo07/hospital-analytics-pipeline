"""
Configuration for the Hospital DB AI Assistant.

This project is currently PostgreSQL-specific.

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

def parse_csv_env(value: str | None, default: list[str]) -> list[str]:
    """
    Parse a comma-separated environment variable into a list.

    Example:
        "patients,doctors,billing"
        becomes
        ["patients", "doctors", "billing"]
    """

    if not value:
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
# AI PostgreSQL database configuration
# ============================================================

AI_DB_DIALECT = os.getenv(
    "AI_DB_DIALECT",
    "postgresql+psycopg2"
)

AI_DB_DIALECT_NAME = os.getenv(
    "AI_DB_DIALECT_NAME",
    "PostgreSQL"
)

AI_DB_HOST = os.getenv("AI_DB_HOST", "localhost")
AI_DB_PORT = os.getenv("AI_DB_PORT", "5432")
AI_DB_NAME = os.getenv("AI_DB_NAME")
AI_DB_USER = os.getenv("AI_DB_USER")
AI_DB_PASSWORD = os.getenv("AI_DB_PASSWORD")


# ============================================================
# AI query scope
# ============================================================

ALLOWED_SCHEMA = os.getenv("AI_DB_SCHEMA", "harmonized")

AI_DB_ALLOWED_TABLES_RAW = os.getenv("AI_DB_ALLOWED_TABLES")

ALLOWED_TABLES = parse_csv_env(
    AI_DB_ALLOWED_TABLES_RAW,
    [
        "patients",
        "doctors",
        "appointments",
        "treatments",
        "billing",
    ]
) if AI_DB_ALLOWED_TABLES_RAW is None else parse_csv_env(
    AI_DB_ALLOWED_TABLES_RAW,
    []
)