"""
Shared database URL builder.

This helper builds SQLAlchemy-compatible database URLs for:

- PostgreSQL
- Oracle
- SQL Server
"""

from sqlalchemy.engine import URL


def build_database_url(
    dialect: str,
    user: str,
    password: str,
    host: str,
    port: str,
    database: str,
    db_type: str = "postgresql",
    driver: str | None = None,
    encrypt: str | None = None,
    trust_server_certificate: str | None = None,
) -> str:
    """
    Build a SQLAlchemy database URL.

    Examples:
        PostgreSQL:
            postgresql+psycopg2://user:password@localhost:5432/database

        Oracle:
            oracle+oracledb://user:password@localhost:1521/?service_name=XEPDB1

        SQL Server:
            mssql+pyodbc://user:password@localhost:1433/database?driver=ODBC+Driver+18+for+SQL+Server
    """

    normalized_db_type = db_type.strip().lower()

    query_params = {}

    if normalized_db_type in {"oracle", "oracledb"}:
        query_params["service_name"] = database

        database_url = URL.create(
            drivername=dialect,
            username=user,
            password=password,
            host=host,
            port=int(port),
            query=query_params,
        )

        return database_url.render_as_string(
            hide_password=False
        )

    if normalized_db_type in {"sqlserver", "mssql"}:
        if driver:
            query_params["driver"] = driver

        if encrypt:
            query_params["Encrypt"] = encrypt

        if trust_server_certificate:
            query_params["TrustServerCertificate"] = trust_server_certificate

    database_url = URL.create(
        drivername=dialect,
        username=user,
        password=password,
        host=host,
        port=int(port),
        database=database,
        query=query_params,
    )

    return database_url.render_as_string(
        hide_password=False
    )