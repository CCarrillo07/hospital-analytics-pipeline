"""
Configuration for the Hospital DB AI Agent.
"""

from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# ============================================================
# Ollama configuration
# ============================================================

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral-nemo")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


# ============================================================
# AI database configuration
# ============================================================

AI_DB_HOST = os.getenv("AI_DB_HOST", "localhost")
AI_DB_PORT = os.getenv("AI_DB_PORT", "5432")
AI_DB_NAME = os.getenv("AI_DB_NAME")
AI_DB_USER = os.getenv("AI_DB_USER")
AI_DB_PASSWORD = os.getenv("AI_DB_PASSWORD")


ALLOWED_SCHEMA = "harmonized"

ALLOWED_TABLES = [
    "patients",
    "doctors",
    "appointments",
    "treatments",
    "billing",
]