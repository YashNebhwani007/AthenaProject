# DuckDB Secure Connection Creation and Pragma Sandboxing

## Overview
Athena exposes DuckDB SQL querying to AI agents and external client queries. To safeguard host
infrastructure and prevent filesystem traversal, unauthorized external network access, or privilege
escalation, DuckDB connections are initialized with hardened security pragmas.

## Security Configuration

When initializing connection pools in `src/athena/data/registry.py`:

```python
import duckdb

def create_secure_connection(read_only: bool = True) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(":memory:", read_only=read_only)
    
    # 1. Disable external filesystem access outside designated sandbox
    conn.execute("SET enable_external_access = false;")
    
    # 2. Lock configuration to prevent re-enabling external access
    conn.execute("SET lock_configuration = true;")
    
    # 3. Limit threads and memory to avoid resource starvation
    conn.execute("SET threads = 4;")
    conn.execute("SET max_memory = '2GB';")
    
    return conn
```

## Security Guarantees
- Blocks `read_csv()` from pulling arbitrary host files (e.g. `/etc/passwd`).
- Blocks DuckDB HTTP/S3 remote extensions (`httpfs`, `aws`).
- Enforces strict memory caps to prevent Out-Of-Memory (OOM) host crashes.
