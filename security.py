import re
import sqlparse
from sqlparse.tokens import DDL, DML

BLOCKED_WORDS = {
    "insert", "update", "delete", "create", "alter", "drop",
    "truncate", "merge", "exec", "execute", "grant", "revoke",
    "backup", "restore", "use", "declare", "set",
    "openrowset", "opendatasource", "openquery"
}

BLOCKED_PATTERNS = (
    r"--",                 # line comment
    r"/\*",                # block comment start
    r"\*/",                # block comment end
    r"\bsp_[a-z0-9_]*\b",  # SQL Server stored procedures
    r"\bxp_[a-z0-9_]*\b",  # SQL Server extended procedures
    r"\bfn_[a-z0-9_]*\b",  # SQL Server function naming pattern
    r"\b[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*\s*\(",  # schema.function(...)
    r"\b[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*\s*\(",  # db.schema.function(...)
)

def validate_readonly_sql(sql: str) -> None:
    cleaned = sql.strip()

    if ";" in cleaned:
        raise ValueError("Ponto e vírgula não é permitido.")

    statements = sqlparse.parse(cleaned)

    if len(statements) != 1:
        raise ValueError("Apenas um statement é permitido.")

    first_token = next(
        (t for t in statements[0].tokens if not t.is_whitespace),
        None
    )

    if not first_token:
        raise ValueError("SQL vazio.")

    first = first_token.value.lower()

    if first not in {"select", "with"}:
        raise ValueError("Apenas SELECT ou CTE com WITH são permitidos.")

    normalized = re.sub(r"\s+", " ", cleaned.lower())

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, normalized):
            raise ValueError("Padrão SQL bloqueado para modo somente leitura.")

    for word in BLOCKED_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", normalized):
            raise ValueError(f"Termo bloqueado: {word}")

    # SQL Server: SELECT ... INTO cria tabela e altera estado.
    if re.search(r"\bselect\b[\s\S]*\binto\b", normalized):
        raise ValueError("SELECT INTO não é permitido em modo somente leitura.")

    for token in statements[0].flatten():
        value = token.value.lower()

        if token.ttype in (DDL,):
            raise ValueError("DDL não é permitido.")

        if token.ttype == DML and value not in {"select"}:
            raise ValueError(f"DML bloqueado: {value}")
