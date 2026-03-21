import asyncio
import httpx
from app.config import settings

async def test():
    print(f"Key: {settings.locationiq_api_key}")
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                settings.locationiq_url, 
                params={'key': settings.locationiq_api_key, 'q': 'madrid', 'format': 'json'}
            )
            print(f"Status: {r.status_code}")
            print(f"Response: {r.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
