import asyncio
from app.external_apis.rapidapi_client import wnba_client

async def test_standings():
    try:
        standings_data = await wnba_client.fetch_standings('2024')
        print(f'Standings data type: {type(standings_data)}')
        print(f'Standings data keys: {standings_data.keys() if isinstance(standings_data, dict) else "Not a dict"}')
        print(f'Standings data: {standings_data}')
    except Exception as e:
        print(f'Error: {e}')
    finally:
        await wnba_client.close()

if __name__ == "__main__":
    asyncio.run(test_standings())