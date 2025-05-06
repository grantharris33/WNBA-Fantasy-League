from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_jobs_route(monkeypatch, tmp_path: Path):
    """Ensure nightly job is registered and exposed via /jobs route."""
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DB_FILENAME", str(db_file))
    monkeypatch.setenv("RAPIDAPI_KEY", "dummy-key")

    # Import app after env vars set
    from importlib import reload

    import app.main as main

    reload(main)  # ensure startup executed with monkeypatched env

    transport = ASGITransport(main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/jobs")
        assert resp.status_code == 200
        jobs = resp.json()
        assert any(job["id"] == "nightly_ingest" for job in jobs)


# ---------------------------------------------------------------------------
# Mocking helpers
# ---------------------------------------------------------------------------


class _StubClient:
    """Minimal awaitable client API for ingest helpers."""

    def __init__(self, responses: list[dict[str, Any]]):
        self._responses = responses
        self.calls = 0

    async def get(self, url: str, params: dict[str, Any] | None = None):
        class _Resp:
            def __init__(self, data: dict[str, Any]):
                self._data = data
                self.status_code = 200

            def raise_for_status(self):
                pass

            def json(self):
                return self._data

        response = self._responses[self.calls]
        self.calls += 1
        return _Resp(response)


@pytest.mark.asyncio
async def test_fetch_helpers_retry(monkeypatch):
    """fetch_schedule retries until success (simulate failure then success)."""

    from app.jobs import ingest as ing

    class DummyResp:
        def __init__(self, ok: bool):
            self._ok = ok

        def raise_for_status(self):
            if not self._ok:
                raise ing.httpx.HTTPError("oops")

        def json(self):
            return {"20250101": []}

    class DummyClient:
        def __init__(self):
            self.calls = 0

        async def get(self, url, params=None):  # noqa: D401
            self.calls += 1
            if self.calls < 3:
                return DummyResp(False)
            return DummyResp(True)

    client = DummyClient()

    result = await ing._get_json(client, "http://test")
    assert isinstance(result, dict)
    # ensure exactly 3 attempts made
    assert client.calls == 3


@pytest.mark.asyncio
async def test_ingest_idempotent(monkeypatch, tmp_path: Path):
    """Running ingest twice for same date should not create duplicates."""
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DB_FILENAME", str(db_file))
    monkeypatch.setenv("RAPIDAPI_KEY", "dummy-key")
    monkeypatch.setenv("TESTING", "true")

    import app.core.database as db

    db.init_db()

    from app.jobs import ingest as ing

    # Prepare stub schedule (one game) and box-score payload
    schedule_payload = [{"id": "game1"}]

    box_payload = {
        "players": [
            {
                "statistics": [
                    {
                        "athletes": [
                            {
                                "athlete": {"id": "1", "displayName": "Player One", "position": {"abbreviation": "G"}},
                                "stats": [
                                    "20",  # MIN
                                    "2-7",  # FG
                                    "1-1",  # 3PT
                                    "2-2",  # FT
                                    "0",  # OREB
                                    "1",  # DREB
                                    "1",  # REB
                                    "1",  # AST
                                    "1",  # STL
                                    "0",  # BLK
                                    "0",  # TO
                                    "4",  # PF
                                    "-10",  # +/-
                                    "7",  # PTS
                                ],
                            }
                        ]
                    }
                ]
            }
        ]
    }

    async def _mock_fetch_schedule(client, date_iso):  # noqa: D401
        return schedule_payload

    async def _mock_fetch_box(client, gid):  # noqa: D401
        return box_payload

    monkeypatch.setattr(ing, "fetch_schedule", _mock_fetch_schedule)
    monkeypatch.setattr(ing, "fetch_box_score", _mock_fetch_box)

    target_date = dt.date(2025, 1, 1)

    # Run twice
    await ing.ingest_stat_lines(target_date)
    await ing.ingest_stat_lines(target_date)

    from app import models as m

    session = db.SessionLocal()
    count = session.query(m.StatLine).count()
    assert count == 1
    session.close()


@pytest.mark.asyncio
async def test_update_weekly_team_scores(monkeypatch, tmp_path: Path):
    # Isolate DB
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DB_FILENAME", str(db_file))
    monkeypatch.setenv("TESTING", "true")

    from app.core import database as db


def test_backfill_cli(monkeypatch, tmp_path: Path):
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DB_FILENAME", str(db_file))
    monkeypatch.setenv("TESTING", "true")

    # Ensure DB has tables
