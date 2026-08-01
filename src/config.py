"""
Centralizes environment configuration loading.

Local development reads variables from a `.env` file via python-dotenv.
GitHub Actions (and any other CI/deployment environment) sets real
environment variables directly via repository secrets -- this module
does not override those. `load_dotenv(override=False)` only fills in
variables that aren't already set, and does nothing at all if no `.env`
file is present, so this is safe to import unconditionally in every
entry point (local scripts, tests, CI) without branching on environment.

This is deliberately a separate module from db/connection.py: loading
environment configuration and producing a database connection are two
different responsibilities, and conflating them would make connection.py
harder to reason about and test in isolation.
"""
from __future__ import annotations

from dotenv import load_dotenv

_loaded = False


def load_env() -> None:
    """Load variables from a .env file into the environment, if present.

    Idempotent (safe to call more than once) and safe in CI (a no-op if
    no .env file exists, and never overwrites an already-set variable
    such as a GitHub Actions secret).
    """
    global _loaded
    if _loaded:
        return
    load_dotenv(override=False)
    _loaded = True
