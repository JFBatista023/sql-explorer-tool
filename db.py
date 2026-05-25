import logging

import yaml
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from logging_utils import log_event, setup_logger

with open("config.yaml", "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

ENGINES = {}
MAX_LIMIT = 500
LOCK_TIMEOUT_MS = 20000
QUERY_TIMEOUT_SECONDS = 30
logger = setup_logger()

def get_engine(connection_name: str):
    if connection_name not in CONFIG["connections"]:
        raise ValueError(f"Conexão não encontrada: {connection_name}")

    if connection_name not in ENGINES:
        url = CONFIG["connections"][connection_name]["url"]
        log_event(
            logger,
            logging.INFO,
            "Creating SQLAlchemy engine",
            connection=connection_name,
        )
        ENGINES[connection_name] = create_engine(
            url,
            pool_pre_ping=True,
            pool_recycle=300,
        )

    return ENGINES[connection_name]


def run_query(connection_name: str, sql: str, limit: int = 100):
    engine = get_engine(connection_name)
    limit = max(1, min(limit, MAX_LIMIT))
    sql_preview = " ".join(sql.strip().split())[:120]

    try:
        with engine.connect() as conn:
            # Prevent waiting indefinitely on locks in SQL Server.
            conn.execute(text(f"SET LOCK_TIMEOUT {LOCK_TIMEOUT_MS}"))

            # Best-effort DBAPI timeout for drivers like pyodbc.
            try:
                raw_conn = conn.connection.driver_connection
                raw_conn.timeout = QUERY_TIMEOUT_SECONDS
            except Exception:
                log_event(
                    logger,
                    logging.WARNING,
                    "Could not set DBAPI query timeout; continuing",
                    connection=connection_name,
                    timeout_seconds=QUERY_TIMEOUT_SECONDS,
                )

            log_event(
                logger,
                logging.INFO,
                "Executing query on database",
                connection=connection_name,
                limit=limit,
                sql_preview=sql_preview,
            )
            result = conn.execute(text(sql))
            rows = result.fetchmany(limit)

            return {
                "columns": list(result.keys()),
                "rows": [dict(zip(result.keys(), row)) for row in rows],
                "limit": limit,
            }
    except SQLAlchemyError as exc:
        log_event(
            logger,
            logging.ERROR,
            "Database query execution failed",
            connection=connection_name,
            error=str(exc),
        )
        raise ValueError(f"Erro ao executar consulta: {exc}") from exc


def list_tables(connection_name: str):
    engine = get_engine(connection_name)
    inspector = inspect(engine)

    tables = []

    for schema in inspector.get_schema_names():
        for table in inspector.get_table_names(schema=schema):
            tables.append({"schema": schema, "table": table})

    return tables


def describe_table(connection_name: str, table_name: str, schema: str | None = None):
    engine = get_engine(connection_name)
    inspector = inspect(engine)

    return {
        "columns": inspector.get_columns(table_name, schema=schema),
        "pk": inspector.get_pk_constraint(table_name, schema=schema),
        "foreign_keys": inspector.get_foreign_keys(table_name, schema=schema),
        "indexes": inspector.get_indexes(table_name, schema=schema),
    }
