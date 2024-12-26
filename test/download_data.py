
import asyncio
import aiohttp


base_url = "http://localhost:8000/v1"


async def check_start():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url) as response:
                text = await response.text()
                print(f"response.status: {response.status}, text: {text}")
                return True

    except Exception as e:
        print(f"failed to connect to {base_url}, err: {e}")
        return False


async def do_check():
    while True:
        res = await check_start()
        if res:
            break
        await asyncio.sleep(1)

asyncio.run(do_check())
