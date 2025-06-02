import asyncio
from app.external_apis.rapidapi_client import wnba_client

async def test_teams():
    try:
        teams_data = await wnba_client.fetch_all_teams()
        print(f'Teams data type: {type(teams_data)}')
        print(f'Teams data keys: {teams_data.keys() if isinstance(teams_data, dict) else "Not a dict"}')
        print(f'Teams data: {teams_data}')
    except Exception as e:
        print(f'Error: {e}')
    finally:
        await wnba_client.close()

if __name__ == "__main__":
    asyncio.run(test_teams())