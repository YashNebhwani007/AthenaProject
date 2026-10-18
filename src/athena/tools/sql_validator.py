"""AST-based SQL validator ensuring only safe read-only queries are executed."""

import sqlglot
from pydantic import BaseModel
from sqlglot import exp
from sqlglot.errors import ParseError

BLACKLIST_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "COPY",
    "EXPORT",
    "IMPORT",
    "ATTACH",
    "DETACH",
    "INSTALL",
    "LOAD",
    "CALL",
    "PRAGMA",
    "SET",
}

FORBIDDEN_NODE_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.Create,
    exp.Copy,
    exp.Command,
    exp.Set,
    exp.Pragma,
    exp.Kill,
)


class ValidationResult(BaseModel):
    """Validation outcome for an analytical SQL statement."""

    is_valid: bool
    error: str | None = None
    sanitized_sql: str | None = None
    has_limit: bool = False
    limit_value: int | None = None


def validate_sql(sql: str) -> ValidationResult:
    """Validate that SQL is a single, read-only SELECT statement with no forbidden operations."""
    cleaned = sql.strip()
    if not cleaned:
        return ValidationResult(is_valid=False, error="Empty SQL query")

    try:
        statements = sqlglot.parse(cleaned, dialect="duckdb")
    except ParseError as exc:
        return ValidationResult(is_valid=False, error=f"SQL syntax error: {exc}")

    # Remove any trailing None/empty expressions
    statements = [s for s in statements if s is not None]

    if not statements:
        return ValidationResult(is_valid=False, error="No valid SQL statements found")

    if len(statements) > 1:
        return ValidationResult(
            is_valid=False,
            error="Multiple SQL statements are not permitted; provide a single SELECT statement",
        )

    stmt = statements[0]

    # Whitelist root statement: only Select or Union
    if not isinstance(stmt, (exp.Select, exp.Union)):
        op_name = type(stmt).__name__
        return ValidationResult(
            is_valid=False,
            error=f"Disallowed statement type '{op_name}'. Only SELECT queries are permitted",
        )

    # Walk full AST to block forbidden operations inside CTEs, subqueries, or expressions
    for node in stmt.walk():
        if isinstance(node, FORBIDDEN_NODE_TYPES):
            node_name = type(node).__name__
            return ValidationResult(
                is_valid=False,
                error=f"Forbidden SQL operation detected: {node_name}",
            )

        # Keyword checks in command or raw literal nodes
        node_sql = node.sql_name().upper() if hasattr(node, "sql_name") else ""
        if node_sql in BLACKLIST_KEYWORDS:
            return ValidationResult(
                is_valid=False,
                error=f"Forbidden keyword '{node_sql}' detected in SQL AST",
            )

    # Check for LIMIT
    limit_node = stmt.find(exp.Limit)
    has_limit = limit_node is not None
    limit_val = None
    if has_limit and limit_node is not None:
        try:
            limit_val = int(limit_node.expression.name)  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            limit_val = None

    return ValidationResult(
        is_valid=True,
        sanitized_sql=stmt.sql(dialect="duckdb"),
        has_limit=has_limit,
        limit_value=limit_val,
    )
