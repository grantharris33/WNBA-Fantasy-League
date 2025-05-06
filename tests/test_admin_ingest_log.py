from __future__ import annotations

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_ingest_log_admin(monkeypatch, tmp_path: Path):
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DB_FILENAME", str(db_file))
    monkeypatch.setenv("RAPIDAPI_KEY", "dummy-key")

    from importlib import reload

    import app.main as main

    reload(main)

    # Insert fake log entries
    from app.core.database import SessionLocal
    from app.models import IngestLog

    session = SessionLocal()
    for i in range(150):
        session.add(IngestLog(provider="rapidapi", message=f"err {i}"))
    session.commit()

    transport = ASGITransport(main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First page default size 100
        resp = await client.get("/admin/ingest-log")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 150
        assert len(data["items"]) == 100

        # Second page
        resp2 = await client.get("/admin/ingest-log?page=2")
        data2 = resp2.json()
        assert len(data2["items"]) == 50

        # Clear
        del_resp = await client.delete("/admin/ingest-log")
        assert del_resp.status_code == 200
        assert del_resp.json()["deleted"] == 150

        resp3 = await client.get("/admin/ingest-log")
        assert resp3.json()["total"] == 0

    session.close()
