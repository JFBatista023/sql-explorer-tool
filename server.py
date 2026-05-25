from mcp.server.fastmcp import FastMCP

from db import run_query, list_tables, describe_table
from security import validate_readonly_sql

mcp = FastMCP("sql-explorer-readonly")


@mcp.tool()
def query(connection: str, sql: str, limit: int = 100) -> dict:
    """
    Executa uma consulta SQL somente leitura.
    Permitido: SELECT e CTE com WITH.
    Bloqueado: INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, etc.
    """
    if limit > 500:
        limit = 500

    validate_readonly_sql(sql)

    return run_query(connection, sql, limit)


@mcp.tool()
def tables(connection: str) -> list:
    """
    Lista tabelas disponíveis na conexão.
    """
    return list_tables(connection)


@mcp.tool()
def describe(connection: str, table: str, schema: str | None = None) -> dict:
    """
    Descreve colunas, PK, FKs e índices de uma tabela.
    """
    return describe_table(connection, table, schema)


if __name__ == "__main__":
    mcp.run()