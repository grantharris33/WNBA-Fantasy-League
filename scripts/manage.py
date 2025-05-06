#!/usr/bin/env python3
"""Lightweight management CLI for development / ops tasks.

Currently supports only the subset needed for Story 4:

* ``backfill <YYYY>`` – iterate over every ISO week in the given season and
  recompute ``team_score`` totals via the scoring engine.

Example::

    poetry run python scripts/manage.py backfill 2024
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

# Ensure project root on path when running script directly
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.append(str(_PROJECT_ROOT))

from app.services.scoring import (  # noqa: E402  pylint: disable=wrong-import-position
    update_weekly_team_scores,
)


def backfill_season(season: int):
    """Recompute weekly ``team_score`` rows for a whole *season* (calendar year).

    The command loops for ISO weeks of the given **season** (ISO year)
    and invokes ``update_weekly_team_scores`` for the Monday of each valid week.
    Existing rows will be overwritten, so the operation is idempotent.
    """
    weeks_run: list[int] = []

    # Determine the number of ISO weeks in the target ISO year `season`
    # The ISO week number of Dec 28th will be 52 or 53.
    last_week_check_date = dt.date(season, 12, 28)
    _, num_iso_weeks_in_season, _ = last_week_check_date.isocalendar()

    for week_num in range(1, num_iso_weeks_in_season + 1):
        try:
            # Get the date for Monday of week_num in the specified ISO year `season`
            monday_of_iso_week = dt.datetime.strptime(f'{season}-{week_num}-1', "%G-%V-%u").date()
        except ValueError:
            # This should ideally not happen if num_iso_weeks_in_season is correct
            # and strptime is working as expected for valid ISO weeks.
            print(
                f"Warning: strptime failed for supposedly valid ISO week {season}-{week_num}. Skipping."
            )  # Add a print for diagnostics
            continue

        update_weekly_team_scores(monday_of_iso_week)
        weeks_run.append(week_num)

    if weeks_run:
        print(
            f"Backfill complete – processed {len(weeks_run)} ISO weeks ({weeks_run[0]}–{weeks_run[-1]}) for ISO season {season}."
        )
    else:
        print(f"Backfill complete – no ISO weeks processed for ISO season {season}.")


def main():
    parser = argparse.ArgumentParser(description="Management CLI for development / ops tasks.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Backfill command
    backfill_parser = subparsers.add_parser("backfill", help="Recompute weekly team_score rows for a whole season.")
    backfill_parser.add_argument("season", type=int, help="The calendar year of the season to backfill (e.g., 2024).")

    args = parser.parse_args()

    if args.command == "backfill":
        backfill_season(args.season)
    elif args.command is None:
        parser.print_help()


if __name__ == "__main__":
    main()  # pragma: no cover
