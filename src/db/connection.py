"""
Database connection helper.

Centralizes database connectivity for the entire application.

This module now provides:

1. A psycopg2 connection (used by ingestion)
2. A SQLAlchemy engine (used by pandas / dashboard)

Environment variables are loaded from .env locally through load_env().
"""

from __future__ import annotations

import os

import psycopg2
from psycopg2.extensions import connection as PGConnection
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from src.config import load_env


class MissingDatabaseUrlError(RuntimeError):
    """Raised when DATABASE_URL is missing."""


def _get_database_url() -> str:
    """
    Load .env (if present) and return DATABASE_URL.
    """

    load_env()

    dsn = os.environ.get("DATABASE_URL")

    if not dsn:
        raise MissingDatabaseUrlError(
            "DATABASE_URL is not set.\n\n"
            "Copy .env.example to .env or configure the environment variable."
        )

    return dsn


def get_connection() -> PGConnection:
    """
    Return a psycopg2 connection.

    Used primarily by the ingestion pipeline.
    """

    return psycopg2.connect(_get_database_url())


def get_engine() -> Engine:
    """
    Return a SQLAlchemy engine.

    Used by pandas.read_sql() to avoid DBAPI warnings.
    """

    return create_engine(_get_database_url())

