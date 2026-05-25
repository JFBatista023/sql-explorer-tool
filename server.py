import hashlib
import logging
import time
import uuid

from mcp.server.fastmcp import FastMCP

from db import run_query, list_tables, describe_table
from logging_utils import actor_context, log_event, setup_logger
from security import validate_readonly_sql

mcp = FastMCP("sql-explorer-readonly")
logger = setup_logger()


def _sql_fingerprint(sql: str) -> str:
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()[:16]


@mcp.tool()
def query(connection: str, sql: str, limit: int = 100) -> dict:
    """
    Executa uma consulta SQL somente leitura.
    Permitido: SELECT e CTE com WITH.
    Bloqueado: INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, etc.
    """
    request_id = str(uuid.uuid4())
    started = time.perf_counter()
    ctx = actor_context()
    sql_clean = sql.strip()
    sql_preview = " ".join(sql_clean.split())[:120]
    sql_fingerprint = _sql_fingerprint(sql_clean)

    log_event(
        logger,
        logging.INFO,
        "MCP query call started",
        request_id=request_id,
        tool="query",
        connection=connection,
        limit_requested=limit,
        sql_length=len(sql_clean),
        sql_preview=sql_preview,
        sql_fingerprint=sql_fingerprint,
        **ctx,
    )

    if limit > 500:
        log_event(
            logger,
            logging.WARNING,
            "Limit above max; clamped to 500",
            request_id=request_id,
            tool="query",
            connection=connection,
            limit_requested=limit,
            limit_effective=500,
            **ctx,
        )
        limit = 500

    try:
        validate_readonly_sql(sql)
        result = run_query(connection, sql, limit)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        log_event(
            logger,
            logging.INFO,
            "MCP query call finished",
            request_id=request_id,
            tool="query",
            connection=connection,
            rows_returned=len(result.get("rows", [])),
            columns_returned=len(result.get("columns", [])),
            duration_ms=elapsed_ms,
            **ctx,
        )
        return result
    except ValueError as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        log_event(
            logger,
            logging.WARNING,
            "MCP query rejected",
            request_id=request_id,
            tool="query",
            connection=connection,
            duration_ms=elapsed_ms,
            error=str(exc),
            **ctx,
        )
        raise
    except Exception:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        log_event(
            logger,
            logging.ERROR,
            "MCP query failed",
            request_id=request_id,
            tool="query",
            connection=connection,
            duration_ms=elapsed_ms,
            **ctx,
        )
        logger.exception("Unhandled error on query", extra={"extra_fields": {"request_id": request_id, "tool": "query"}})
        raise


@mcp.tool()
def tables(connection: str) -> list:
    """
    Lista tabelas disponíveis na conexão.
    """
    request_id = str(uuid.uuid4())
    started = time.perf_counter()
    ctx = actor_context()
    log_event(
        logger,
        logging.INFO,
        "MCP tables call started",
        request_id=request_id,
        tool="tables",
        connection=connection,
        **ctx,
    )
    try:
        result = list_tables(connection)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        log_event(
            logger,
            logging.INFO,
            "MCP tables call finished",
            request_id=request_id,
            tool="tables",
            connection=connection,
            table_count=len(result),
            duration_ms=elapsed_ms,
            **ctx,
        )
        return result
    except Exception:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        log_event(
            logger,
            logging.ERROR,
            "MCP tables call failed",
            request_id=request_id,
            tool="tables",
            connection=connection,
            duration_ms=elapsed_ms,
            **ctx,
        )
        logger.exception("Unhandled error on tables", extra={"extra_fields": {"request_id": request_id, "tool": "tables"}})
        raise


@mcp.tool()
def describe(connection: str, table: str, schema: str | None = None) -> dict:
    """
    Descreve colunas, PK, FKs e índices de uma tabela.
    """
    request_id = str(uuid.uuid4())
    started = time.perf_counter()
    ctx = actor_context()
    log_event(
        logger,
        logging.INFO,
        "MCP describe call started",
        request_id=request_id,
        tool="describe",
        connection=connection,
        table=table,
        schema=schema,
        **ctx,
    )
    try:
        result = describe_table(connection, table, schema)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        log_event(
            logger,
            logging.INFO,
            "MCP describe call finished",
            request_id=request_id,
            tool="describe",
            connection=connection,
            table=table,
            schema=schema,
            columns_count=len(result.get("columns", [])),
            duration_ms=elapsed_ms,
            **ctx,
        )
        return result
    except Exception:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        log_event(
            logger,
            logging.ERROR,
            "MCP describe call failed",
            request_id=request_id,
            tool="describe",
            connection=connection,
            table=table,
            schema=schema,
            duration_ms=elapsed_ms,
            **ctx,
        )
        logger.exception("Unhandled error on describe", extra={"extra_fields": {"request_id": request_id, "tool": "describe"}})
        raise


@mcp.tool()
def health() -> dict:
    """
    Verifica se o MCP está ativo.
    """
    ctx = actor_context()
    log_event(
        logger,
        logging.INFO,
        "MCP health call",
        tool="health",
        **ctx,
    )
    return {"status": "ok", "service": "sql-explorer-readonly"}


if __name__ == "__main__":
    log_event(
        logger,
        logging.INFO,
        "MCP sql-explorer-readonly iniciado",
        service="sql-explorer-readonly",
        **actor_context(),
    )
    mcp.run()
