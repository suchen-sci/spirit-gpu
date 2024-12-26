import aiohttp
from spirit_gpu import start, logger


base_url = "http://localhost:8000/v1"


async def check_start():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url) as response:
                if response.status == 200:
                    return True
                else:
                    body = await response.text()
                    logger.info(f"failed to connect to {base_url}, status code: {response.status}, body: {body}")
                    return False
    except Exception as e:
        logger.info(f"failed to connect to {base_url}, err: {e}")
        return False


start({
    "mode": "proxy",
    "base_url": "http://localhost:8000/v1",
    "check_start": check_start,
})
