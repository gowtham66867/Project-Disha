"""Database engine/session — SQLite (zero-infra) or PostgreSQL (production)."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    pass


def _make_engine():
    url = settings.database_url
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        if url == "sqlite://":
            return create_engine(url, connect_args=connect_args, poolclass=StaticPool, echo=False)
        return create_engine(url, connect_args=connect_args, echo=False)
    return create_engine(url, pool_pre_ping=True, echo=False)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    from . import models  # noqa: F401
    from .db_guards import install_audit_immutability_guard

    Base.metadata.create_all(bind=engine)
    install_audit_immutability_guard(engine)


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
