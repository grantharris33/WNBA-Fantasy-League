from pathlib import Path
import pytest

# We purposely defer importing app modules until after we tweak env vars

@pytest.mark.asyncio
async def test_seed_script(tmp_path: Path, monkeypatch):
    # Isolate DB to temporary file
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DB_FILENAME", str(db_file))

    # Import seed script (this will import DB after env var set) and run
    from scripts import seed_demo  # local import after env var set

    seed_demo.main()

    # Import db and models after seed script completed
    from app.core import database as db
    from app import models

    session = db.SessionLocal()

    users = session.query(models.User).all()
    assert len(users) == 4

    league = session.query(models.League).first()
    assert league is not None
    assert league.name == "Demo League"
    assert league.commissioner == users[0]

    teams = session.query(models.Team).all()
    assert len(teams) == 4

    session.close()