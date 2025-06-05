#!/usr/bin/env python3

import asyncio

from app.external_apis.rapidapi_client import wnba_client


async def test_roster():
    try:
        # Test with a specific team ID - let's use Atlanta Dream (teamId: 20)
        print("Testing team roster API call...")
        roster_data = await wnba_client.fetch_team_roster("20")

        print(f"Roster data type: {type(roster_data)}")

        if roster_data:
            print(f"Roster data keys: {roster_data.keys() if isinstance(roster_data, dict) else 'Not a dict'}")

            if isinstance(roster_data, dict):
                # Check for team info
                team_info = roster_data.get("team", {})
                print(f"Team info keys: {team_info.keys() if isinstance(team_info, dict) else 'No team key'}")

                if isinstance(team_info, dict):
                    athletes = team_info.get("athletes", [])
                    print(f"Athletes found: {len(athletes) if isinstance(athletes, list) else 'Not a list'}")

                    if athletes and len(athletes) > 0:
                        print(f"First athlete: {athletes[0]}")
                    else:
                        print("No athletes in roster")
                        print(f"Team info structure: {team_info}")

            print(f"Raw roster data: {roster_data}")
        else:
            print("No roster data received")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await wnba_client.close()


if __name__ == "__main__":
    asyncio.run(test_roster())
