"""
Database initialization script.

Applies src/db/schema.sql against the database configured via
DATABASE_URL (loaded from .env locally, or a real environment
variable/secret in CI/production). Safe to re-run: every statement in
schema.sql uses IF NOT EXISTS, so re-applying it against an
already-initialized database is a no-op, not an error.

This exists as a cross-platform alternative to running `psql` directly
(useful on Windows or anywhere psql isn't installed), and reuses the
same get_connection()/load_env() path the rest of the application uses,
so there is exactly one way DATABASE_URL gets resolved -- not a second,
separate one specific to setup.

Usage (from the project root):
    python -m src.db.init_db
    # or
    python src/db/init_db.py
"""
from __future__ import annotations

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.db.connection import get_connection  # noqa: E402

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


def init_db() -> None:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.commit()
        print(f"Schema applied successfully from {SCHEMA_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
