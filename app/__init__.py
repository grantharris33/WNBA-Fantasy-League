"""
App package initialization.
"""

# Import models so they register mappings
from app import models  # noqa: F401
from app.core.database import init_db  # noqa: F401

# Automatically create tables in dev environment
init_db()
