"""Chinook database setup and safe query helpers."""
from __future__ import annotations

import logging
import re
from pathlib import Path
from urllib.request import urlopen

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from config import settings

log = logging.getLogger(__name__)
_engine: Engine | None = None


def normalize_phone(value: str | None) -> str:
    """Remove formatting while retaining a leading international plus."""
    value = value or ""
    digits = re.sub(r"\D", "", value)
    return ("+" if value.strip().startswith("+") else "") + digits


def create_database(sql_script: str) -> Engine:
    """Create an in-memory SQLite database from the canonical Chinook script."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    connection = engine.raw_connection()
    try:
        connection.driver_connection.executescript(sql_script)
        connection.commit()
    finally:
        connection.close()
    return engine


def initialize_database(sql_script: str | None = None) -> Engine:
    """Initialize once, downloading the source script when none is supplied."""
    global _engine
    if _engine is not None and sql_script is None:
        return _engine
    if sql_script is None:
        cache = Path.home() / ".cache" / "customer_support_assistant" / "Chinook_Sqlite.sql"
        cache.parent.mkdir(parents=True, exist_ok=True)
        if not cache.exists():
            log.info("Downloading Chinook database script")
            with urlopen(settings.database_url, timeout=30) as response:
                cache.write_bytes(response.read())
        sql_script = cache.read_text(encoding="utf-8")
    _engine = create_database(sql_script)
    log.info("Chinook database initialized")
    return _engine


def get_engine() -> Engine:
    if _engine is None:
        return initialize_database()
    return _engine


def query(sql: str, params: dict | None = None, engine: Engine | None = None) -> list[dict]:
    """Execute a SQLAlchemy text query with bound parameters."""
    log.debug("Executing database query")
    with (engine or get_engine()).connect() as conn:
        return [dict(row._mapping) for row in conn.execute(text(sql), params or {}).fetchall()]


def health_check(engine: Engine | None = None) -> bool:
    try:
        return query("SELECT 1 AS ok", engine=engine)[0]["ok"] == 1
    except Exception:
        log.exception("Database health check failed")
        return False

