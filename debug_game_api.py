import asyncio
from app.external_apis.rapidapi_client import wnba_client

async def debug_game():
    try:
        # Get a specific game's box score
        box = await wnba_client.fetch_box_score("401620232")

        print("Box score structure:")
        print(f"Keys: {box.keys()}")

        teams = box.get("teams", [])
        print(f"\nTeams count: {len(teams)}")

        for i, team in enumerate(teams):
            print(f"\nTeam {i}:")
            print(f"  Keys: {team.keys()}")
            print(f"  Team data: {team}")

        players = box.get("players", [])
        print(f"\nPlayers blocks count: {len(players)}")

        if players:
            print(f"First player block keys: {players[0].keys()}")

        print(f"\nGame ID: {box.get('id')}")

    except Exception as e:
        print(f'Error: {e}')
    finally:
        await wnba_client.close()

if __name__ == "__main__":
    asyncio.run(debug_game())