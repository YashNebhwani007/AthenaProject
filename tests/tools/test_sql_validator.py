"""Tests for SQL validator: valid analytical queries and adversarial attack cases."""

import pytest

from athena.tools.sql_validator import validate_sql


@pytest.mark.parametrize(
    "query",
    [
        "SELECT * FROM customers",
        "SELECT customer_id, avg(monthly_fee) FROM customers GROUP BY customer_id",
        "SELECT * FROM customers WHERE churn = 1 ORDER BY tenure DESC LIMIT 50",
        (
            "WITH cte AS (SELECT customer_id, monthly_fee FROM customers WHERE churn = 1) "
            "SELECT count(*) FROM cte"
        ),
        "SELECT id, total FROM orders WHERE total > (SELECT avg(total) FROM orders)",
        "SELECT 1 AS x UNION ALL SELECT 2 AS x",
        "SELECT id, rank() OVER (PARTITION BY region ORDER BY revenue DESC) as rnk FROM sales",
    ],
)
def test_valid_sql_queries(query: str):
    """Verify standard and advanced analytical SELECT queries pass validation."""
    result = validate_sql(query)
    assert result.is_valid is True
    assert result.error is None
    assert result.sanitized_sql is not None


def test_sql_limit_detection():
    """Verify limit detection and extraction."""
    res_with_limit = validate_sql("SELECT * FROM tbl LIMIT 42")
    assert res_with_limit.is_valid is True
    assert res_with_limit.has_limit is True
    assert res_with_limit.limit_value == 42

    res_without_limit = validate_sql("SELECT * FROM tbl")
    assert res_without_limit.is_valid is True
    assert res_without_limit.has_limit is False
    assert res_without_limit.limit_value is None


@pytest.mark.parametrize(
    ("attack_sql", "expected_err_snippet"),
    [
        ("", "Empty SQL query"),
        ("   ", "Empty SQL query"),
        ("SELECT * FROM", "SQL syntax error"),
        ("SELECT 1; DROP TABLE customers;", "Multiple SQL statements"),
        ("SELECT 1; SELECT 2;", "Multiple SQL statements"),
        ("DROP TABLE customers", "Disallowed statement type"),
        ("DELETE FROM customers WHERE id = 1", "Disallowed statement type"),
        ("INSERT INTO customers VALUES (1, 'John')", "Disallowed statement type"),
        ("UPDATE customers SET churn = 0", "Disallowed statement type"),
        ("ALTER TABLE customers DROP COLUMN churn", "Disallowed statement type"),
        ("CREATE TABLE hacked AS SELECT 1", "Disallowed statement type"),
        ("COPY customers TO 'leak.csv'", "Disallowed statement type"),
        ("SET enable_external_access = true", "Disallowed statement type"),
        ("PRAGMA version", "Disallowed statement type"),
        ("ATTACH 'remote.db' AS remote", "Disallowed statement type"),
        ("DETACH remote", "Disallowed statement type"),
    ],
)
def test_attack_and_invalid_sql_cases(attack_sql: str, expected_err_snippet: str):
    """Verify blacklisted, destructive, or invalid SQL statements are rejected."""
    result = validate_sql(attack_sql)
    assert result.is_valid is False
    assert result.error is not None
    assert expected_err_snippet.lower() in result.error.lower()
