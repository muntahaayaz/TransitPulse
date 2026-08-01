"""
Database connection helper.

Centralizes how the rest of the application obtains a PostgreSQL
connection, so connection details (env var name, driver choice) only
need to change in one place if they ever do.

Configuration: reads DATABASE_URL from the environment. No credentials
are hardcoded here or anywhere else in this project -- see .env.example
for the expected format and README.md for setup instructions.

Bug fix (M0): this module previously read os.environ directly without
ever loading .env, so DATABASE_URL was always missing locally unless it
happened to already be set as a real system environment variable --
despite the README instructing users to create a .env file. Fixed by
calling config.load_env() before reading the variable. See config.py
for why environment loading lives in its own module rather than here.
"""
from __future__ import annotations

import os
import psycopg2
from psycopg2.extensions import connection as PGConnection

from src.config import load_env


class MissingDatabaseUrlError(RuntimeError):
    """Raised when DATABASE_URL is not set in the environment."""


def get_connection() -> PGConnection:
    """Return a new psycopg2 connection built from the DATABASE_URL env var."""
    load_env()  # loads .env locally if present; no-op in CI, never overrides real secrets
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise MissingDatabaseUrlError(
            "DATABASE_URL is not set. Copy .env.example to .env (or set the "
            "environment variable / GitHub Actions secret directly) before running."
        )
    return psycopg2.connect(dsn)
