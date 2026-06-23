"""
PostgreSQL database URL builder.
"""

from sqlalchemy.engine import URL


def build_database_url(
    dialect: str,
    user: str,
    password: str,
    host: str,
    port: str,
    database: str,
) -> str:
    """
    Build a PostgreSQL SQLAlchemy database URL.

    Example:
        postgresql+psycopg2://user:password@localhost:5432/database
    """

    database_url = URL.create(
        drivername=dialect,
        username=user,
        password=password,
        host=host,
        port=int(port),
        database=database,
    )

    return database_url.render_as_string(
        hide_password=False
    )