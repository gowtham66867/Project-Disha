"""DB-level append-only triggers for the prospect interaction audit log.

ORM-level guards only stop writes going through SQLAlchemy unit-of-work.
These triggers reject raw SQL UPDATE/DELETE at the database itself — so
the guarantee holds against psql sessions, other services, and direct
session.execute(text(...)) calls.  Both dialects are handled; idempotent.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

_TABLE = "prospect_interaction_log"

_SQLITE_DDL = [
    f"""CREATE TRIGGER IF NOT EXISTS trg_{_TABLE}_no_update
    BEFORE UPDATE ON {_TABLE}
    BEGIN
        SELECT RAISE(ABORT, '{_TABLE} is append-only: UPDATE not permitted');
    END;""",
    f"""CREATE TRIGGER IF NOT EXISTS trg_{_TABLE}_no_delete
    BEFORE DELETE ON {_TABLE}
    BEGIN
        SELECT RAISE(ABORT, '{_TABLE} is append-only: DELETE not permitted');
    END;""",
]

_POSTGRES_DDL = [
    f"""CREATE OR REPLACE FUNCTION reject_{_TABLE}_mutation() RETURNS trigger AS $$
    BEGIN
        RAISE EXCEPTION '{_TABLE} is append-only: % not permitted', TG_OP;
    END;
    $$ LANGUAGE plpgsql;""",
    f"DROP TRIGGER IF EXISTS trg_{_TABLE}_no_update ON {_TABLE};",
    f"""CREATE TRIGGER trg_{_TABLE}_no_update
    BEFORE UPDATE ON {_TABLE}
    FOR EACH ROW EXECUTE FUNCTION reject_{_TABLE}_mutation();""",
    f"DROP TRIGGER IF EXISTS trg_{_TABLE}_no_delete ON {_TABLE};",
    f"""CREATE TRIGGER trg_{_TABLE}_no_delete
    BEFORE DELETE ON {_TABLE}
    FOR EACH ROW EXECUTE FUNCTION reject_{_TABLE}_mutation();""",
]


def install_audit_immutability_guard(engine: Engine) -> None:
    stmts = _POSTGRES_DDL if engine.dialect.name == "postgresql" else _SQLITE_DDL
    with engine.begin() as conn:
        for stmt in stmts:
            conn.execute(text(stmt))
