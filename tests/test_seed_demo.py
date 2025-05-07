import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# We purposely defer importing app modules until after we tweak env vars


@pytest.mark.asyncio
async def test_seed_script(tmp_path: Path, monkeypatch):
    # Isolate DB to temporary file
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DB_FILENAME", str(db_file))
    monkeypatch.setenv("TESTING", "true")

    # Mock sys.argv to avoid argparse errors with pytest arguments
    with patch.object(sys, 'argv', ['seed_demo.py']):
        # Import seed script (this will import DB after env var set) and run
        from scripts import seed_demo  # local import after env var set

        # Mock argparse.ArgumentParser to avoid argument parsing issues
        with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
            # Configure the mock to return an args object with force=False
            mock_args = type('args', (), {'force': False})
            mock_parse_args.return_value = mock_args

            # Run the seed script
            seed_demo.main()

            # Import db and models after seed script completed
            from app import models
            from app.core import database as db

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
