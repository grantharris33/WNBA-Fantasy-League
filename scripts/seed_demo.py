#!/usr/bin/env python
"""Seed script for local development.

Inserts:
* 4 demo users (demo1..4@example.com)
* A league "Demo League" with commissioner demo1
* One team per user in the league

Run with:
    poetry run python scripts/seed_demo.py
"""
from __future__ import annotations

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app import models
from app.core.database import SessionLocal, init_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def main() -> None:
    init_db()
    db: Session = SessionLocal()

    # If data already seeded, skip
    if db.query(models.User).first():
        print("Demo data already exists. Skipping.")
        return

    users = []
    for i in range(1, 5):
        user = models.User(email=f"demo{i}@example.com", hashed_password=get_password_hash("password"))
        db.add(user)
        users.append(user)
    db.flush()  # assign IDs

    league = models.League(name="Demo League", commissioner=users[0])
    db.add(league)
    db.flush()

    teams = []
    for i, user in enumerate(users, start=1):
        team = models.Team(name=f"Team {i}", owner=user, league=league)
        db.add(team)
        teams.append(team)

    db.commit()
    print("Seeded demo data successfully.")


if __name__ == "__main__":
    main()
