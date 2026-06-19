"""
Shared database URL builder.

This helper builds SQLAlchemy-compatible database URLs for different
database engines.
"""

from sqlalchemy.engine import URL


def build_database_url(
    dialect: str,
    user: str,
    password: str,
    host: str,
    port: str,
    database: str,
    driver: str | None = None,
    encrypt: str | None = None,
    trust_server_certificate: str | None = None,
) -> str:
    """
    Build a SQLAlchemy database URL.

    Supported examples:
    - postgresql+psycopg2
    - oracle+oracledb
    - mssql+pyodbc

    Important:
    SQLAlchemy hides passwords when converting a URL to string by default.
    We must use render_as_string(hide_password=False) so create_engine()
    receives the real password.
    """

    query_params = {}

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