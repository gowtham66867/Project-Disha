"""Append-only audit log — ORM and DB-level immutability tests."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.main import app
from app.db import SessionLocal, init_db
from app.models.interaction_log import ProspectInteractionLog, InteractionImmutableError


@pytest.fixture(scope="module", autouse=True)
def _init(tmp_path_factory):
    """Boot the app once so tables + triggers exist before raw-session tests."""
    with TestClient(app):
        pass


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _seed_log():
    session = SessionLocal()
    row = ProspectInteractionLog(
        prospect_id="PR001", rm_id="RM01",
        event_type="score_computed", event_detail="test",
        lead_score_snapshot=72.0, score_version="test",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return session, row


def test_orm_rejects_update():
    session, row = _seed_log()
    try:
        row.event_detail = "TAMPERED"
        with pytest.raises(InteractionImmutableError):
            session.commit()
        session.rollback()
    finally:
        session.close()


def test_orm_rejects_delete():
    session, row = _seed_log()
    try:
        session.delete(row)
        with pytest.raises(InteractionImmutableError):
            session.commit()
        session.rollback()
    finally:
        session.close()


def test_db_trigger_rejects_raw_sql_update():
    """DB trigger must fire even when bypassing the ORM entirely."""
    session, row = _seed_log()
    try:
        with pytest.raises(DBAPIError):
            session.execute(
                text("UPDATE prospect_interaction_log SET event_detail = 'TAMPERED' WHERE log_id = :id"),
                {"id": row.log_id},
            )
            session.commit()
        session.rollback()
    finally:
        session.close()


def test_db_trigger_rejects_raw_sql_delete():
    session, row = _seed_log()
    try:
        with pytest.raises(DBAPIError):
            session.execute(
                text("DELETE FROM prospect_interaction_log WHERE log_id = :id"),
                {"id": row.log_id},
            )
            session.commit()
        session.rollback()
    finally:
        session.close()


def test_api_pipeline_stats(client):
    resp = client.get("/api/v1/pipeline/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] > 0
    assert "by_band" in body


def test_api_prospects_list(client):
    resp = client.get("/api/v1/prospects/")
    assert resp.status_code == 200
    assert len(resp.json()) > 0


def test_api_score_detail(client):
    resp = client.get("/api/v1/score/PR001")
    assert resp.status_code == 200
    body = resp.json()
    assert "contributions" in body
    assert len(body["contributions"]) > 0
